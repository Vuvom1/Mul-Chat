"""
This script updates NATS credentials in the User table to ensure all required fields are present.
It adds jwt, public_key, and account_public_key fields if they're missing.
"""

import sys
import os
import logging
import base64
import json
from datetime import datetime

# Add the parent directory to the path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db import get_db
from app.querries.user_querries import UserQueries
from app.utils.nats_helpers import extract_jwt_and_nkeys_seed_from_file
from app.nats.ncs import get_creds_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_user_nats_fields():
    """Update NATS fields for users"""
    try:
        # Get database session
        db = next(get_db())
        user_queries = UserQueries(db)
        
        # Get all users with NATS credentials
        users = user_queries.get_active_nats_users()
        logger.info(f"Found {len(users)} users with active NATS credentials")
        
        updated_count = 0
        for user in users:
            # Check if required fields are missing
            if not user.nats_jwt or not user.nats_public_key or not user.nats_account_public_key:
                logger.info(f"User {user.username} is missing NATS fields, attempting to update...")
                
                # Get credentials file path
                creds_file = get_creds_path(user.username)
                if not creds_file:
                    logger.warning(f"Credentials file for user {user.username} not found")
                    continue
                
                # Extract credential information
                jwt, seed, public_key, account_public_key = extract_jwt_and_nkeys_seed_from_file(creds_file)
                if not jwt or not public_key or not account_public_key:
                    logger.warning(f"Failed to extract credential information for user {user.username}")
                    continue
                
                # Update user's NATS fields
                user.nats_jwt = jwt
                user.nats_public_key = public_key
                user.nats_account_public_key = account_public_key
                
                # If seed has changed, update it
                if seed and seed != user.nats_seed_hash:
                    user.nats_seed_hash = seed
                
                db.commit()
                updated_count += 1
                logger.info(f"Updated NATS fields for user {user.username}")
                
        logger.info(f"Updated NATS fields for {updated_count} users")
        return True
        
    except Exception as e:
        logger.error(f"Error updating NATS fields: {e}")
        return False

if __name__ == "__main__":
    success = update_user_nats_fields()
    if success:
        print("NATS fields updated successfully!")
        sys.exit(0)
    else:
        print("Failed to update NATS fields.")
        sys.exit(1)
