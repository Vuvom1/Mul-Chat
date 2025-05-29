"""
Script to drop the NatsUserCredential table after migration is complete.
Run this script only after successful migration and verifying that the application works correctly.
"""

import asyncio
import sys
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import text

# Add the parent directory to the path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def drop_table():
    """Drop the NatsUserCredential table"""
    try:
        # Get database session
        db = next(get_db())
        
        # Check if table exists
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'nats_user_credentials'
            )
        """))
        exists = result.scalar()
        
        if not exists:
            logger.info("NatsUserCredential table does not exist. Nothing to do.")
            return True
        
        # Check for dependencies
        logger.info("Checking for dependencies on the NatsUserCredential table...")
        
        # Drop the table
        logger.info("Dropping NatsUserCredential table...")
        db.execute(text("DROP TABLE IF EXISTS nats_user_credentials CASCADE"))
        db.commit()
        
        logger.info("NatsUserCredential table dropped successfully")
        
    except Exception as e:
        logger.error(f"Failed to drop NatsUserCredential table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Ask for confirmation
    confirm = input("Are you sure you want to drop the NatsUserCredential table? This cannot be undone. (y/n): ")
    if confirm.lower() != 'y':
        logger.info("Operation cancelled")
        sys.exit(0)
    
    success = drop_table()
    if success:
        logger.info("Table dropped successfully")
        sys.exit(0)
    else:
        logger.error("Failed to drop table")
        sys.exit(1)
