# app/routes/admin.py - Integrated version with full node control + all endpoints

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
import signal
import psutil
from datetime import datetime
from pathlib import Path

admin_bp = Blueprint('admin', __name__)

# PID file directory
PID_DIR = Path(os.getcwd()) / "node_pids"
PID_DIR.mkdir(exist_ok=True)

# ============================================================================
# Process Management Utilities
# ============================================================================

def get_pid_file(node_id):
    """Get PID file path for a node"""
    return PID_DIR / f"{node_id}.pid"

def write_pid_file(node_id, pid):
    """Write PID to file"""
    try:
        with open(get_pid_file(node_id), 'w') as f:
            f.write(str(pid))
        print(f"[ADMIN] Wrote PID {pid} for node {node_id}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to write PID file: {e}")
        return False

def read_pid_file(node_id):
    """Read PID from file"""
    pid_file = get_pid_file(node_id)
    if not pid_file.exists():
        return None
    try:
        with open(pid_file, 'r') as f:
            return int(f.read().strip())
    except Exception as e:
        print(f"[ERROR] Failed to read PID file: {e}")
        return None

def delete_pid_file(node_id):
    """Delete PID file"""
    pid_file = get_pid_file(node_id)
    if pid_file.exists():
        pid_file.unlink()

def is_process_running(pid):
    """Check if process is running"""
    try:
        process = psutil.Process(pid)
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def find_node_process(node_id):
    """Find running node process by scanning all processes"""
    print(f"[ADMIN] Searching for process with node_id: {node_id}")
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline:
                cmdline_str = ' '.join(cmdline)
                # Check if this is a storage_node.py process with matching node_id
                if 'storage_node.py' in cmdline_str:
                    # Extract the node_id argument from command line
                    # Command format: python storage_node.py <node_id> <host> <port> <storage_gb>
                    if node_id in cmdline:
                        print(f"[ADMIN] Found matching process - PID: {proc.info['pid']}, CMD: {cmdline_str}")
                        return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    print(f"[ADMIN] No process found for node_id: {node_id}")
    return None

def kill_process(pid):
    """Kill a process gracefully, then forcefully if needed"""
    try:
        process = psutil.Process(pid)
        print(f"[ADMIN] Terminating process {pid}...")
        process.terminate()
        
        # Wait up to 5 seconds for graceful shutdown
        try:
            process.wait(timeout=5)
            print(f"[ADMIN] Process {pid} terminated gracefully")
            return True
        except psutil.TimeoutExpired:
            print(f"[ADMIN] Process {pid} didn't stop gracefully, forcing...")
            process.kill()
            process.wait()
            print(f"[ADMIN] Process {pid} force killed")
            return True
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        print(f"[ERROR] Failed to kill process {pid}: {e}")
        return False

def verify_admin_key(request):
    """Verify admin key from request headers or body"""
    admin_key = request.headers.get('X-Admin-Key')
    if not admin_key:
        data = request.get_json(silent=True)
        if data:
            admin_key = data.get('admin_key')
    
    expected_key = current_app.config.get('ADMIN_KEY')
    if not expected_key:
        return False, "Admin key not configured"
    
    if admin_key and expected_key:
        admin_key = admin_key.strip()
        expected_key = expected_key.strip()
    
    if admin_key != expected_key:
        return False, "Invalid admin key"
    
    return True, "Valid"

# ============================================================================
# Authentication Endpoints
# ============================================================================

@admin_bp.route('/verify', methods=['POST'])
def verify_admin():
    """Verify admin key"""
    data = request.get_json()
    admin_key = data.get('admin_key')
    
    if not admin_key:
        return error_response("Admin key is required"), 400
    
    expected_key = current_app.config.get('ADMIN_KEY')
    
    if not expected_key:
        return error_response("Admin authentication not configured"), 500
    
    if admin_key.strip() == expected_key.strip():
        return success_response({
            'verified': True
        }, message='Admin key verified successfully')
    else:
        return error_response("Invalid admin key"), 401

# ============================================================================
# Node Management Endpoints - FULL CONTROL
# ============================================================================

