from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.models import NatsRoom, NatsUserRoom, User
from app.database.db import get_db

class NatsRoomQueries:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
    
    # Get room by ID
    def get_room(self, room_id: int):
        return self.db.query(NatsRoom).filter(NatsRoom.id == room_id).first()
    
    # Get room by name
    def get_room_by_name(self, name: str):
        return self.db.query(NatsRoom).filter(NatsRoom.name == name).first()
    
    # Get rooms by account ID
    def get_rooms_by_account(self, account_id: int):
        return self.db.query(NatsRoom).filter(NatsRoom.account_id == account_id).all()
    
    # Get public rooms
    def get_public_rooms(self, account_id: int = None):
        query = self.db.query(NatsRoom).filter(NatsRoom.is_public == True)
        if account_id:
            query = query.filter(NatsRoom.account_id == account_id)
        return query.all()
    
    # Create new room
    def create_room(self, name: str, subject_prefix: str, account_id: int, 
                    description: str = None, is_public: bool = False):
        db_room = NatsRoom(
            name=name,
            subject_prefix=subject_prefix,
            account_id=account_id,
            description=description,
            is_public=is_public
        )
        self.db.add(db_room)
        self.db.commit()
        self.db.refresh(db_room)
        return db_room
    
    # Add user to room
    def add_user_to_room(self, user_id: int, room_id: int):
        # Check if association already exists
        exists = self.db.query(NatsUserRoom).filter(
            NatsUserRoom.user_id == user_id,
            NatsUserRoom.room_id == room_id
        ).first()
        
        if not exists:
            user_room = NatsUserRoom(user_id=user_id, room_id=room_id)
            self.db.add(user_room)
            self.db.commit()
            return user_room
        return exists
    
    # Remove user from room
    def remove_user_from_room(self, user_id: int, room_id: int):
        user_room = self.db.query(NatsUserRoom).filter(
            NatsUserRoom.user_id == user_id,
            NatsUserRoom.room_id == room_id
        ).first()
        
        if user_room:
            self.db.delete(user_room)
            self.db.commit()
        return user_room
    
    # Get users in room
    def get_users_in_room(self, room_id: int):
        return self.db.query(User).join(
            NatsUserRoom, User.id == NatsUserRoom.user_id
        ).filter(NatsUserRoom.room_id == room_id).all()
    
    # Get rooms for user
    def get_rooms_for_user(self, user_id: int):
        return self.db.query(NatsRoom).join(
            NatsUserRoom, NatsRoom.id == NatsUserRoom.room_id
        ).filter(NatsUserRoom.user_id == user_id).all()
    
    def get_room_for_user_by_username(self, username: str):
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None
        return self.db.query(NatsRoom).join(
            NatsUserRoom, NatsRoom.id == NatsUserRoom.room_id
        ).filter(NatsUserRoom.user_id == user.id).all()
    
    # Update room
    def update_room(self, room_id: int, **kwargs):
        self.db.query(NatsRoom).filter(NatsRoom.id == room_id).update(kwargs)
        self.db.commit()
        return self.get_room(room_id)
    
    # Delete room
    def delete_room(self, room_id: int):
        room = self.get_room(room_id)
        if room:
            # First delete all user-room associations
            self.db.query(NatsUserRoom).filter(NatsUserRoom.room_id == room_id).delete()
            # Then delete the room
            self.db.delete(room)
            self.db.commit()
        return room
