from fastapi import Depends, WebSocket
from fastapi import APIRouter
from app.routers.models import CreateGroupRequest, CreateUserRequest, LoginRequest, SendMessageRequest
from app.nats.client import ChatClient
from nats.aio.client import Client as NATS
from typing import Dict
import logging
from app.auth.dependencies import get_current_user
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
    jwt = await create_user_service(user.username, user.password, user.email)
    if jwt == False:
        return {"message": "User creation failed"}
    return {"message": "User created successfully", "jwt": jwt}

@router.post("/login")
async def login_user(user: LoginRequest):
    auth_token = await login_user_service(user.username, user.password)

    return {
       "access_token": auth_token,
       "token_type": "bearer",
    }

@router.get("/me")
async def get_user_info(current_user = Depends(get_current_user)):
    from app.services.user_service import get_user_information
    user_info = await get_user_information(current_user)
    return {"user_info": user_info}

@router.get("/get_users")
async def get_users(acount: str = None):
    from app.nats.ncs import get_users
    nc = await get_users(account=acount)
    users = await get_users(nc)
    return {"users": users}

@router.post("/operators")
async def create_operator(operator_name: str):
    from app.nats.ncs import add_operator
    nc = add_operator(operator_name)
    return {"message": "Operator created successfully", "nc": nc}

@router.get("/operators")
async def get_operators():
    from app.nats.ncs import get_operators
    nc = get_operators()
    operators = await get_operators(nc)
    return {"operators": operators}