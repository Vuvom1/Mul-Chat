"""
Migration script to move NATS credentials from NatsUserCredential table to User table.
Run this script after updating models.py but before removing the NatsUserCredential table.
"""

import asyncio
import sys
import os
import logging
from dotenv import load_dotenv

# Add the parent directory to the path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db import get_db
from app.utils.migration_helpers import migrate_credentials_to_user, update_auth_sessions, verify_migration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def run_migration():
    """Run the migration process"""
    try:
        # Get database session
        db = next(get_db())
        
        # Step 1: Migrate credentials to User table
        logger.info("Starting migration of NATS credentials to User table...")
        count = migrate_credentials_to_user(db)
        logger.info(f"Migrated {count} NATS credentials to User table")
        
        # Step 2: Verify the migration
        if verify_migration(db):
            logger.info("Migration verification successful")
            
            # Step 3: Update auth sessions to remove credential_id references
            logger.info("Updating NatsAuthSession table...")
            if update_auth_sessions(db):
                logger.info("NatsAuthSession table updated successfully")
                
                logger.info("Migration completed successfully!")
                logger.info("You can now remove the NatsUserCredential table from models.py")
            else:
                logger.error("Failed to update NatsAuthSession table")
        else:
            logger.error("Migration verification failed. Some credentials may not have been migrated properly.")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
