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

async def create_user(username: str, email: str, password: str):
    try:
        # Check if user already exists
        existing_user = user_queries.get_user_by_username(username)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        # Create new user
        new_user = user_queries.create_user(username=username, email=email, hashed_password=password)
        return new_user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
async def login_user(username: str, password: str):
    try:
        # Check if user exists
        user = user_queries.get_user_by_username(username=username)
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        hashed_password = user_queries.get_hashed_password(username)

        if password != hashed_password:
            raise HTTPException(status_code=400, detail="Incorrect password")

        return user
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    