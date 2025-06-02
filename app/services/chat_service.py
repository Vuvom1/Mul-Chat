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
from app.querries.nats_room_querries import NatsRoomQueries
from app.database.db import get_db
from nacl.signing import SigningKey

db = next(get_db())

user_group_queries = UserGroupQueries(db)
group_queries = GroupQueries(db)
user_queries = UserQueries(db)
message_queries = MessageQueries(db)
nats_room_queries = NatsRoomQueries(db)

# Load environment variables from .env file
load_dotenv()
logger = logging.getLogger(__name__)

clients = dict[int, WebSocket]()
active_subscriptions = dict[str, int]()
nats_client = dict[str, NATS]()

async def get_nats_client():
    """Connect to NATS server with authentication"""
    nats_client = NATS()
    
    # Get NATS server URL from environment variable
    nats_url = os.getenv("NATS_SERVER_URL")
    if not nats_url:
        logger.error("NATS_SERVER_URL not set in environment variables")
        raise ValueError("NATS server URL not configured")
    
    logger.info(f"Attempting to connect to NATS server at {nats_url}")

    # async def jwt_cb():
    #     # Ensure JWT is properly encoded
    #     if isinstance(user_jwt, str):
    #         return user_jwt
    #     return user_jwt.encode() if hasattr(user_jwt, 'encode') else str(user_jwt)
    
    # def signature_callback(nonce):
    #     kp = nkeys.from_seed(user_seed.encode())
    #     sig = kp.sign(nonce)

        # return base64.b64encode(sig)
    
    try:
        await nats_client.connect(
            nats_url,
            user=os.getenv("NATS_USER", "default_user"),
            password=os.getenv("NATS_PASSWORD", "default_password"),
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

async def user_rooms_websocket(websocket: WebSocket, current_user: str):
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for user {current_user}")

        try:
            nc = await get_nats_client()
        except Exception as e:
            logger.error(f"NATS connection error: {str(e)}")
            # Don't raise HTTPException here, use WebSocket close instead
            await websocket.close(code=1011, reason=f"Failed to connect to NATS: {str(e)}")
            return

        # Define message handler
        async def message_handler(msg):
            try:
                data = msg.data.decode()
                logger.debug(f"Received message on subject {msg.subject}: {data}")
                # Forward message to WebSocket client
                await websocket.send_text(data)
                logger.debug(f"Forwarded message from {msg.subject} to WebSocket")
            except Exception as e:
                logger.error(f"Error handling message: {str(e)}")

        # Subscribe to the room channels
        try:
            user_rooms = nats_room_queries.get_room_for_user_by_username(current_user)
            
            # Check if user_rooms is None or empty
            if not user_rooms:
                logger.warning(f"No rooms found for user {current_user}")
                await websocket.send_text(json.dumps({"type": "info", "message": "You don't have any rooms available."}))
                user_rooms = [] 
            
            for room in user_rooms:
                room_topic = f"{room.subject_prefix}.{room.name}" if hasattr(room, 'subject_prefix') and hasattr(room, 'name') else f"room.{room.id}"
                await nc.subscribe(room_topic, cb=message_handler)
                logger.info(f"Subscribed to room {room_topic}")
        except Exception as e:
            logger.error(f"Failed to subscribe to rooms for user {current_user}: {str(e)}")
            await websocket.close(code=1008, reason=f"Subscription failed: {str(e)}")
            return

        # Handle WebSocket messages
        try:
            while True:
                message = await websocket.receive_json()
                room = message.get("room")
                if not room:
                    logger.error("No room specified in message")
                    await websocket.close(code=1008, reason="No room specified")
                    return
                
                if room not in [r.name for r in user_rooms]:
                    logger.error(f"User {current_user} not subscribed to room {room}")
                    await websocket.close(code=1008, reason="Not subscribed to room")
                    return

                message_json = json.dumps(message)
                await nc.publish(f"room.{room}", message_json.encode())
                logger.debug(f"Published message to room.{room}")

        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            
    finally:
        # Clean up
        logger.info(f"Disconnected from rooms for user {current_user}")
        # Close NATS connection if it exists and is connected
        if 'nc' in locals() and nc.is_connected:
            try:
                await nc.drain()
            except:
                pass