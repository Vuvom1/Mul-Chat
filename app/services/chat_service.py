import base64
import datetime
import json
from fastapi import FastAPI, WebSocket, HTTPException
from nats.aio.client import Client as NATS
import os
from dotenv import load_dotenv
import logging

import nkeys
from app.querries.user_group_querries import UserGroupQueries
from app.querries.group_querries import GroupQueries
from app.querries.user_querries import UserQueries
from app.querries.message_querries import MessageQueries
from app.database.db import get_db
from nacl.signing import SigningKey

db = next(get_db())

user_group_queries = UserGroupQueries(db)
group_queries = GroupQueries(db)
user_queries = UserQueries(db)
message_queries = MessageQueries(db)

# Load environment variables from .env file
load_dotenv()
logger = logging.getLogger(__name__)

clients = dict[int, WebSocket]()
active_subscriptions = dict[str, int]()
nats_client = dict[str, NATS]()

async def get_nats_client(user_jwt, user_seed):
    """Connect to NATS server with authentication"""
    nats_client = NATS()
    
    # Get NATS server URL from environment variable
    nats_url = os.getenv("NATS_SERVER_URL")
    if not nats_url:
        logger.error("NATS_SERVER_URL not set in environment variables")
        raise ValueError("NATS server URL not configured")
    
    logger.info(f"Attempting to connect to NATS server at {nats_url}")

    async def jwt_cb():
        # Ensure JWT is properly encoded
        if isinstance(user_jwt, str):
            return user_jwt
        return user_jwt.encode() if hasattr(user_jwt, 'encode') else str(user_jwt)
    
    def signature_callback(nonce):
        kp = nkeys.from_seed(user_seed.encode())
        sig = kp.sign(nonce)

        return base64.b64encode(sig)
    
    try:
        await nats_client.connect(
            nats_url,
            user=os.getenv("NATS_USER", "default_user"),
            password=os.getenv("NATS_PASSWORD", "default_password"),
            user_jwt_cb=jwt_cb,
            signature_cb=signature_callback,
            connect_timeout=15,  # Increase timeout
            verbose=True,
            max_reconnect_attempts=5,
            reconnect_time_wait=2,
            ping_interval=20,  # Keep connection alive
            max_outstanding_pings=5,
            allow_reconnect=True,
            tls_hostname=None  # Set this if you need TLS
        )
        
        logger.info(f"Successfully connected to NATS server at {nats_url}")
        return nats_client
    except TimeoutError:
        logger.error(f"Timeout connecting to NATS server at {nats_url}. Server might be down or unreachable.")
        raise ConnectionError(f"Timeout connecting to NATS server. Please check if the server is running and accessible.")
    except Exception as e:
        logger.error(f"Failed to connect to NATS server: {str(e)}")
        raise ConnectionError(f"Failed to connect to NATS server: {str(e)}")

async def group_websocket(websocket: WebSocket, room: str):
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for room: {room}")

        # Get JWT and NKeys seed from WebSocket headers
        user_jwt = websocket.headers.get("X-User-JWT")
        nkeys_seed = websocket.headers.get("X-NKeys-Seed")

        if not user_jwt or not nkeys_seed:
            logger.error("Missing JWT or NKeys seed in headers")
            await websocket.close(code=1008, reason="Authentication failed: Missing JWT or NKeys seed")
            return

        # Connect to NATS (this might be causing the issue by raising an HTTPException)
        try:
            nc = await get_nats_client(user_jwt=user_jwt, user_seed=nkeys_seed)
        except Exception as e:
            logger.error(f"NATS connection error: {str(e)}")
            # Don't raise HTTPException here, use WebSocket close instead
            await websocket.close(code=1011, reason=f"Failed to connect to NATS: {str(e)}")
            return

        # Define message handler
        async def message_handler(msg):
            try:
                data = msg.data.decode()
                # Forward message to WebSocket client
                await websocket.send_text(data)
                logger.debug(f"Forwarded message from {msg.subject} to WebSocket")
            except Exception as e:
                logger.error(f"Error handling message: {str(e)}")

        # Subscribe to the room channel
        try:
            sub = await nc.subscribe(room, cb=message_handler)
            logger.info(f"Subscribed to room {room}")
        except Exception as e:
            logger.error(f"Failed to subscribe to room {room}: {str(e)}")
            await websocket.close(code=1008, reason=f"Subscription failed: {str(e)}")
            return

        # Handle WebSocket messages
        try:
            while True:
                message = await websocket.receive_text()
                
                message_data = {
                    "room": room,
                    "message": message,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                message_json = json.dumps(message_data)
                await nc.publish(f"{room}", message_json.encode())
                logger.debug(f"Published message to chat.{room}")
                
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            
    finally:
        # Clean up
        logger.info(f"Disconnected from room {room}")
        # Close NATS connection if it exists and is connected
        if 'nc' in locals() and nc.is_connected:
            try:
                await nc.drain()
            except:
                pass

async def send_group_message(message: str, user_id: int, group_id: int):
    try:
        nats = NATS()
        await nats.connect(os.getenv("NATS_SERVER_URL"))
        logger.info("Connected to NATS server")

        group = group_queries.get_group(group_id)
        user = user_queries.get_user(user_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # Check if user is part of the group
        if not user_group_queries.is_user_in_group(user_id, group_id):
            raise HTTPException(status_code=403, detail="User not in group")

        message_data = {
            "username": user.username,
            "user_id": user_id,
            "group_id": group_id,
            "message": message,
            "timestamp": datetime.datetime.now().isoformat()
        }

        # message_json = json.dumps(message_data)

        await nats.publish(f"chat.{group.name}", message_data.encode())

        message_queries.create_message(message, user_id, group_id)
    except Exception as e:
        logger.error(f"Error sending message to NATS: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send message")
    finally:
        await nats.drain()

async def join_group(user_id: int, group_id: int | None, group_name: str | None):
    if group_id is None and group_name is None:
        raise HTTPException(status_code=400, detail="Either group_id or group_name must be provided")
    
    try:
        nats = NATS()
        await nats.connect(os.getenv("NATS_SERVER_URL"))
        logger.info("Connected to NATS server")

        if group_id is None:
            group = group_queries.get_group_by_name(group_name)
            if not group:
                raise HTTPException(status_code=404, detail="Group not found")
        else:
            group = group_queries.get_group(group_id)
            if not group:
                raise HTTPException(status_code=404, detail="Group not found")

        await nats.publish(f"chat.{group.name}", f"User {user_id} joined the group".encode())
        logger.info(f"User {user_id} joined group {group.name}")
        
        user_group_queries.add_user_to_group(user_id, group_id=group.id)
    except Exception as e:
        logger.error(f"Error joining group: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join group")
    finally:
        await nats.drain()

async def create_group(group_name: str):
    try:
        nats = NATS()
        await nats.connect(os.getenv("NATS_SERVER_URL"))
        logger.info("Connected to NATS server")
        
        await nats.publish(f"chat.{group_name}", f"Group {group_name} created".encode())
        group_queries.create_group(group_name)
    except Exception as e:
        logger.error(f"Error creating group: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create group")
    finally:
        await nats.drain()

async def get_user_groups(user_id: int):
    try:
        groups = user_group_queries.get_user_groups(user_id)
        return groups
    except Exception as e:
        logger.error(f"Error getting user groups: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user groups")
    
async def get_chat_history(group_id: str):
    try:
        messages = message_queries.get_group_messages(group_id)
        return messages
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")
    