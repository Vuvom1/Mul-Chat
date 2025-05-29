import os
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter
from app.routers.models import CreateGroupRequest, JoinGroupRequest, SendMessageRequest
from app.nats.client import ChatClient
from nats.aio.client import Client as NATS
from typing import Dict
import logging
from app.services.chat_service import (
    group_websocket, 
    send_group_message as send_group_message_service, 
    create_group as create_group_service,
    join_group as join_group_service,
    get_user_groups as get_user_groups_service,
    get_chat_history as get_group_messages_service
) 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

active_clients: Dict[str, ChatClient] = {}
clients = set()

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, room: str):
    await group_websocket(websocket, room)

@router.post("/send-group-message")
async def send_group_message(message: SendMessageRequest):
    await send_group_message_service(message.message, message.user_id, message.group_id)
    return {"message": f"Message sent to group '{message.group_id}'."}

@router.post("/create-group")
async def create_group(group: CreateGroupRequest):
    await create_group_service(group.group_name)
    return {"message": f"Group '{group.group_name}' created successfully."}

@router.post("/join-group")
async def join_group(group: JoinGroupRequest):
    await join_group_service(group.user_id, group.group_id, group.group_name)
    return {"message": f"User {group.user_id} joined group '{group.group_name}'."}


@router.get("/get-user-groups/{user_id}")
async def get_user_groups(user_id: int):
    try:
        # Fetch user groups from the database
        user_groups = await get_user_groups_service(user_id)
        return {"user_groups": user_groups}
    except Exception as e:
        logger.error(f"Error fetching user groups: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.get("/get-group-messages/{group_id}")
async def get_group_messages(group_id: str):
    try:
        group_messages = await get_group_messages_service(group_id)
        return {"group_messages": group_messages}
    except Exception as e:
        logger.error(f"Error fetching group messages: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")