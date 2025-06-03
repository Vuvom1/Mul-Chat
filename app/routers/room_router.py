from fastapi import Depends, HTTPException, WebSocket
from fastapi import APIRouter
from app.routers.models import CreateRoomRequest
from app.nats.client import ChatClient
from nats.aio.client import Client as NATS
from typing import Dict
import logging
from app.auth.dependencies import get_current_user
from app.services.room_service import (
   create_room_and_add_admin_user as create_room_and_add_admin_user_service,
   get_users_in_room as get_users_in_room_service,  
    join_room as join_room_service,
    leave_room as leave_room_service, 
    setup_stream_for_rooms as setup_stream_for_rooms_service
)
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create_room")
async def create_room(room: CreateRoomRequest, current_user: str = Depends(get_current_user)):
    try:
        created_room = await create_room_and_add_admin_user_service(
            name=room.name,
            subject_prefix="room",
            description=room.description or "",
            admin_username=current_user, 
            is_public=room.is_public or False
        )
        return {"message": f"Room '{created_room['name']}' created successfully."}
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.post("/join_room")
async def join_room(room_name: str, current_user: str = Depends(get_current_user)):
    try:
        room = await join_room_service(current_user, room_name)
        return {
            "message": f"User '{current_user}' joined room '{room['name']}' successfully.",
            "history": room.get("history", []),
                }
    except Exception as e:
        logger.error(f"Error joining room {room_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.get("/get_users_in_room/{room_id}")
async def get_users_in_room(room_id: str, current_user: str = Depends(get_current_user)):
    try:
        users = await get_users_in_room_service(room_id)
        return {"users": users}
    except Exception as e:
        logger.error(f"Error fetching users in room {room_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.delete("/leave_room/{room_id}")
async def leave_room(room_id: str, current_user: str = Depends(get_current_user)):
    try:
        response = await leave_room_service(current_user, room_id)
        return response
    except HTTPException as e:
        logger.error(f"Error leaving room {room_id}: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error leaving room {room_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.get("/setup")
async def setup_stream_for_rooms():
    try:
        await setup_stream_for_rooms_service()

        return {"message": "Stream setup for rooms is successful."}
    except Exception as e:
        logger.error(f"Error setting up stream for rooms: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
