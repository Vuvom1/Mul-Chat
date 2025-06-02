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
) 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

active_clients: Dict[str, ChatClient] = {}
clients = set()

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, current_user = Depends(get_current_user_ws)):
    await user_rooms_websocket(websocket, current_user)