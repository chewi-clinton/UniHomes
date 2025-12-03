from flask import Blueprint, request, jsonify, Response, current_app
from app.utils.grpc_client import get_grpc_client
from app.models.response import success_response, error_response
import generated.cloud_storage_pb2 as cloud_storage_pb2
import grpc
import json
import subprocess
import os
import sys
import time
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# Helper function to verify admin key
def verify_admin_key(request):
    """Verify admin key from request headers or body"""
    admin_key = request.headers.get('X-Admin-Key')
    if not admin_key:
        # Try to get from request body for POST requests
        data = request.get_json(silent=True)
        if data:
            admin_key = data.get('admin_key')
    
    expected_key = current_app.config.get('ADMIN_KEY')
    if not expected_key:
        return False, "Admin key not configured"
    
    # Strip whitespace from both keys before comparing
    if admin_key and expected_key:
        admin_key = admin_key.strip()
        expected_key = expected_key.strip()
    
    if admin_key != expected_key:
        return False, "Invalid admin key"
    
    return True, "Valid"

# ============================================================================
# Admin Authentication
# ============================================================================

@admin_bp.route('/verify', methods=['POST'])
def verify_admin():
    """Verify admin key"""
    data = request.get_json()
    admin_key = data.get('admin_key')
    
    if not admin_key:
        return error_response("Admin key is required"), 400
    
    # Verify against configured admin key
    expected_key = current_app.config.get('ADMIN_KEY')
    
    if not expected_key:
        return error_response("Admin authentication not configured"), 500
    
    # Strip whitespace before comparison
    if admin_key.strip() == expected_key.strip():
        return success_response({
            'verified': True
        }, message='Admin key verified successfully')
    else:
        return error_response("Invalid admin key"), 401

# ============================================================================
# System Status & Monitoring
# ============================================================================

@admin_bp.route('/status', methods=['GET'])
def get_system_status():
    """Get system status"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    admin_key = request.headers.get('X-Admin-Key')
    client = get_grpc_client()
    
    try:
        response = client.admin_stub.GetSystemStatus(
            cloud_storage_pb2.SystemStatusRequest(admin_key=admin_key.strip())
        )
        
        if response.success:
            return success_response({
                'global_capacity_bytes': response.global_capacity_bytes,
                'global_allocated_bytes': response.global_allocated_bytes,
                'global_used_bytes': response.global_used_bytes,
                'total_users': response.total_users,
                'total_nodes': response.total_nodes,
                'online_nodes': response.online_nodes,
                'total_files': response.total_files,
                'total_chunks': response.total_chunks,
                'system_health': response.system_health
            })
        else:
            return error_response("Failed to get system status"), 400
    except grpc.RpcError as e:
        print(f"[ERROR] gRPC error in get_system_status: {e.details()}")
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        print(f"[ERROR] Exception in get_system_status: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to get system status: {str(e)}"), 500

@admin_bp.route('/events', methods=['GET'])
def stream_events():
    """Stream system events (Server-Sent Events)"""
    admin_key = request.args.get('admin_key')
    
    if not admin_key:
        return error_response("Admin key is required"), 401
    
    expected_key = current_app.config.get('ADMIN_KEY')
    
    # Strip whitespace and compare
    if not expected_key or admin_key.strip() != expected_key.strip():
        print(f"[EVENTS] Auth failed - received: '{admin_key}' expected: '{expected_key}'")
        return error_response("Invalid admin key"), 401
    
    print(f"[EVENTS] Starting SSE stream for admin")
    client = get_grpc_client()
    
    def event_stream():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'event_type': 'CONNECTED', 'message': 'Event stream connected', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            stream_request = cloud_storage_pb2.StreamEventsRequest(admin_key=admin_key.strip())
            for event in client.admin_stub.StreamSystemEvents(stream_request):
                data = {
                    'event_type': event.event_type,
                    'timestamp': event.timestamp,
                    'message': event.message,
                    'user_id': event.user_id,
                    'details': event.details
                }
                print(f"[EVENTS] Sending event: {event.event_type}")
                yield f"data: {json.dumps(data)}\n\n"
        except grpc.RpcError as e:
            print(f"[ERROR] SSE gRPC error: {e.details()}")
            yield f"data: {json.dumps({'error': e.details()})}\n\n"
        except Exception as e:
            print(f"[ERROR] SSE exception: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response

# ============================================================================
# User Management
# ============================================================================

@admin_bp.route('/users', methods=['GET'])
def list_users():
    """List all users"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    admin_key = request.headers.get('X-Admin-Key')
    client = get_grpc_client()
    
    try:
        response = client.admin_stub.ListAllUsers(
            cloud_storage_pb2.ListUsersRequest(admin_key=admin_key.strip())
        )
        
        if response.success:
            users = [{
                'user_id': u.user_id,
                'email': u.email,
                'name': u.name,
                'storage_allocated': u.storage_allocated,
                'storage_used': u.storage_used,
                'created_at': u.created_at,
                'last_login': u.last_login,
                'file_count': u.file_count
            } for u in response.users]
            
            return success_response({'users': users})
        else:
            return error_response("Failed to list users"), 400
    except grpc.RpcError as e:
        print(f"[ERROR] gRPC error in list_users: {e.details()}")
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        print(f"[ERROR] Exception in list_users: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to list users: {str(e)}"), 500

