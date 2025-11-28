"""
Database Models
"""
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a unique ID"""
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    storage_allocated = Column(BigInteger, default=0)  # bytes
    storage_used = Column(BigInteger, default=0)  # bytes
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    files = relationship('File', back_populates='user', cascade='all, delete-orphan')
    folders = relationship('Folder', back_populates='user', cascade='all, delete-orphan')
    sessions = relationship('Session', back_populates='user', cascade='all, delete-orphan')


class Session(Base):
    __tablename__ = 'sessions'
    
    session_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='sessions')


class File(Base):
    __tablename__ = 'files'
    
    file_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=True)
    parent_folder_id = Column(String(36), ForeignKey('folders.folder_id'), nullable=True)
    is_shared = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='files')
    chunks = relationship('Chunk', back_populates='file', cascade='all, delete-orphan')
    parent_folder = relationship('Folder', back_populates='files')
    shares = relationship('FileShare', back_populates='file', cascade='all, delete-orphan')


class Folder(Base):
    __tablename__ = 'folders'
    
    folder_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    folder_name = Column(String(255), nullable=False)
    parent_folder_id = Column(String(36), ForeignKey('folders.folder_id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='folders')
    files = relationship('File', back_populates='parent_folder')
    parent_folder = relationship('Folder', remote_side=[folder_id], backref='subfolders')


class Chunk(Base):
    __tablename__ = 'chunks'
    
    chunk_id = Column(String(36), primary_key=True, default=generate_uuid)
    file_id = Column(String(36), ForeignKey('files.file_id'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    size = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=False)
    primary_node_id = Column(String(36), ForeignKey('storage_nodes.node_id'), nullable=False)
    replica_nodes = Column(JSON, default=list)  # List of node IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    file = relationship('File', back_populates='chunks')
    primary_node = relationship('StorageNode', foreign_keys=[primary_node_id])


class StorageNode(Base):
    __tablename__ = 'storage_nodes'
    
    node_id = Column(String(36), primary_key=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    storage_capacity = Column(BigInteger, nullable=False)  # bytes
    storage_used = Column(BigInteger, default=0)  # bytes
    cpu_cores = Column(Integer, default=1)
    status = Column(String(20), default='online')  # online, offline, maintenance
    health_score = Column(Integer, default=100)
    last_heartbeat = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FileShare(Base):
    __tablename__ = 'file_shares'
    
    share_id = Column(String(36), primary_key=True, default=generate_uuid)
    file_id = Column(String(36), ForeignKey('files.file_id'), nullable=False)
    shared_by_user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    shared_with_user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    share_token = Column(String(255), unique=True, nullable=False)
    permission = Column(String(20), default='read')  # read, write
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    file = relationship('File', back_populates='shares')
    shared_by = relationship('User', foreign_keys=[shared_by_user_id])
    shared_with = relationship('User', foreign_keys=[shared_with_user_id])


class SystemEvent(Base):
    __tablename__ = 'system_events'
    
    event_id = Column(String(36), primary_key=True, default=generate_uuid)
    event_type = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    user_id = Column(String(36), nullable=True)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)