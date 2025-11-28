"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
from dotenv import load_dotenv
from .models import Base

load_dotenv()

class Database:
    def __init__(self):
        self.db_url = os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@localhost:5432/cloud_storage'
        )
        
        self.engine = create_engine(
            self.db_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
        
        self.SessionFactory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.SessionFactory)
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
        print("[DATABASE] Tables created successfully")
    
    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(self.engine)
        print("[DATABASE] Tables dropped")
    
    @contextmanager
    def get_session(self):
        """Get a database session with automatic commit/rollback"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_new_session(self):
        """Get a new database session (caller must manage it)"""
        return self.SessionFactory()
    
    def close(self):
        """Close database connections"""
        self.Session.remove()
        self.engine.dispose()

# Global database instance
db = Database()

def init_database():
    """Initialize database and create tables"""
    db.create_tables()
    print("[DATABASE] Database initialized")

def get_db_session():
    """Get a database session"""
    return db.get_session()