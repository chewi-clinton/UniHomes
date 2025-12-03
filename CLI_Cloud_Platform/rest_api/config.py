import os
from datetime import timedelta
from dotenv import load_dotenv


load_dotenv()



class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    GRPC_SERVER = os.environ.get('GRPC_SERVER', 'localhost:50051')
    ADMIN_KEY = os.environ.get('ADMIN_KEY', 'admin123')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # CORS origins
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:5173',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173'
    ]
    
    # Database configuration (same as gRPC server)
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'cloud_storage')
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
    
    @classmethod
    def init_app(cls, app):
        """Initialize app with config - print debug info"""
        admin_key = app.config.get('ADMIN_KEY')
        if admin_key:
            print(f"[CONFIG] ✓ Admin Key Loaded: ***{admin_key[-4:]}")
        else:
            print(f"[CONFIG] ✗ Admin Key NOT LOADED!")
        print(f"[CONFIG] gRPC Server: {app.config.get('GRPC_SERVER')}")
        print(f"[CONFIG] Flask Env: {app.config.get('FLASK_ENV')}")