from flask import Blueprint, request, jsonify, Response
from app.utils.grpc_client import get_grpc_client
from app.models.response import success_response, error_response
import generated.cloud_storage_pb2 as cloud_storage_pb2
import grpc
import json
import subprocess
import os
import sys
import time

admin_bp = Blueprint('admin', __name__)

# Node management functions
def start_node(node_id, host, port, storage_gb):
    """Start a storage node as a subprocess"""
    try:
        # Path to storage_node.py
        storage_node_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'storage_node.py'
        )
        
        # Start the node as a subprocess
        cmd = [
            sys.executable, 
            storage_node_path,
            node_id, host, str(port), str(storage_gb)
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit to see if it starts successfully
        time.sleep(2)
        
        if process.poll() is None:
            return True, f"Node {node_id} started successfully"
        else:
            _, stderr = process.communicate()
            return False, f"Failed to start node: {stderr.decode('utf-8')}"
    except Exception as e:
        return False, f"Error starting node: {str(e)}"

def stop_node(node_id):
    """Stop a storage node by finding and killing its process"""
    try:
        # Find the process by node_id
        cmd = f"ps aux | grep 'storage_node.py {node_id}' | grep -v grep | awk '{{print $2}}'"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pid, _ = process.communicate()
        
        if pid:
            # Kill the process
            os.kill(int(pid.strip()), 15)  # SIGTERM
            return True, f"Node {node_id} stopped successfully"
        else:
            return False, f"Node {node_id} not found"
    except Exception as e:
        return False, f"Error stopping node: {str(e)}"

def delete_node(node_id):
    """Delete a node from the database"""
    try:
        # Connect to the database directly
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        db_url = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'postgres')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'cloud_storage')}"
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Import the model
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from db.models import StorageNode
        
        # Find and delete the node
        node = session.query(StorageNode).filter_by(node_id=node_id).first()
        if node:
            session.delete(node)
            session.commit()
            session.close()
            return True, f"Node {node_id} deleted from database"
        else:
            session.close()
            return False, f"Node {node_id} not found in database"
    except Exception as e:
        return False, f"Error deleting node: {str(e)}"

@admin_bp.route('/status', methods=['GET'])
def get_system_status():
    admin_key = request.headers.get('X-Admin-Key')
    if admin_key != request.app.config['ADMIN_KEY']:
        return error_response("Invalid admin key"), 401
    
    client = get_grpc_client()
    try:
        response = client.admin_stub.GetSystemStatus(
            cloud_storage_pb2.SystemStatusRequest(admin_key=admin_key)
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
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to get system status: {str(e)}"), 500

@admin_bp.route('/users', methods=['GET'])
def list_users():
    admin_key = request.headers.get('X-Admin-Key')
    if admin_key != request.app.config['ADMIN_KEY']:
        return error_response("Invalid admin key"), 401
    
    client = get_grpc_client()
    try:
        response = client.admin_stub.ListAllUsers(
            cloud_storage_pb2.ListUsersRequest(admin_key=admin_key)
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
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to list users: {str(e)}"), 500

@admin_bp.route('/nodes', methods=['GET'])
def list_nodes():
    admin_key = request.headers.get('X-Admin-Key')
    if admin_key != request.app.config['ADMIN_KEY']:
        return error_response("Invalid admin key"), 401
    
    client = get_grpc_client()
    try:
        response = client.admin_stub.ListAllNodes(
            cloud_storage_pb2.ListNodesRequest(admin_key=admin_key)
        )
        
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
            
            return success_response({'nodes': nodes})
        else:
            return error_response("Failed to list nodes"), 400
    except grpc.RpcError as e:
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to list nodes: {str(e)}"), 500

@admin_bp.route('/events', methods=['GET'])
def stream_events():
    admin_key = request.args.get('admin_key')
    if admin_key != request.app.config['ADMIN_KEY']:
        return error_response("Invalid admin key"), 401
    
    client = get_grpc_client()
    
    def event_stream():
        try:
            request = cloud_storage_pb2.StreamEventsRequest(admin_key=admin_key)
            for event in client.admin_stub.StreamSystemEvents(request):
                data = {
                    'event_type': event.event_type,
                    'timestamp': event.timestamp,
                    'message': event.message,
                    'user_id': event.user_id,
                    'details': event.details
                }
                yield f"data: {json.dumps(data)}\n\n"
        except grpc.RpcError as e:
            yield f"data: {json.dumps({'error': e.details()})}\n\n"
    
    return Response(event_stream(), mimetype="text/event-stream")

# Node management endpoints
@admin_bp.route('/nodes', methods=['POST'])
def create_node():
    admin_key = request.headers.get('X-Admin-Key')
    if admin_key != request.app.config['ADMIN_KEY']:
        return error_response("Invalid admin key"), 401
    
    data = request.get_json()
    node_id = data.get('node_id')
    host = data.get('host')
    port = data.get('port')
    storage_gb = data.get('storage_gb')
    
    if not all([node_id, host, port, storage_gb]):
        return error_response("Missing required fields"), 400
    
    # Start the node
    success, message = start_node(node_id, host, port, storage_gb)
    if not success:
        return error_response(message), 500
    
    return success_response(message=message)

@admin_bp.route('/nodes/<node_id>/start', methods=['POST'])
def start_node_endpoint(node_id):
    admin_key = request.headers.get('X-Admin-Key')
    if admin_key != request.app.config['ADMIN_KEY']:
        return error_response("Invalid admin key"), 401
    
    data = request.get_json()
    host = data.get('host')
    port = data.get('port')
    storage_gb = data.get('storage_gb')
    
    if not all([host, port, storage_gb]):
        return error_response("Missing required fields"), 400
    
    # Start the node
    success, message = start_node(node_id, host, port, storage_gb)
    if not success:
        return error_response(message), 500
    
    return success_response(message=message)

@admin_bp.route('/nodes/<node_id>/stop', methods=['POST'])
def stop_node_endpoint(node_id):
    admin_key = request.headers.get('X-Admin-Key')
    if admin_key != request.app.config['ADMIN_KEY']:
        return error_response("Invalid admin key"), 401
    
    # Stop the node
    success, message = stop_node(node_id)
    if not success:
        return error_response(message), 500
    
    return success_response(message=message)

@admin_bp.route('/nodes/<node_id>', methods=['DELETE'])
def delete_node_endpoint(node_id):
    admin_key = request.headers.get('X-Admin-Key')
    if admin_key != request.app.config['ADMIN_KEY']:
        return error_response("Invalid admin key"), 401
    
    # Stop the node first
    stop_node(node_id)
    
    # Delete from database
    success, message = delete_node(node_id)
    if not success:
        return error_response(message), 500
    
    return success_response(message=message)