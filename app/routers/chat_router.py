import os
from fastapi import Depends, FastAPI, WebSocket, HTTPException
from fastapi import APIRouter
from app.auth.dependencies import get_current_user, get_current_user_ws
from app.nats.client import ChatClient
from nats.aio.client import Client as NATS
from typing import Dict
import logging
from app.services.chat_service import (
    user_rooms_websocket, 
    get_room_message_history as get_room_message_history_service
) 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, current_user = Depends(get_current_user_ws)):
    await user_rooms_websocket(websocket, current_user)

@router.get("/history")
async def get_history(room_name: str, current_user = Depends(get_current_user)):
    messages_history = await get_room_message_history_service(room_name)

    if not messages_history:
        raise HTTPException(status_code=404, detail="No history found for this room")

    return {"history": messages_history}