from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.models import UserGroup, User, Group
from app.database.db import get_db

class UserGroupQueries:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
    
    # Add user to group
    def add_user_to_group(self, user_id: int, group_id: int):
        db_user_group = UserGroup(user_id=user_id, group_id=group_id)
        self.db.add(db_user_group)
        self.db.commit()
        return db_user_group
    
    # Remove user from group
    def remove_user_from_group(self, user_id: int, group_id: int):
        db_user_group = self.db.query(UserGroup).filter(
            UserGroup.user_id == user_id, 
            UserGroup.group_id == group_id
        ).first()
        if db_user_group:
            self.db.delete(db_user_group)
            self.db.commit()
        return db_user_group
    
    # Get all groups for a user
    def get_user_groups(self, user_id: int):
        return self.db.query(Group).join(UserGroup).filter(UserGroup.user_id == user_id).all()
    
    # Get all users in a group
    def get_group_users(self, group_id: int):
        return self.db.query(User).join(UserGroup).filter(UserGroup.group_id == group_id).all()
    
    def is_user_in_group(self, user_id: int, group_id: int):
        return self.db.query(UserGroup).filter(
            UserGroup.user_id == user_id, 
            UserGroup.group_id == group_id
        ).first() is not None