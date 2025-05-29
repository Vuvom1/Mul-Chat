from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Table, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime
import enum

from .db import Base

# PermissionType enum for NATS permissions
class PermissionType(enum.Enum):
    PUB = "pub"
    SUB = "sub"
    BOTH = "both"

# Message table
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="messages")
    group = relationship("Group", back_populates="messages")

# User table
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    nats_seed_hash = Column(String(100), nullable=True)
    nats_account_id = Column(Integer, ForeignKey("nats_accounts.id"), nullable=True)
    nats_expires_at = Column(DateTime, nullable=True)
    nats_expired_at = Column(DateTime, nullable=True)
    
    # Relationships
    messages = relationship("Message", back_populates="user")
    groups = relationship("UserGroup", back_populates="user")
    nats_account = relationship("NatsAccount", foreign_keys=[nats_account_id])
    nats_auth_sessions = relationship("NatsAuthSession", back_populates="user")
    nats_permissions = relationship("NatsPermission", back_populates="user")
    nats_rooms = relationship("NatsUserRoom", back_populates="user")

# NatsAccount table
class NatsAccount(Base):
    __tablename__ = "nats_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    public_key = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    nats_rooms = relationship("NatsRoom", back_populates="account")

# NatsPermission table
class NatsPermission(Base):
    __tablename__ = "nats_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("nats_rooms.id"), nullable=False)
    permission_type = Column(Enum(PermissionType), nullable=False)
    subject = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="nats_permissions")
    room = relationship("NatsRoom", back_populates="permissions")

# NatsAuthSession table
class NatsAuthSession(Base):
    __tablename__ = "nats_auth_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(String(100), nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="nats_auth_sessions")

# NatsRoom table
class NatsRoom(Base):
    __tablename__ = "nats_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    subject_prefix = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    account_id = Column(Integer, ForeignKey("nats_accounts.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("NatsUserRoom", back_populates="room")
    permissions = relationship("NatsPermission", back_populates="room")
    account = relationship("NatsAccount", back_populates="nats_rooms")

# NatsUserRoom association table
class NatsUserRoom(Base):
    __tablename__ = "nats_user_rooms"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    room_id = Column(Integer, ForeignKey("nats_rooms.id"), primary_key=True)
    joined_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="nats_rooms")
    room = relationship("NatsRoom", back_populates="users")

# Group table
class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="group")
    users = relationship("UserGroup", back_populates="group")

# User Group association table
class UserGroup(Base):
    __tablename__ = "user_groups"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), primary_key=True)
    joined_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="groups")
    group = relationship("Group", back_populates="users")