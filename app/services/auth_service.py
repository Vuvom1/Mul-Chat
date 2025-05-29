import asyncio
import json
from typing import Any, Dict, List
from nats.aio.client import Client as NATS
from nacl.signing import SigningKey
import os
import jwt
import time
import base64
import nkeys
from dotenv import load_dotenv
import logging
from datetime import datetime

from app.shared.auth_token import AuthToken
from app.database.db import get_db
from app.querries.user_querries import UserQueries
from app.querries.nats_auth_session_querries import NatsAuthSessionQueries
from app.querries.nats_permission_querries import NatsPermissionQueries
from app.querries.nats_room_querries import NatsRoomQueries
from app.database.models import PermissionType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

USER_SEED = 'SUADAVQYP6ORBZIBGWK5XJSUHR7XFYHXJ6M2VCEMEARHXVUMS452HEDNAI'
USER_JWT= 'eyJ0eXAiOiJKV1QiLCJhbGciOiJlZDI1NTE5LW5rZXkifQ.eyJqdGkiOiJRM0FDSzdNWTNJUzdFMktNTUNKMzRONU1RSkVKTkFKSjU2R0NJNVU2NEU0S1FYNFJCNFNRIiwiaWF0IjoxNzQ4MjQ2MTY2LCJpc3MiOiJBREdSQzdYVlpCMk1FWENKSkczWkQ2SzVCRTdWRUFDR1NETEhPNURTU0I3STM0WElETkVOWjRVMyIsIm5hbWUiOiJhbGljZSIsInN1YiI6IlVEUkwzRkMyWlFYUVNOTUY3VFRTWEdQTkJOWklBUEI1QkNXVlFWRUtNQzJFREVaQlJMNjJZRUVMIiwibmF0cyI6eyJwdWIiOnt9LCJzdWIiOnt9LCJzdWJzIjotMSwiZGF0YSI6LTEsInBheWxvYWQiOi0xLCJ0eXBlIjoidXNlciIsInZlcnNpb24iOjJ9fQ.So0KXcRIpg-dsxGRhXIDDBIN2dAHfQk6b02LO1vOeEaUS4QQQhmDN246HJAX-PCtukVqemBMl6NOqZnSpLgfAA'
NATS_SERVER_URL = os.getenv("NATS_SERVER_URL")
NATS_USER = os.getenv("NATS_USER")
NATS_PASSWORD = os.getenv("NATS_PASSWORD")
ISSUER_SEED = os.getenv("NATS_ISSUER_SEED")

# Initialize database session and queries
db = next(get_db())
user_queries = UserQueries(db)
nats_auth_session_queries = NatsAuthSessionQueries(db)
nats_permission_queries = NatsPermissionQueries(db)
nats_room_queries = NatsRoomQueries(db)

if not USER_SEED:
    raise ValueError("USER_SEED environment variable is not set")
if not USER_JWT:
    raise ValueError("USER_JWT environment variable is not set")


async def encode_authorization_response(user_nkey: str, server_id: str, 
                                        issuer_keypair, jwt_token: str = "", 
                                        error_msg: str = "") -> str:
    try:
        # Create the JWT payload
        now = int(time.time())
        payload = {
            "jti": f"response-{now}",
            "iat": now,
            "exp": now + 60,  # Response valid for 60 seconds
            "iss": issuer_keypair.public_key(),
            "sub": user_nkey,
            "nats": {
                "server_id": server_id,
                "jwt": jwt_token,
                "error": error_msg
            }
        }
        
        # Create header
        header = {
            "typ": "jwt",
            "alg": "ed25519-nkey"
        }
        
        # Sign the JWT using the issuer key
        encoded = jwt.encode(
            payload=payload,
            key=issuer_keypair.seed,
            algorithm="EdDSA",
            headers=header
        )
        
        return encoded
        
    except Exception as e:
        logger.error(f"Error encoding authorization response: {str(e)}")
        raise

async def encode_user_jwt(username: str, user_nkey: str, issuer_keypair,
                         allowed_pub: List[str], allowed_sub: List[str],
                         account: str) -> str:
    try:
        # Create the JWT payload
        now = int(time.time())
        payload = {
            "jti": f"user-{username}-{now}",
            "iat": now,
            "exp": now + 24*60*60,  # Token valid for 24 hours
            "iss": issuer_keypair.public_key(),
            "name": username,
            "sub": user_nkey,
            "aud": account,
            "nats": {
                "pub": {
                    "allow": allowed_pub
                },
                "sub": {
                    "allow": allowed_sub
                },
                "subs": -1,  # Unlimited subscriptions
                "data": -1,   # Unlimited data
                "payload": -1,  # Unlimited payload size
                "type": "user",
                "version": 2
            }
        }
        
        # Create header
        header = {
            "typ": "jwt",
            "alg": "ed25519-nkey"
        }
        
        # Sign the JWT using the issuer key
        encoded = jwt.encode(
            payload=payload,
            key=issuer_keypair.seed,
            algorithm="EdDSA",
            headers=header
        )
        
        return encoded
        
    except Exception as e:
        logger.error(f"Error encoding user JWT: {str(e)}")
        raise

async def verify_user_credentials(username: str, password: str) -> bool:
    # First check the database
    user = user_queries.get_user_by_username(username)
    if user and user.hashed_password == password:  # In a real app, verify the hashed password
        return True