@admin_bp.route('/users/<user_id>', methods=['GET'])
def get_user_details(user_id):
    """Get detailed information about a specific user"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    admin_key = request.headers.get('X-Admin-Key')
    client = get_grpc_client()
    
    try:
        response = client.admin_stub.GetUserDetails(
            cloud_storage_pb2.UserDetailsRequest(
                admin_key=admin_key.strip(),
                user_id=user_id
            )
        )
        
        if response.success:
            user_data = {
                'user_id': response.user.user_id,
                'email': response.user.email,
                'name': response.user.name,
                'storage_allocated': response.user.storage_allocated,
                'storage_used': response.user.storage_used,
                'created_at': response.user.created_at,
                'last_login': response.user.last_login,
                'file_count': response.user.file_count
            }
            
            files = [{
                'file_id': f.file_id,
                'filename': f.filename,
                'file_size': f.file_size,
                'mime_type': f.mime_type,
                'created_at': f.created_at,
                'modified_at': f.modified_at
            } for f in response.files]
            
            return success_response({
                'user': user_data,
                'files': files
            })
        else:
            return error_response("User not found"), 404
    except grpc.RpcError as e:
        print(f"[ERROR] gRPC error in get_user_details: {e.details()}")
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        print(f"[ERROR] Exception in get_user_details: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to get user details: {str(e)}"), 500

# ============================================================================
# Node Management
# ============================================================================

@admin_bp.route('/nodes', methods=['GET'])
def list_nodes():
    """List all storage nodes"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    admin_key = request.headers.get('X-Admin-Key')
    client = get_grpc_client()
    
    try:
        print(f"[NODES] Calling ListAllNodes with admin_key")
        response = client.admin_stub.ListAllNodes(
            cloud_storage_pb2.ListNodesRequest(admin_key=admin_key.strip())
        )
        
        print(f"[NODES] Response received: success={response.success}")
        
        if response.success:
            nodes = [{
                'node_id': n.node_id,
                'host': n.host,
                'port': n.port,
                'storage_capacity': n.storage_capacity,
                'storage_used': n.storage_used,
                'status': n.status,
                'last_heartbeat': n.last_heartbeat,
                'chunk_count': n.chunk_count,
                'health_score': n.health_score
            } for n in response.nodes]
            
            print(f"[NODES] Returning {len(nodes)} nodes")
            return success_response({'nodes': nodes})
        else:
            print(f"[NODES] Failed to list nodes")
            return error_response("Failed to list nodes"), 400
    except grpc.RpcError as e:
        print(f"[ERROR] gRPC error in list_nodes: {e.details()}")
        import traceback
        traceback.print_exc()
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        print(f"[ERROR] Exception in list_nodes: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to list nodes: {str(e)}"), 500

@admin_bp.route('/nodes', methods=['POST'])
def create_node():
    """Create and start a new storage node"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    data = request.get_json()
    node_id = data.get('node_id')
    host = data.get('host')
    port = data.get('port')
    storage_gb = data.get('storage_gb')
    
    if not all([node_id, host, port, storage_gb]):
        return error_response("Missing required fields: node_id, host, port, storage_gb"), 400
    
    return success_response(message="Node management not implemented yet"), 501

@admin_bp.route('/nodes/<node_id>/start', methods=['POST'])
def start_node_endpoint(node_id):
    """Start a storage node"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    return success_response(message="Node management not implemented yet"), 501

@admin_bp.route('/nodes/<node_id>/stop', methods=['POST'])
def stop_node_endpoint(node_id):
    """Stop a storage node"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    return success_response(message="Node management not implemented yet"), 501

@admin_bp.route('/nodes/<node_id>', methods=['DELETE'])
def delete_node_endpoint(node_id):
    """Delete a storage node"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    return success_response(message="Node management not implemented yet"), 501