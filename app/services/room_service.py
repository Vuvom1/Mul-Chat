from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

from fastapi import HTTPException

from app.database.db import get_db
from app.querries.nats_room_querries import NatsRoomQueries
from app.querries.user_querries import UserQueries

db = next(get_db())
nats_room_queries = NatsRoomQueries(db)
user_queries = UserQueries(db)

async def create_room_and_add_admin_user(
    name: str,
    subject_prefix: Optional[str] = None,
    account_id: Optional[str] = 1,
    description: str = "",
    admin_username: Optional[str] = None,
    is_public: bool = False
) -> Dict[str, Any]:
    created_room = nats_room_queries.create_room(
        name=name,
        subject_prefix=subject_prefix,
        account_id=account_id,
        description=description,
        is_public=is_public
    )

    if created_room:
        # If admin_username is provided, add the user as an admin to the room
        admin_user = user_queries.get_user_by_username(admin_username) if admin_username else None
        # Add the user as an admin to the room
        nats_room_queries.add_user_to_room(
            user_id=admin_user.id if admin_user else None,
            room_id=created_room.id 
        )

    return {
        "id": created_room.id,
        "name": created_room.name,
        "subject_prefix": created_room.subject_prefix,
        "account_id": created_room.account_id,
        "description": created_room.description,
        "is_public": created_room.is_public,
        "created_at": created_room.created_at.isoformat() if hasattr(created_room, 'created_at') and created_room.created_at else None
    }

async def join_room(
    current_user: str,
    room_name: str
) -> Dict[str, Any]:
    room = nats_room_queries.get_room_by_name(room_name)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found for name: " + room_name)
        
    # Add the user to the room
    user = user_queries.get_user_by_username(current_user)
    if not user:
        raise ValueError("User not found")

    nats_room_queries.add_user_to_room(user_id=user.id, room_id=room.id)

    return {
        "id": room.id,
        "name": room.name,
        "subject_prefix": room.subject_prefix,
        "account_id": room.account_id,
        "description": room.description,
        "is_public": room.is_public,
        "created_at": room.created_at.isoformat() if hasattr(room, 'created_at') and room.created_at else None
    }

async def get_users_in_room(
    room_id: str,
) -> List[Dict[str, Any]]:
    users = await nats_room_queries.get_users_in_room(room_id)
    return users

async def leave_room(
    current_user: str,
    room_id: str
) -> Dict[str, Any]:
    room = nats_room_queries.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found for ID: " + room_id)

    user = user_queries.get_user_by_username(current_user)
    if not user:
        raise ValueError("User not found")

    nats_room_queries.remove_user_from_room(user_id=user.id, room_id=room.id)

    return {
        "message": f"User '{current_user}' left room '{room.name}' successfully."
    }

