"""
Script to update database schema based on SQLAlchemy models.
This will create any missing tables or columns but won't remove any existing ones.
"""

import sys
import os
import logging
from sqlalchemy import inspect

# Add the parent directory to the path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db import engine, Base
from app.database.models import *  # Import all models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_existing_tables():
    """Get a list of existing tables in the database"""
    inspector = inspect(engine)
    return inspector.get_table_names()

def get_existing_columns(table_name):
    """Get existing columns for a table"""
    inspector = inspect(engine)
    return {column['name']: column for column in inspector.get_columns(table_name)}

def update_database():
    """Update the database schema based on SQLAlchemy models"""
    try:
        # Get existing tables before update
        existing_tables_before = set(get_existing_tables())
        logger.info(f"Existing tables before update: {existing_tables_before}")
        
        # Create tables based on models
        logger.info("Updating database schema...")
        Base.metadata.create_all(engine)
        
        # Get tables after update
        existing_tables_after = set(get_existing_tables())
        logger.info(f"Existing tables after update: {existing_tables_after}")
        
        # Show new tables created
        new_tables = existing_tables_after - existing_tables_before
        if new_tables:
            logger.info(f"New tables created: {new_tables}")
        else:
            logger.info("No new tables created")
            
        # Check for columns in User table
        if 'users' in existing_tables_after:
            user_columns = get_existing_columns('users')
            nats_columns = [col for col in user_columns if col.startswith('nats_')]
            if nats_columns:
                logger.info(f"NATS columns in User table: {nats_columns}")
            else:
                logger.warning("NATS columns not found in User table. Schema might not be up to date.")
        
        logger.info("Database schema update completed")
        return True
        
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")
        return False

if __name__ == "__main__":
    success = update_database()
    if success:
        print("Database successfully updated!")
        sys.exit(0)
    else:
        print("Failed to update database.")
        sys.exit(1)