@admin_bp.route('/nodes', methods=['POST'])
def create_node():
    """Create and register a new storage node"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    data = request.get_json()
    node_id = data.get('node_id')
    host = data.get('host', 'localhost')
    port = data.get('port')
    storage_gb = data.get('storage_gb')
    
    if not all([node_id, port, storage_gb]):
        return error_response("Missing required fields: node_id, port, storage_gb"), 400
    
    try:
        # Check if node already exists
        client = get_grpc_client()
        admin_key = request.headers.get('X-Admin-Key')
        
        response = client.admin_stub.ListAllNodes(
            cloud_storage_pb2.ListNodesRequest(admin_key=admin_key.strip())
        )
        
        if response.success:
            existing_node = next((n for n in response.nodes if n.node_id == node_id), None)
            if existing_node:
                return error_response(f"Node {node_id} already exists"), 400
        
        # Create node directory
        node_storage_dir = os.path.join(os.getcwd(), f'node_storage_{node_id}')
        os.makedirs(node_storage_dir, exist_ok=True)
        
        print(f"[ADMIN] Created node {node_id} - ready to start")
        
        return success_response({
            'node_id': node_id,
            'host': host,
            'port': port,
            'storage_gb': storage_gb,
            'storage_dir': node_storage_dir,
            'status': 'created'
        }, message=f"Node {node_id} created successfully. Click Start to launch it.")
    
    except Exception as e:
        print(f"[ERROR] Failed to create node: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to create node: {str(e)}"), 400

@admin_bp.route('/nodes/<node_id>/start', methods=['POST'])
def start_node(node_id):
    """Start a storage node - WORKS FOR ANY NODE"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    data = request.get_json()
    host = data.get('host', 'localhost')
    port = data.get('port')
    storage_gb = data.get('storage_gb')
    
    if not all([port, storage_gb]):
        return error_response("Missing required fields: port, storage_gb"), 400
    
    try:
        # Check if node is already running
        existing_pid = read_pid_file(node_id)
        if existing_pid and is_process_running(existing_pid):
            return error_response(f"Node {node_id} is already running (PID: {existing_pid})"), 400
        
        # Try to find if process is running without PID file
        running_pid = find_node_process(node_id)
        if running_pid:
            write_pid_file(node_id, running_pid)
            return error_response(f"Node {node_id} is already running (PID: {running_pid}, recovered)"), 400
        
        # Find the storage_node.py file
        # Get the project root (assuming admin.py is in app/routes/)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Try multiple possible locations
        possible_paths = [
            os.path.join(project_root, 'node', 'storage_node.py'),
            os.path.join(project_root, 'backend', 'clients', 'storage_node.py'),
            os.path.join(project_root, 'clients', 'storage_node.py'),
        ]
        
        node_script = None
        for path in possible_paths:
            if os.path.exists(path):
                node_script = path
                print(f"[ADMIN] Found storage_node.py at: {path}")
                break
        
        if not node_script:
            return error_response(f"Storage node script not found. Tried: {possible_paths}"), 500
        
        # Start the node process
        print(f"[ADMIN] Starting node {node_id} on {host}:{port}")
        
        process = subprocess.Popen(
            [sys.executable, node_script, node_id, host, str(port), str(storage_gb)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=project_root
        )
        
        # Write PID file
        write_pid_file(node_id, process.pid)
        
        # Wait a moment to check if it started successfully
        time.sleep(2)
        
        if not is_process_running(process.pid):
            delete_pid_file(node_id)
            stdout, stderr = process.communicate()
            error_msg = stderr.decode() if stderr else stdout.decode()
            return error_response(f"Node failed to start: {error_msg}"), 500
        
        print(f"[ADMIN] Node {node_id} started successfully (PID: {process.pid})")
        
        return success_response({
            'node_id': node_id,
            'pid': process.pid,
            'status': 'started'
        }, message=f"Node {node_id} started successfully")
    
    except Exception as e:
        print(f"[ERROR] Failed to start node: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to start node: {str(e)}"), 500

@admin_bp.route('/nodes/<node_id>/stop', methods=['POST'])
def stop_node(node_id):
    """Stop a running storage node - WORKS FOR ANY NODE"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    try:
        print(f"[ADMIN] Attempting to stop node {node_id}")
        
        # Try to get PID from file first
        pid = read_pid_file(node_id)
        print(f"[ADMIN] PID from file: {pid}")
        
        # If no PID file, try to find the process by scanning
        if not pid:
            print(f"[ADMIN] No PID file found, scanning for process...")
            pid = find_node_process(node_id)
            if pid:
                print(f"[ADMIN] Found node {node_id} running without PID file (PID: {pid})")
                write_pid_file(node_id, pid)
            else:
                print(f"[ADMIN] No running process found for node {node_id}")
        
        if not pid:
            # Double check by listing all storage_node.py processes
            print(f"[ADMIN] Listing all storage_node.py processes:")
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and 'storage_node.py' in ' '.join(cmdline):
                        print(f"  - PID {proc.info['pid']}: {' '.join(cmdline)}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return error_response(f"Node {node_id} is not running (no process found)"), 400
        
        # Check if process is actually running
        if not is_process_running(pid):
            print(f"[ADMIN] Process {pid} is not running, cleaning up PID file")
            delete_pid_file(node_id)
            return error_response(f"Node {node_id} process not found (stale PID: {pid})"), 400
        
        print(f"[ADMIN] Stopping node {node_id} (PID: {pid})")
        
        # Kill the process
        if kill_process(pid):
            delete_pid_file(node_id)
            print(f"[ADMIN] Node {node_id} stopped successfully")
            return success_response({
                'node_id': node_id,
                'pid': pid,
                'status': 'stopped'
            }, message=f"Node {node_id} stopped successfully (PID: {pid})")
        else:
            return error_response(f"Failed to stop node {node_id} (PID: {pid})"), 500
    
    except Exception as e:
        print(f"[ERROR] Failed to stop node: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to stop node: {str(e)}"), 500

@admin_bp.route('/nodes/<node_id>', methods=['DELETE'])
def delete_node(node_id):
    """Delete a storage node completely - WORKS FOR ANY NODE"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    try:
        # First, stop the node if it's running
        pid = read_pid_file(node_id)
        if not pid:
            pid = find_node_process(node_id)
        
        if pid and is_process_running(pid):
            print(f"[ADMIN] Stopping running node {node_id} before deletion (PID: {pid})")
            kill_process(pid)
            delete_pid_file(node_id)
        
        # Delete node from database
        from db.database import get_db_session
        from db.models import StorageNode, Chunk
        
        with get_db_session() as session:
            node = session.query(StorageNode).filter_by(node_id=node_id).first()
            
            if not node:
                return error_response(f"Node {node_id} not found in database"), 404
            
            # Check if node has chunks
            chunk_count = session.query(Chunk).filter_by(primary_node_id=node_id).count()
            
            if chunk_count > 0:
                return error_response(
                    f"Cannot delete node {node_id}: it contains {chunk_count} chunks. "
                    "Data must be migrated first."
                ), 400
            
            # Delete the node
            session.delete(node)
            session.commit()
        
        # Delete node storage directory
        node_storage_dir = os.path.join(os.getcwd(), f'node_storage_{node_id}')
        if os.path.exists(node_storage_dir):
            import shutil
            shutil.rmtree(node_storage_dir)
            print(f"[ADMIN] Deleted storage directory: {node_storage_dir}")
        
        print(f"[ADMIN] Node {node_id} deleted successfully")
        
        return success_response({
            'node_id': node_id,
            'status': 'deleted'
        }, message=f"Node {node_id} deleted successfully")
    
    except Exception as e:
        print(f"[ERROR] Failed to delete node: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to delete node: {str(e)}"), 500

@admin_bp.route('/nodes/running', methods=['GET'])
def get_running_nodes():
    """Get list of currently running nodes (by scanning processes)"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    try:
        running = []
        
        # Scan all PID files
        for pid_file in PID_DIR.glob("*.pid"):
            node_id = pid_file.stem
            pid = read_pid_file(node_id)
            
            if pid:
                if is_process_running(pid):
                    running.append({
                        'node_id': node_id,
                        'pid': pid,
                        'status': 'running'
                    })
                else:
                    # Clean up stale PID file
                    delete_pid_file(node_id)
        
        return success_response({
            'running_nodes': running,
            'count': len(running)
        })
    
    except Exception as e:
        print(f"[ERROR] Failed to get running nodes: {e}")
        return error_response(f"Failed to get running nodes: {str(e)}"), 500

@admin_bp.route('/nodes', methods=['GET'])
def list_nodes():
    """List all storage nodes"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    admin_key = request.headers.get('X-Admin-Key')
    client = get_grpc_client()
    
    try:
        response = client.admin_stub.ListAllNodes(
            cloud_storage_pb2.ListNodesRequest(admin_key=admin_key.strip())
        )
        
        if response.success:
            nodes = []
            for n in response.nodes:
                # Check if node is actually running
                pid = read_pid_file(n.node_id)
                is_running = pid and is_process_running(pid)
                
                nodes.append({
                    'node_id': n.node_id,
                    'host': n.host,
                    'port': n.port,
                    'storage_capacity': n.storage_capacity,
                    'storage_used': n.storage_used,
                    'status': n.status,
                    'last_heartbeat': n.last_heartbeat,
                    'chunk_count': n.chunk_count,
                    'health_score': n.health_score,
                    'process_running': is_running,
                    'pid': pid if is_running else None
                })
            
            return success_response({'nodes': nodes})
        else:
            return error_response("Failed to list nodes"), 400
    except Exception as e:
        print(f"[ERROR] Exception in list_nodes: {str(e)}")
        return error_response(f"Failed to list nodes: {str(e)}"), 500

# ============================================================================
# System Status Endpoints
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
    
    if not expected_key or admin_key.strip() != expected_key.strip():
        return error_response("Invalid admin key"), 401
    
    client = get_grpc_client()
    
    def event_stream():
        try:
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
                yield f"data: {json.dumps(data)}\n\n"
        except Exception as e:
            print(f"[ERROR] SSE exception: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response

# ============================================================================
# User Management Endpoints
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
    except Exception as e:
        print(f"[ERROR] Exception in list_users: {str(e)}")
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
    except Exception as e:
        print(f"[ERROR] Exception in get_user_details: {str(e)}")
        return error_response(f"Failed to get user details: {str(e)}"), 500