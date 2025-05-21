from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.models import User
from app.database.db import get_db

class UserQueries:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
    
    # Get user by ID
    def get_user(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()
    
    # Get user by username
    def get_user_by_username(self, username: str):
        return self.db.query(User).filter(User.username == username).first()
    
    def get_hashed_password(self, username: str):
        user = self.db.query(User).filter(User.username == username).first()
        if user:
            return user.hashed_password
        return None
    
    # Get user by email
    def get_user_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()
    
    # Create new user
    def create_user(self, username: str, email: str, hashed_password: str):
        db_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    # Get all users
    def get_users(self, skip: int = 0, limit: int = 100):
        return self.db.query(User).offset(skip).limit(limit).all()