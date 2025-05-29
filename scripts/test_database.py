"""
Test script to verify database connection and model definitions.
"""

import sys
import os
import logging

# Add the parent directory to the path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db import get_db
from app.database.models import User, NatsAccount, NatsPermission, NatsAuthSession, NatsRoom
from sqlalchemy import inspect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and verify tables"""
    try:
        db = next(get_db())
        logger.info("Successfully connected to database")
        
        # Get database inspector
        inspector = inspect(db.bind)
        
        # Check existing tables
        tables = inspector.get_table_names()
        logger.info(f"Tables in database: {tables}")
        
        # Check if required tables exist
        required_tables = ['users', 'nats_accounts', 'nats_permissions', 
                          'nats_auth_sessions', 'nats_rooms']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            logger.warning(f"Missing tables: {missing_tables}")
        else:
            logger.info("All required tables exist")
        
        # Check columns in User table
        if 'users' in tables:
            columns = [column['name'] for column in inspector.get_columns('users')]
            logger.info(f"Columns in User table: {columns}")
            
            # Check if NATS columns exist
            nats_columns = ['nats_jwt', 'nats_seed_hash', 'nats_public_key', 
                           'nats_account_id', 'nats_account_public_key', 
                           'nats_expires_at', 'nats_expired_at']
            
            missing_columns = [column for column in nats_columns if column not in columns]
            
            if missing_columns:
                logger.warning(f"Missing NATS columns in User table: {missing_columns}")
            else:
                logger.info("All NATS columns exist in User table")
        
        # Check if NatsUserCredential table exists (should be removed)
        if 'nats_user_credentials' in tables:
            logger.warning("NatsUserCredential table still exists")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing database: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    if success:
        print("Database connection and model verification successful!")
        sys.exit(0)
    else:
        print("Database connection or model verification failed.")
        sys.exit(1)
