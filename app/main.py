import asyncio
import threading
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pages
from app.routers import chat_router
from app.routers import user_router
import logging
from dotenv import load_dotenv
from app.database.db import engine, get_db
from app.database import models
from sqlalchemy.orm import Session

from app.services.auth_service import start_auth_service

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables on application startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(chat_router.router, tags=["chat"])
app.include_router(pages.router)
app.include_router(user_router.router, tags=["user"])


# Add a simple DB test endpoint
@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    try:
        # Execute a simple query
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).fetchone()
        if result[0] == 1:
            return {"message": "Database connection successful!"}
        return {"message": "Database connection failed."}
    except Exception as e:
        return {"message": f"Database connection error: {str(e)}"}
    
@app.get("/test-nats")
async def test_nats():
    from app.services.auth_service import get_test_connection
    try:
        nc = await get_test_connection()
        return {"message": "NATS connection successful!"}
    except Exception as e:
        return {"message": f"NATS connection error: {str(e)}"}
    

# auth_service_thread = None

# # Define a function to run the auth service in a separate thread
# def run_auth_service_in_thread():
#     """Run the auth service in a separate thread"""
#     from app.services.auth_service import run_auth_service
    
#     # Create a new event loop for this thread
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
    
#     try:
#         # Run the auth service async function
#         # Make sure run_auth_service is an async function in your auth_service.py
#         loop.run_until_complete(run_auth_service())
#     except Exception as e:
#         logger.error(f"Error starting auth service: {str(e)}")
#     finally:
#         loop.close()

# @app.on_event("startup")
# async def startup_event():
#     """Start the application and the auth service in a background thread"""
#     global auth_service_thread
    
#     logger.info("Starting up the application...")
    
#     # Start auth service in a separate thread
#     auth_service_thread = threading.Thread(target=run_auth_service_in_thread, daemon=True)
#     auth_service_thread.start()
    
#     logger.info("Auth service started in background thread")

# @app.on_event("shutdown")
# async def shutdown_event():
#     """Clean up resources when the application shuts down"""
#     logger.info("Shutting down the application...")
    
#     # If you need to gracefully stop the auth service, add code here
#     # For example, you might want to implement a stop_auth_service() function
    
#     logger.info("Application shutdown complete.")

# Add an endpoint to check auth service status
# @app.get("/auth-service-status")
# async def auth_service_status():
#     """Check if the auth service is running"""
#     global auth_service_thread
    
#     if auth_service_thread and auth_service_thread.is_alive():
#         return {"status": "running"}
#     else:
#         return {"status": "not running"}
