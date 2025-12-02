from flask import Blueprint, request, jsonify
from app.utils.grpc_client import get_grpc_client
from app.models.response import success_response, error_response
import generated.cloud_storage_pb2 as cloud_storage_pb2
import grpc

storage_bp = Blueprint('storage', __name__)

def get_session_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    return auth_header.split(' ')[1]

@storage_bp.route('', methods=['GET'])
def get_storage_info():
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
    
    client = get_grpc_client()
    try:
        response = client.storage_stub.GetStorageInfo(
            cloud_storage_pb2.StorageInfoRequest(session_token=session_token)
        )
        
        if response.success:
            return success_response({
                'allocated_bytes': response.allocated_bytes,
                'used_bytes': response.used_bytes,
                'available_bytes': response.available_bytes,
                'usage_percentage': response.usage_percentage
            })
        else:
            return error_response("Failed to get storage info"), 400
    except grpc.RpcError as e:
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to get storage info: {str(e)}"), 500