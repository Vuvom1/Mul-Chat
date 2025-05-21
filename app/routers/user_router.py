from fastapi import WebSocket
from fastapi import APIRouter
from app.routers.models import CreateGroupRequest, CreateUserRequest, LoginRequest, SendMessageRequest
from app.nats.client import ChatClient
from nats.aio.client import Client as NATS
from typing import Dict
import logging
from app.services.user_service import (
    create_user as create_user_service,
    login_user as login_user_service
)
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create_user")
async def create_user(user: CreateUserRequest):
    await create_user_service(user.username, user.email, user.password)
    return {"message": "User created successfully"}

@router.post("/login")
async def login_user(user: LoginRequest):
    logined_user = await login_user_service(user.username, user.password)
    return {"message": "User logged in successfully", "user_id": logined_user.id}





    