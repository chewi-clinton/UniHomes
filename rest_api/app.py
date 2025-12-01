#!/usr/bin/env python3
"""
Flask REST API - Main Application
A production-ready REST API bridge to the gRPC Cloud Storage backend
"""
import os
import sys
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Add parent directory to path to import gRPC modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import route blueprints
from routes.auth_routes import auth_bp
from routes.file_routes import file_bp
from routes.storage_routes import storage_bp
from routes.admin_routes import admin_bp
from middleware.error_handlers import register_error_handlers

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5GB max file size
    app.config['JSON_SORT_KEYS'] = False
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # CORS Configuration - Allow React frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "http://localhost:5173",  # Vite default
                os.getenv('FRONTEND_URL', 'http://localhost:3000')
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Disposition"],
            "supports_credentials": True
        }
    })
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(file_bp, url_prefix='/api/files')
    app.register_blueprint(storage_bp, url_prefix='/api/storage')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'success': True,
            'message': 'Flask REST API is running',
            'grpc_server': os.getenv('GRPC_SERVER', 'localhost:50051')
        }
    
    @app.route('/')
    def index():
        return {
            'success': True,
            'message': 'Cloud Storage REST API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'files': '/api/files',
                'storage': '/api/storage',
                'admin': '/api/admin',
                'health': '/health'
            }
        }
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 8000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    print("=" * 80)
    print("CLOUD STORAGE - FLASK REST API")
    print("=" * 80)
    print(f"Server: http://{host}:{port}")
    print(f"Environment: {'Development' if debug else 'Production'}")
    print(f"gRPC Backend: {os.getenv('GRPC_SERVER', 'localhost:50051')}")
    print(f"CORS Origins: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}")
    print("=" * 80)
    print("\n[READY] Flask REST API is ready to accept connections\n")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )