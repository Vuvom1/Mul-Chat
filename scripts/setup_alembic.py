"""
Setup script for Alembic migrations.
Run this script to initialize Alembic for database migrations.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_alembic():
    """Set up Alembic for database migrations"""
    try:
        # Check if alembic is installed
        try:
            subprocess.run(["alembic", "--version"], check=True, capture_output=True)
            logger.info("Alembic is already installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info("Installing Alembic...")
            subprocess.run(["pip", "install", "alembic"], check=True)
            logger.info("Alembic installed successfully")
        
        # Initialize alembic if not already initialized
        if not os.path.exists("alembic.ini"):
            logger.info("Initializing Alembic...")
            subprocess.run(["alembic", "init", "migrations"], check=True)
            logger.info("Alembic initialized successfully")
        
            # Update alembic.ini with database URL
            logger.info("Updating alembic.ini...")
            with open("alembic.ini", "r") as f:
                content = f.read()
            
            # Replace the sqlalchemy.url line
            # Note: You should update this with your actual database URL
            content = content.replace(
                "sqlalchemy.url = driver://user:pass@localhost/dbname",
                "sqlalchemy.url = sqlite:///./app.db"  # Update this with your actual database URL
            )
            
            with open("alembic.ini", "w") as f:
                f.write(content)
                
            # Update env.py to import models
            logger.info("Updating migrations/env.py...")
            with open("migrations/env.py", "r") as f:
                content = f.read()
            
            # Add imports for models and set target_metadata
            import_statement = "import os\nimport sys\nsys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\nfrom app.database.models import Base\n"
            content = content.replace("from alembic import context", "from alembic import context\n" + import_statement)
            content = content.replace("target_metadata = None", "target_metadata = Base.metadata")
            
            with open("migrations/env.py", "w") as f:
                f.write(content)
        
        # Create initial migration
        logger.info("Creating initial migration...")
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", "Initial migration"], check=True)
        
        # Apply migration
        logger.info("Applying migration...")
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        
        logger.info("Alembic setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up Alembic: {e}")
        return False

if __name__ == "__main__":
    success = setup_alembic()
    if success:
        print("Alembic setup completed successfully!")
        sys.exit(0)
    else:
        print("Failed to set up Alembic.")
        sys.exit(1)
