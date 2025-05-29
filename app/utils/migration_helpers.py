"""
This file provides utility functions to migrate data from the NatsUserCredential table to the User table.
After migration is complete, this file can be deleted.
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.querries.user_querries import UserQueries
import logging

logger = logging.getLogger(__name__)

def migrate_credentials_to_user(db: Session = Depends(get_db)):
    """
    Migrate data from the NatsUserCredential table to the User table.
    This function should be run once during the migration process.
    
    Args:
        db: Database session
        
    Returns:
        int: Number of migrated credentials
    """
    try:
        # Execute SQL directly to perform the migration
        # This assumes that both tables exist during migration
        result = db.execute("""
            UPDATE users u
            SET 
                nats_jwt = c.jwt,
                nats_seed_hash = c.seed_hash,
                nats_public_key = c.public_key,
                nats_account_id = c.account_id,
                nats_account_public_key = c.account_public_key,
                nats_expires_at = c.expires_at,
                nats_expired_at = c.expired_at
            FROM nats_user_credentials c
            WHERE u.id = c.user_id
        """)
        
        # Commit the changes
        db.commit()
        
        # Get the number of affected rows
        count = result.rowcount
        logger.info(f"Migrated {count} NATS credentials to User table")
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Error migrating NATS credentials: {e}")
        raise

def update_auth_sessions(db: Session = Depends(get_db)):
    """
    Update NatsAuthSession table to remove credential_id references.
    This function should be run once during the migration process.
    
    Args:
        db: Database session
        
    Returns:
        int: Number of updated sessions
    """
    try:
        # Execute SQL directly to update sessions
        # This will keep only the user_id reference and drop the credential_id column
        result = db.execute("""
            ALTER TABLE nats_auth_sessions 
            DROP COLUMN credential_id
        """)
        
        # Commit the changes
        db.commit()
        
        logger.info("Updated NatsAuthSession table to remove credential_id references")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating NatsAuthSession table: {e}")
        raise

def verify_migration(db: Session = Depends(get_db)):
    """
    Verify that all users with credentials in the old table have been properly migrated.
    
    Args:
        db: Database session
        
    Returns:
        bool: True if migration is complete, False otherwise
    """
    try:
        # Count users with missing credentials that should have them
        missing = db.execute("""
            SELECT COUNT(*) FROM users u
            JOIN nats_user_credentials c ON u.id = c.user_id
            WHERE u.nats_jwt IS NULL OR u.nats_public_key IS NULL
        """).scalar()
        
        if missing > 0:
            logger.warning(f"Found {missing} users with missing NATS credentials")
            return False
        
        logger.info("All NATS credentials have been successfully migrated")
        return True
    except Exception as e:
        logger.error(f"Error verifying NATS credentials migration: {e}")
        return False
