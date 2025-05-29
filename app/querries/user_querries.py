from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.models import User
from app.database.db import get_db
from datetime import datetime

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
    
    # Update user NATS credentials
    def update_user_nats_credentials(self, user_id: int, seed_hash: str, 
                                    account_id: int, 
                                    expires_at=None):
        user = self.get_user(user_id)
        if not user:
            return None
        
        user.nats_seed_hash = seed_hash
        user.nats_account_id = account_id
        user.nats_expires_at = expires_at

        self.db.commit()
        self.db.refresh(user)
        return user
    
    # Get active NATS users (users with valid credentials)
    def get_active_nats_users(self):
        now = datetime.now()
        return self.db.query(User).filter(
            (User.nats_expires_at.is_(None) | (User.nats_expires_at > now)),
            User.nats_expired_at.is_(None)
        ).all()
    
    # Create new user with NATS credentials
    def create_user_with_nats_credentials(self, username: str, email: str, hashed_password: str, seed_hash: str,
                                         account_id: int, expires_at=None):
        db_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            nats_seed_hash=seed_hash,
            nats_account_id=account_id,
            nats_expires_at=expires_at
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    # Expire NATS credentials for a user
    def expire_nats_credentials(self, user_id: int):
        user = self.get_user(user_id)
        if not user:
            return None
        
        user.nats_expired_at = datetime.now()
        self.db.commit()
        self.db.refresh(user)
        return user