from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.models import NatsAccount
from app.database.db import get_db

class NatsAccountQueries:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
    
    # Get account by ID
    def get_account(self, account_id: int):
        return self.db.query(NatsAccount).filter(NatsAccount.id == account_id).first()
    
    # Get account by name
    def get_account_by_name(self, name: str):
        return self.db.query(NatsAccount).filter(NatsAccount.name == name).first()
    
    # Get account by public key
    def get_account_by_public_key(self, public_key: str):
        return self.db.query(NatsAccount).filter(NatsAccount.public_key == public_key).first()
    
    # Create new account
    def create_account(self, name: str, public_key: str, description: str = None):
        db_account = NatsAccount(
            name=name,
            public_key=public_key,
            description=description
        )
        self.db.add(db_account)
        self.db.commit()
        self.db.refresh(db_account)
        return db_account
    
    # Get all accounts
    def get_accounts(self, skip: int = 0, limit: int = 100):
        return self.db.query(NatsAccount).offset(skip).limit(limit).all()
    
    # Update account
    def update_account(self, account_id: int, **kwargs):
        self.db.query(NatsAccount).filter(NatsAccount.id == account_id).update(kwargs)
        self.db.commit()
        return self.get_account(account_id)
    
    # Delete account
    def delete_account(self, account_id: int):
        account = self.get_account(account_id)
        if account:
            self.db.delete(account)
            self.db.commit()
        return account
