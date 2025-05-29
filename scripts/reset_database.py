# reset_db_psycopg2.py
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def reset_database_with_psycopg2():
    # Connection information
    dbname = "postgres"  # The database we want to reset
    admin_dbname = "template1"  # Connect to a different database to drop postgres
    user = "postgres"
    password = "password123"
    host = "localhost"
    
    # Connect to a different database first (template1 is always available)
    conn = psycopg2.connect(
        dbname=admin_dbname,
        user=user,
        password=password,
        host=host
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    try:
        # Terminate all connections to the target database
        cursor.execute(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{dbname}'
        AND pid <> pg_backend_pid();
        """)
        
        # Drop database if it exists
        cursor.execute(f"DROP DATABASE IF EXISTS {dbname}")
        
        # Create database again
        cursor.execute(f"CREATE DATABASE {dbname}")
        
        print(f"Database '{dbname}' has been reset successfully!")
    except Exception as e:
        print(f"Error resetting database: {e}")
    finally:
        cursor.close()
        conn.close()
    
    # Update alembic.ini to use PostgreSQL
    import configparser
    config = configparser.ConfigParser()
    config.read('alembic.ini')
    
    # Set PostgreSQL URL in alembic.ini
    postgres_url = f"postgresql://{user}:{password}@{host}/{dbname}"
    config.set('alembic', 'sqlalchemy.url', postgres_url)
    
    with open('alembic.ini', 'w') as f:
        config.write(f)
    
    # Apply migrations
    import subprocess
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Migrations applied successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error applying migrations: {e}")
        # Fix migrations issues if needed
        fix_migrations()

def fix_migrations():
    """Fix any migration issues"""
    # Check if we need to stamp the current state
    import subprocess
    try:
        # Stamp the database to the initial migration state
        subprocess.run(["alembic", "stamp", "head"], check=True)
        print("Migration state has been stamped as current.")
    except subprocess.CalledProcessError as e:
        print(f"Error stamping migration state: {e}")

if __name__ == "__main__":
    reset_database_with_psycopg2()
