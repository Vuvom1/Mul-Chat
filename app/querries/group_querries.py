from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.models import Group
from app.database.db import get_db

class GroupQueries:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        
    # Get group by ID
    def get_group(self, group_id: int):
        return self.db.query(Group).filter(Group.id == group_id).first()
    
    # Get group by name
    def get_group_by_name(self, name: str):
        return self.db.query(Group).filter(Group.name == name).first()
    
    # Create new group
    def create_group(self, name: str, description: str = None):
        db_group = Group(name=name, description=description)
        self.db.add(db_group)
        self.db.commit()
        self.db.refresh(db_group)
        return db_group
    
    # Get all groups
    def get_groups(self, skip: int = 0, limit: int = 100):
        return self.db.query(Group).offset(skip).limit(limit).all()