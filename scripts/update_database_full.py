#!/usr/bin/env python3
"""
Master script to update the database schema and migrate data.
This script will:
1. Update the database schema based on models
2. Set up Alembic for future migrations
3. Update NATS fields for users
4. Run the NATS credential migration if needed
"""

import os
import sys
import subprocess
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_script(script_path, description):
    """Run a Python script and return True if successful"""
    try:
        logger.info(f"Running {description}...")
        result = subprocess.run([sys.executable, script_path], check=True)
        logger.info(f"{description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {description}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Update the database schema and migrate data.")
    parser.add_argument("--skip-schema", action="store_true", help="Skip database schema update")
    parser.add_argument("--skip-alembic", action="store_true", help="Skip Alembic setup")
    parser.add_argument("--skip-nats-fields", action="store_true", help="Skip NATS fields update")
    parser.add_argument("--skip-nats-migration", action="store_true", help="Skip NATS credential migration")
    parser.add_argument("--drop-nats-table", action="store_true", help="Drop the NatsUserCredential table")
    args = parser.parse_args()
    
    # Get the base directory of the script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Update the database schema
    if not args.skip_schema:
        success = run_script(
            os.path.join(base_dir, "scripts", "update_database.py"),
            "database schema update"
        )
        if not success:
            logger.error("Database schema update failed. Stopping.")
            return False
    
    # 2. Set up Alembic
    if not args.skip_alembic:
        success = run_script(
            os.path.join(base_dir, "scripts", "setup_alembic.py"),
            "Alembic setup"
        )
        if not success:
            logger.warning("Alembic setup failed, but continuing with other steps.")
    
    # 3. Update NATS fields
    if not args.skip_nats_fields:
        success = run_script(
            os.path.join(base_dir, "scripts", "update_nats_fields.py"),
            "NATS fields update"
        )
        if not success:
            logger.warning("NATS fields update failed, but continuing with other steps.")
    
    # 4. Run NATS credential migration
    if not args.skip_nats_migration:
        success = run_script(
            os.path.join(base_dir, "scripts", "migrate_nats_credentials.py"),
            "NATS credential migration"
        )
        if not success:
            logger.warning("NATS credential migration failed, but continuing with other steps.")
    
    # 5. Drop NatsUserCredential table if requested
    if args.drop_nats_table:
        logger.warning("About to drop the NatsUserCredential table. This cannot be undone!")
        confirm = input("Are you sure you want to proceed? (y/n): ")
        if confirm.lower() == 'y':
            success = run_script(
                os.path.join(base_dir, "scripts", "drop_nats_user_credential_table.py"),
                "Drop NatsUserCredential table"
            )
            if not success:
                logger.error("Failed to drop NatsUserCredential table.")
        else:
            logger.info("Skipping drop NatsUserCredential table.")
    
    logger.info("Database update process completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
