import base64
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
from app.querries.nats_account_querries import NatsAccountQueries
from app.querries.nats_auth_session_querries import NatsAuthSessionQueries
from app.querries.nats_room_querries import NatsRoomQueries
from app.querries.nats_permission_querries import NatsPermissionQueries
from app.database.models import PermissionType
from app.services.auth_service import verify_user_credentials
from app.database.db import get_db
from datetime import datetime, timedelta

from app.utils.nats_helpers import extract_jwt_and_nkeys_seed_from_file

db = next(get_db())

# Initialize queries
user_group_queries = UserGroupQueries(db)
group_queries = GroupQueries(db)
user_queries = UserQueries(db)
message_queries = MessageQueries(db)
nats_account_queries = NatsAccountQueries(db)
nats_session_queries = NatsAuthSessionQueries(db)
nats_room_queries = NatsRoomQueries(db)
nats_permission_queries = NatsPermissionQueries(db)

# Load environment variables from .env file
load_dotenv()
logger = logging.getLogger(__name__)

async def create_user(username: str, password: str, email: str = None):
    from app.nats.ncs import create_user as ncs_create_user, get_creds_path
    from app.utils.nats_helpers import extract_jwt_and_nkeys_seed_from_file
    
    # Check if the user already exists
    existing_user = user_queries.get_user_by_username(username)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create the user in the database
    ncs_create_user(username, 'chat-app')  # This would create the user in NATS

    # Get the creds_path from environment variable
    creds_file = get_creds_path(username)
    if not creds_file:
        logger.error(f"Credentials file for user {username} not found")
        return False
    
    # Set expiration to 30 days from now
    expires_at = datetime.now() + timedelta(days=30)

    jwt, seed, public_key, account_public_key = extract_jwt_and_nkeys_seed_from_file(creds_file)
    if not jwt or not seed or not public_key or not account_public_key:
        logger.error(f"Failed to extract JWT or seed from credentials file for user {username}")
        return False
    
    # Get user information from decoded JWT
    user_info = json.loads(base64.urlsafe_b64decode(jwt.split('.')[1] + '=='))

    # Find or create NATS account
    account = nats_account_queries.get_account_by_public_key(account_public_key)
    if not account:
        account = nats_account_queries.create_account(
            name="chat-app",  # Using the account name from ncs_create_user
            public_key=account_public_key
        )

    # Create user in database with NATS credentials
    user = user_queries.create_user_with_nats_credentials(
        username=username,
        hashed_password=password,  # In a real app, this should be hashed
        email=email,
        seed_hash= seed,
        account_id=account.id,
    )
    # Extract permissions from JWT to identify rooms
    permissions = []
    if 'nats' in user_info and 'pub' in user_info['nats'] and 'allow' in user_info['nats']['pub']:
        pub_allow = user_info['nats']['pub']['allow']
        for subject in pub_allow:
            # Extract room name from subject pattern
            parts = subject.split('.')
            if len(parts) >= 1:
                room_name = parts[0]
                
                # Skip if it's a wildcard
                if room_name == '>' or room_name == '*':
                    continue
                    
                # Create room if it doesn't exist
                room = nats_room_queries.get_room_by_name(room_name)
                if not room:
                    room = create_room(room_name)
                
                permissions.append(room_name)

    logger.info(f"Added user {user.username} with permissions for rooms: {permissions}")
    return jwt
    
