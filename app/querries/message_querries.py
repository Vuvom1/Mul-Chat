from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.models import Message
from app.database.db import get_db

class MessageQueries:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
    
    # Create message
    def create_message(self, content: str, user_id: int, group_id: int):
        db_message = Message(content=content, user_id=user_id, group_id=group_id)
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return db_message
    
    # Get messages for a group
    def get_group_messages(self, group_id: int, skip: int = 0, limit: int = 100):
        return self.db.query(Message).filter(
            Message.group_id == group_id
        ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    # Get messages from a specific user
    def get_user_messages(self, user_id: int, skip: int = 0, limit: int = 100):
        return self.db.query(Message).filter(
            Message.user_id == user_id
        ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()