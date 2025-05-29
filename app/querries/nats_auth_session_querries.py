from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.models import NatsAuthSession
from app.database.db import get_db
from datetime import datetime

class NatsAuthSessionQueries:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
    
    # Get session by ID
    def get_session(self, session_id: int):
        return self.db.query(NatsAuthSession).filter(NatsAuthSession.id == session_id).first()
    
    # Get sessions by user ID
    def get_sessions_by_user(self, user_id: int, active_only: bool = False):
        query = self.db.query(NatsAuthSession).filter(NatsAuthSession.user_id == user_id)
        if active_only:
            now = datetime.now()
            query = query.filter(
                NatsAuthSession.active == True,
                (NatsAuthSession.expires_at.is_(None) | (NatsAuthSession.expires_at > now))
            )
        return query.all()
    
    # Get session by client ID
    def get_session_by_client_id(self, client_id: str, active_only: bool = True):
        query = self.db.query(NatsAuthSession).filter(NatsAuthSession.client_id == client_id)
        if active_only:
            now = datetime.now()
            query = query.filter(
                NatsAuthSession.active == True,
                (NatsAuthSession.expires_at.is_(None) | (NatsAuthSession.expires_at > now))
            )
        return query.first()
    
    # Create new session
    def create_session(self, user_id: int, client_id: str, 
                       ip_address: str = None, user_agent: str = None, expires_at: datetime = None):
        db_session = NatsAuthSession(
            user_id=user_id,
            client_id=client_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            active=True
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session
    
    # Update session activity
    def update_session_activity(self, session_id: int):
        return self.update_session(session_id, last_activity=datetime.now())
    
    # Update session
    def update_session(self, session_id: int, **kwargs):
        self.db.query(NatsAuthSession).filter(NatsAuthSession.id == session_id).update(kwargs)
        self.db.commit()
        return self.get_session(session_id)
    
    # Deactivate session
    def deactivate_session(self, session_id: int):
        return self.update_session(session_id, active=False)
    
    # Delete session
    def delete_session(self, session_id: int):
        session = self.get_session(session_id)
        if session:
            self.db.delete(session)
            self.db.commit()
        return session
