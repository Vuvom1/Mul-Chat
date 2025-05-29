from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.models import NatsPermission, PermissionType
from app.database.db import get_db

class NatsPermissionQueries:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
    
    # Get permission by ID
    def get_permission(self, permission_id: int):
        return self.db.query(NatsPermission).filter(NatsPermission.id == permission_id).first()
    
    # Get permissions by user ID
    def get_permissions_by_user(self, user_id: int):
        return self.db.query(NatsPermission).filter(NatsPermission.user_id == user_id).all()
    
    # Get permissions by room ID
    def get_permissions_by_room(self, room_id: int):
        return self.db.query(NatsPermission).filter(NatsPermission.room_id == room_id).all()
    
    # Get specific permission
    def get_specific_permission(self, user_id: int, room_id: int, permission_type: PermissionType = None):
        query = self.db.query(NatsPermission).filter(
            NatsPermission.user_id == user_id,
            NatsPermission.room_id == room_id
        )
        if permission_type:
            query = query.filter(NatsPermission.permission_type == permission_type)
        return query.all()
    
    # Create new permission
    def create_permission(self, user_id: int, room_id: int, permission_type: PermissionType, subject: str):
        db_permission = NatsPermission(
            user_id=user_id,
            room_id=room_id,
            permission_type=permission_type,
            subject=subject
        )
        self.db.add(db_permission)
        self.db.commit()
        self.db.refresh(db_permission)
        return db_permission
    
    # Update permission
    def update_permission(self, permission_id: int, **kwargs):
        self.db.query(NatsPermission).filter(NatsPermission.id == permission_id).update(kwargs)
        self.db.commit()
        return self.get_permission(permission_id)
    
    # Delete permission
    def delete_permission(self, permission_id: int):
        permission = self.get_permission(permission_id)
        if permission:
            self.db.delete(permission)
            self.db.commit()
        return permission
    
    # Delete all permissions for a user in a room
    def delete_user_room_permissions(self, user_id: int, room_id: int):
        return self.db.query(NatsPermission).filter(
            NatsPermission.user_id == user_id,
            NatsPermission.room_id == room_id
        ).delete()
