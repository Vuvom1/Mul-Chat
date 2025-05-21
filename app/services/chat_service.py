import datetime
import json
from fastapi import FastAPI, WebSocket, HTTPException
from nats.aio.client import Client as NATS
import os
from dotenv import load_dotenv
import logging
from app.querries.user_group_querries import UserGroupQueries
from app.querries.group_querries import GroupQueries
from app.querries.user_querries import UserQueries
from app.querries.message_querries import MessageQueries
from app.database.db import get_db

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
nats_client = None

async def get_nats_client():
    global nats_client
    if nats_client is None:
        nats_client = NATS()
        await nats_client.connect(os.getenv("NATS_SERVER_URL"))
    return nats_client

async def group_websocket(websocket: WebSocket, user_id: int, group_id: str):
    await websocket.accept()
    clients[user_id] = websocket
    print(clients)

    nats_client = await get_nats_client()  # Get NATS client

    group = group_queries.get_group(group_id)
    if not group:
        logger.error(f"Group {group_id} not found")
        await websocket.close(code=1008, reason="Group not found")
        return

    async def message_handler(msg):
        print(f"Received message on {msg.subject}: {msg.data.decode()}")

        group_users = user_group_queries.get_group_users(group_id)

        # Check if group_users is empty
        if not group_users:
            logger.error(f"No users found in group {group_id}")
            return
        
        data_str = msg.data.decode()
        message_data = json.loads(data_str)
        sender_id = message_data.get("user_id")

        # Send the message to all users in the group
        sent_users = group_users.copy()  # Create a copy of the list to avoid modifying it while iterating
        sent_users.remove(user_queries.get_user(sender_id))  # Remove the sender from the list of users to send to

        for user in sent_users:
            if user.id not in clients:
                logger.info(f"User {user.id} is not connected, skipping.")
                continue
            print(f"Sending message to user {user.id}: {msg.data.decode()}")
            await clients[user.id].send_text(msg.data.decode())

    group = group_queries.get_group(group_id)

    sub_key = f"chat.{group.name}"

    if sub_key not in active_subscriptions:
        sub = await nats_client.subscribe(sub_key, cb=message_handler)
        active_subscriptions[sub_key] = {"subcription": sub, "count": 1}
    else:
        active_subscriptions[sub_key]["count"] += 1

    # await nats_client.subscribe(f"chat.{group.name}", cb=message_handler)

    try:
        while True:
            message = await websocket.receive_text()

            message_data = {
                "username": user_queries.get_user(user_id).username,
                "user_id": user_id,
                "group_id": group_id,
                "message": message,
                "timestamp": datetime.datetime.now().isoformat()
            }
            message_json = json.dumps(message_data)
            await nats_client.publish(f"chat.{group.name}", message_json.encode())
            # await nats_client.publish(f"chat.{group_id}", message)
    except:
        # clients.pop(user_id, None)
        logger.info(f"User {user_id} disconnected from group {group_id}")

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