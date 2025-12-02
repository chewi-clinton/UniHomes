import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    GRPC_SERVER = os.environ.get('GRPC_SERVER', 'localhost:50051')
    ADMIN_KEY = os.environ.get('ADMIN_KEY', 'admin123')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    CORS_ORIGINS = ['http://localhost:3000', 'https://your-production-domain.com']
    
    # Database configuration (same as gRPC server)
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'cloud_storage')
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')