async def login_user(username: str, password: str, client_id: str = None, ip_address: str = None, user_agent: str = None):
    from app.nats.ncs import get_creds_path    
    # Verify credentials (this would check the hashed password in a real app)
    isVerified = await verify_user_credentials(username, password)
    if not isVerified:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Get the user from database
    db_user = user_queries.get_user_by_username(username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get jwt from credentials file
    creds_file = get_creds_path(username)
    if not creds_file:
        logger.error(f"Credentials file for user {username} not found")
        raise HTTPException(status_code=404, detail="Credentials file not found")
    jwt, seed, public_key, account_public_key = extract_jwt_and_nkeys_seed_from_file(creds_file)

    if not jwt or not seed or not public_key or not account_public_key:
        logger.error(f"Failed to extract JWT or seed from credentials file for user {username}")
        raise HTTPException(status_code=404, detail="Failed to extract JWT or seed")
    
    chat_rooms = nats_room_queries.get_rooms_for_user(db_user.id)

    return {
        "jwt": jwt,
        "chat_rooms": [room.name for room in chat_rooms],
    }

# Remaining functions
def get_nats_users():
    """
    Get a list of users from NATS server.
    """
    from app.nats.ncs import get_users
    nats_users = []
    try:
        # Assuming 'chat' is the account name
        nats_users = get_users("chat")
        if not nats_users:
            logger.info("No users found in NATS server.")
    except Exception as e:
        logger.error(f"Error fetching users from NATS server: {e}")
    
    return nats_users

def get_operators():
    """
    Get a list of operators from NATS server.
    """
    from app.nats.ncs import get_operators
    import base64
    import json
    nats_operators = []
    try:
        nats_operators = get_operators()
        if not nats_operators:
            logger.info("No operators found in NATS server.")
    except Exception as e:
        logger.error(f"Error fetching operators from NATS server: {e}")
    
    return nats_operators

# New functions for NATS authentication

def get_user_rooms(username: str):
    """
    Get all rooms that a user has access to.
    """
    user = user_queries.get_user_by_username(username)
    if not user:
        return []
    
    return nats_room_queries.get_rooms_for_user(user.id)

def get_room_users(room_name: str):
    """
    Get all users in a specific room.
    """
    room = nats_room_queries.get_room_by_name(room_name)
    if not room:
        return []
    
    return nats_room_queries.get_users_in_room(room.id)

def add_user_to_room(username: str, room_name: str):
    """
    Add a user to a room and grant necessary permissions.
    """
    user = user_queries.get_user_by_username(username)
    if not user:
        logger.error(f"User {username} not found")
        return False
    
    room = nats_room_queries.get_room_by_name(room_name)
    if not room:
        logger.error(f"Room {room_name} not found")
        return False
    
    # Add user to room
    nats_room_queries.add_user_to_room(user.id, room.id)
    
    # Create permissions for the room
    # PUB permission
    nats_permission_queries.create_permission(
        user_id=user.id,
        room_id=room.id,
        permission_type=PermissionType.PUB,
        subject=f"chat.{room_name}"
    )
    
    # SUB permission
    nats_permission_queries.create_permission(
        user_id=user.id,
        room_id=room.id,
        permission_type=PermissionType.SUB,
        subject=f"chat.{room_name}"
    )
    
    logger.info(f"Added user {username} to room {room_name}")
    return True

async def get_user_information(username: str):
    user = user_queries.get_user_by_username(username)
    if not user:
        logger.error(f"User {username} not found")
        return None
    
    # Get NATS account information
    nats_account = nats_account_queries.get_account(user.nats_account_id) if user.nats_account_id else None
    
    # Get NATS permissions
    permissions = nats_permission_queries.get_permissions_by_user(user.id)
    
    return {
        "username": user.username,
        "email": user.email,
        "nats_account": nats_account.name if nats_account else None,
        "permissions": [perm.subject for perm in permissions],
        "created_at": user.created_at.isoformat(),
        "nats_expires_at": user.nats_expires_at.isoformat() if user.nats_expires_at else None,
        "nats_expired_at": user.nats_expired_at.isoformat() if user.nats_expired_at else None
    }

def remove_user_from_room(username: str, room_name: str):
    """
    Remove a user from a room and revoke permissions.
    """
    user = user_queries.get_user_by_username(username)
    if not user:
        logger.error(f"User {username} not found")
        return False
    
    room = nats_room_queries.get_room_by_name(room_name)
    if not room:
        logger.error(f"Room {room_name} not found")
        return False
    
    # Remove user from room
    nats_room_queries.remove_user_from_room(user.id, room.id)
    
    # Delete all permissions for the user in this room
    nats_permission_queries.delete_user_room_permissions(user.id, room.id)
    
    logger.info(f"Removed user {username} from room {room_name}")
    return True

def create_room(room_name: str, is_public: bool = False, description: str = None, account_name: str = "default"):
    """
    Create a new chat room.
    """
    # Check if room already exists
    existing_room = nats_room_queries.get_room_by_name(room_name)
    if existing_room:
        logger.warning(f"Room {room_name} already exists")
        return existing_room
    
    # Get account
    account = nats_account_queries.get_account_by_name(account_name)
    if not account:
        logger.error(f"Account {account_name} not found")
        return None
    
    # Create room
    room = nats_room_queries.create_room(
        name=room_name,
        subject_prefix=f"chat.{room_name}",
        account_id=account.id,
        description=description,
        is_public=is_public
    )
    
    logger.info(f"Created room {room_name}")
    return room
