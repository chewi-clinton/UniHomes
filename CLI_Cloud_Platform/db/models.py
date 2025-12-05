"""
Database Models - Complete merged version
Includes core file storage system + extended payment and storage purchase system
"""

from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, JSON, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum


Base = declarative_base()


def generate_uuid():
    """Generate a unique ID"""
    return str(uuid.uuid4())


# ----------------------------------------------------------------------
# Enums for Payment System
# ----------------------------------------------------------------------
class PaymentStatus(enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentProvider(enum.Enum):
    """Payment provider enumeration"""
    MTN_MOMO = "mtn_momo"
    ORANGE_MONEY = "orange_money"


# ----------------------------------------------------------------------
# Core Models (File Storage System)
# ----------------------------------------------------------------------
class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    storage_allocated = Column(BigInteger, default=0)  # bytes
    storage_used = Column(BigInteger, default=0)  # bytes
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships - Core
    files = relationship('File', back_populates='user', cascade='all, delete-orphan')
    folders = relationship('Folder', back_populates='user', cascade='all, delete-orphan')
    sessions = relationship('Session', back_populates='user', cascade='all, delete-orphan')
    
    # Relationships - Payment System (added)
    payments = relationship('Payment', back_populates='user', cascade='all, delete-orphan')
    storage_purchases = relationship('StoragePurchase', back_populates='user')


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
    metadatas = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ----------------------------------------------------------------------
# Extended Payment System Models
# ----------------------------------------------------------------------
class StorageTier(Base):
    """Storage purchase tiers"""
    __tablename__ = 'storage_tiers'

    tier_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), nullable=False, unique=True)  # e.g., "Starter", "Pro"
    display_name = Column(String(100), nullable=False)
    storage_bytes = Column(BigInteger, nullable=False)  # Additional storage in bytes
    price_xaf = Column(Integer, nullable=False)  # Price in XAF (Central African Franc)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    payments = relationship('Payment', back_populates='tier')


class Payment(Base):
    """Payment transactions"""
    __tablename__ = 'payments'

    payment_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    tier_id = Column(String(36), ForeignKey('storage_tiers.tier_id'), nullable=False)

    # Payment details
    amount_xaf = Column(Integer, nullable=False)
    storage_bytes = Column(BigInteger, nullable=False)
    provider = Column(String(20), nullable=False)  # mtn_momo, orange_money
    phone_number = Column(String(20), nullable=False)

    # Transaction tracking
    transaction_ref = Column(String(100), unique=True, nullable=False)  # Our internal ref
    external_ref = Column(String(100), nullable=True)  # Campay reference
    campay_transaction_id = Column(String(100), nullable=True)

    # Status tracking
    status = Column(String(20), default='pending', nullable=False)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Metadata - FIXED: renamed to avoid SQLAlchemy conflict
    payment_metadata = Column(JSON, default=dict)  # Additional data from Campay

    # Relationships
    user = relationship('User', back_populates='payments')
    tier = relationship('StorageTier', back_populates='payments')
    storage_purchase = relationship('StoragePurchase', back_populates='payment', uselist=False)
    webhooks = relationship('PaymentWebhook', back_populates='payment')


class StoragePurchase(Base):
    """Storage purchase history - tracks actual storage additions"""
    __tablename__ = 'storage_purchases'

    purchase_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    payment_id = Column(String(36), ForeignKey('payments.payment_id'), nullable=False)
    storage_bytes = Column(BigInteger, nullable=False)
    previous_allocation = Column(BigInteger, nullable=False)
    new_allocation = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='storage_purchases')
    payment = relationship('Payment')


class PaymentWebhook(Base):
    """Log all webhook callbacks from Campay"""
    __tablename__ = 'payment_webhooks'

    webhook_id = Column(String(36), primary_key=True, default=generate_uuid)
    payment_id = Column(String(36), ForeignKey('payments.payment_id'), nullable=True)

    # Webhook data
    external_ref = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False)
    raw_data = Column(JSON, nullable=False)  # Complete webhook payload
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    payment = relationship('Payment', back_populates='webhooks')