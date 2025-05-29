import base64
import json
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import os
from app.utils.auth_helpers import verify_jwt_and_seed
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    from app.querries.user_querries import UserQueries
    from app.database.db import get_db
    db = next(get_db())
    user_queries = UserQueries(db)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try: 

        parts = token.split('.')
        payload_b64 = parts[1]
        # Add padding if needed
        padding = '=' * (4 - len(payload_b64) % 4) if len(payload_b64) % 4 != 0 else ''
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode('utf-8')
        payload = json.loads(payload_json)

        if not payload.get("name"):
            raise credentials_exception

        user = user_queries.get_user_by_username(payload["name"])

        if not user:
            raise credentials_exception
        isVerify, username = verify_jwt_and_seed(token, user.nats_seed_hash)

        if not isVerify:
            raise credentials_exception
        return username
    except Exception as e:
        raise credentials_exception from e
    
    