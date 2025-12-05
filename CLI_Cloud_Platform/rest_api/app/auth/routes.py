from flask import Blueprint, request, jsonify
from app.utils.grpc_client import get_grpc_client
from app.models.response import success_response, error_response
import generated.cloud_storage_pb2 as cloud_storage_pb2

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return error_response("Email is required"), 400
    
    client = get_grpc_client()
    try:
        response = client.auth_stub.SendOTP(
            cloud_storage_pb2.SendOTPRequest(email=email)
        )
        if response.success:
            return success_response(message=response.message)
        else:
            return error_response(response.message), 400
    except Exception as e:
        return error_response(f"Failed to send OTP: {str(e)}"), 500

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    
    if not email or not otp:
        return error_response("Email and OTP are required"), 400
    
    client = get_grpc_client()
    try:
        response = client.auth_stub.VerifyOTP(
            cloud_storage_pb2.VerifyOTPRequest(email=email, otp=otp)
        )
        if response.success:
            # Check if user exists in database
            try:
                # Try to check if user exists via gRPC
                check_response = client.auth_stub.CheckUserExists(
                    cloud_storage_pb2.CheckUserRequest(email=email)
                )
                user_exists = check_response.exists
            except:
                # If CheckUserExists doesn't exist, check database directly
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                import os
                
                db_url = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'postgres')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'cloud_storage')}"
                engine = create_engine(db_url)
                Session = sessionmaker(bind=engine)
                session = Session()
                
                # Import User model
                import sys
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                from db.models import User
                
                user = session.query(User).filter_by(email=email).first()
                user_exists = user is not None
                session.close()
            
            return success_response({
                'exists': user_exists,
                'message': response.message
            })
        else:
            return error_response(response.message), 400
    except Exception as e:
        return error_response(f"Failed to verify OTP: {str(e)}"), 500

@auth_bp.route('/enroll', methods=['POST'])
def enroll():
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    
    if not email or not name:
        return error_response("Email and name are required"), 400
    
    client = get_grpc_client()
    try:
        response = client.auth_stub.Enroll(
            cloud_storage_pb2.EnrollRequest(email=email, full_name=name)
        )
        if response.success:
            return success_response({
                'token': response.session_token,  # Changed from session_token to token for consistency
                'user': {
                    'user_id': response.user_id,
                    'email': email,
                    'name': name
                }
            }, response.message)
        else:
            return error_response(response.message), 400
    except Exception as e:
        return error_response(f"Failed to enroll: {str(e)}"), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return error_response("Email is required"), 400
    
    client = get_grpc_client()
    try:
        response = client.auth_stub.Login(
            cloud_storage_pb2.LoginRequest(email=email)
        )
        if response.success:
            return success_response({
                'token': response.session_token,  # Changed from session_token to token for consistency
                'user': {
                    'user_id': response.user_id,
                    'email': email
                }
            }, response.message)
        else:
            return error_response(response.message), 400
    except Exception as e:
        return error_response(f"Failed to login: {str(e)}"), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response("Authentication required"), 401
    
    session_token = auth_header.split(' ')[1]
    
    client = get_grpc_client()
    try:
        response = client.auth_stub.Logout(
            cloud_storage_pb2.LogoutRequest(session_token=session_token)
        )
        if response.success:
            return success_response(message=response.message)
        else:
            return error_response(response.message), 400
    except Exception as e:
        return error_response(f"Failed to logout: {str(e)}"), 500