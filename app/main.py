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