async def get_user_permissions(username: str) -> Dict[str, List[str]]:
    """
    Get the publish and subscribe permissions for a user.
    """
    user = user_queries.get_user_by_username(username)
    
    # Get permissions from the database
    pub_permissions = []
    sub_permissions = []
    
    # Get all permissions for the user
    permissions = nats_permission_queries.get_permissions_by_user(user.id)
    
    for permission in permissions:
        if permission.permission_type == PermissionType.PUB or permission.permission_type == PermissionType.BOTH:
            pub_permissions.append(permission.subject)
        
        if permission.permission_type == PermissionType.SUB or permission.permission_type == PermissionType.BOTH:
            sub_permissions.append(permission.subject)
    
    return {
        "pub": pub_permissions,
        "sub": sub_permissions
    }

async def handle_auth_request(msg):
    logger.info(f"Received auth request: {msg.subject}")
    
    try:
        # Get the issuer keypair
        issuer_keypair = nkeys.from_seed(ISSUER_SEED.encode())
        
        # Decode the request
        request_data = json.loads(msg.data.decode())
        
        # Extract request details
        user_nkey = request_data.get("nats", {}).get("user_nkey", "")
        server_id = request_data.get("nats", {}).get("server_id", {}).get("id", "")
        connect_opts = request_data.get("nats", {}).get("connect_opts", {})
        auth_token_str = connect_opts.get("auth_token", "")
        requested_user = connect_opts.get("user", "")
        
        # Parse requested rooms (if any)
        requested_rooms = requested_user.split(";") if requested_user else []
        
        if not auth_token_str:
            # No auth token provided
            response = await encode_authorization_response(
                user_nkey, server_id, issuer_keypair, 
                error_msg="no auth_token in request"
            )
            await msg.respond(response.encode())
            return
            
        try:
            # Parse the auth token
            auth_token = AuthToken.from_dict(json.loads(auth_token_str))
        except Exception as e:
            # Invalid auth token format
            response = await encode_authorization_response(
                user_nkey, server_id, issuer_keypair, 
                error_msg=f"invalid auth token format: {str(e)}"
            )
            await msg.respond(response.encode())
            return
            
        # Check if the token signature is valid
        if not auth_token.verify_signature():
            response = await encode_authorization_response(
                user_nkey, server_id, issuer_keypair, 
                error_msg="invalid auth token signature"
            )
            await msg.respond(response.encode())
            return
        
        username = auth_token.user
        
        # Check if the user exists
        user = user_queries.get_user_by_username(username)
        if not user:
            response = await encode_authorization_response(
                user_nkey, server_id, issuer_keypair, 
                error_msg=f"user {username} not found"
            )
            await msg.respond(response.encode())
            return
        
        # Get the client_id from the request if available
        client_id = connect_opts.get("client_id", user_nkey)
        
        # If user exists in the database, update or create auth session
        if user:
            # Check if user has active credentials
            if not user.nats_jwt or not user.nats_public_key:
                response = await encode_authorization_response(
                    user_nkey, server_id, issuer_keypair, 
                    error_msg=f"no active credential for user {username}"
                )
                await msg.respond(response.encode())
                return
            
            # Check for existing session
            session = nats_auth_session_queries.get_session_by_client_id(client_id)
            if session:
                # Update last activity
                nats_auth_session_queries.update_session_activity(session.id)
            else:
                # Create new session
                ip_address = request_data.get("nats", {}).get("client_ip", "")
                user_agent = connect_opts.get("user_agent", "")
                
                nats_auth_session_queries.create_session(
                    user_id=user.id,
                    client_id=client_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
        
        # Get permissions for the user
        permissions = await get_user_permissions(username)
        
        # Create user JWT with permissions
        user_jwt = await encode_user_jwt(
            username=username,
            user_nkey=user_nkey,
            issuer_keypair=issuer_keypair,
            allowed_pub=permissions["pub"],
            allowed_sub=permissions["sub"],
            account=user.account.name if user.account else "default_account"
        )
        
        # Send successful response with JWT
        response = await encode_authorization_response(
            user_nkey=user_nkey,
            server_id=server_id,
            issuer_keypair=issuer_keypair,
            jwt_token=user_jwt
        )
        
        await msg.respond(response.encode())
        logger.info(f"Authorized user {username}")
        
    except Exception as e:
        logger.error(f"Error handling auth request: {str(e)}")
        # Try to respond with an error message
        try:
            issuer_keypair = nkeys.from_seed(ISSUER_SEED.encode())
            request_data = json.loads(msg.data.decode())
            user_nkey = request_data.get("nats", {}).get("user_nkey", "")
            server_id = request_data.get("nats", {}).get("server_id", {}).get("id", "")
            
            response = await encode_authorization_response(
                user_nkey=user_nkey,
                server_id=server_id,
                issuer_keypair=issuer_keypair,
                error_msg=f"internal server error: {str(e)}"
            )
            await msg.respond(response.encode())
        except Exception as nested_e:
            logger.error(f"Failed to send error response: {str(nested_e)}")

async def run_auth_service():
    """Start the NATS authentication service"""
    try:
        logger.info(f"Starting NATS authentication service on {NATS_SERVER_URL}")
        
        nc = NATS()
        # Connect to NATS
        await nc.connect(
            servers=[NATS_SERVER_URL],
            user=NATS_USER,
            password=NATS_PASSWORD
        )
        logger.info("Connected to NATS server")
        
        # Subscribe to auth requests
        sub = await nc.subscribe("$SYS.REQ.USER.AUTH", cb=handle_auth_request)
        logger.info(f"Listening for authentication requests on {sub.subject}...")
        
        # Keep the service running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Authentication service stopped by user")
    except Exception as e:
        logger.error(f"Error in authentication service: {str(e)}")
    finally:
        # Ensure NATS connection is properly closed
        try:
            await nc.drain()
            logger.info("NATS connection drained")
        except:
            pass

# Function to run the authentication service
def start_auth_service():
    """Start the NATS authentication service"""
    asyncio.run(run_auth_service())
    logger.info("NATS authentication service started")


