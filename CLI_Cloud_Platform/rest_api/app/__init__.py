from flask import Flask
import os
import sys
from config import Config
from app.extensions import init_extensions
from app.utils.grpc_client import init_grpc_client

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    init_extensions(app)
    init_grpc_client(app)
    
    # Register blueprints
    from app.auth.routes import auth_bp
    from app.files.routes import files_bp
    from app.storage.routes import storage_bp
    from app.admin.routes import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(storage_bp, url_prefix='/api/storage')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    return app