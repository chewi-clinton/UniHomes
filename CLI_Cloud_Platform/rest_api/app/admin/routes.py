# app/routes/admin.py - COMPLETE SOLUTION WITH CAPACITY TRACKING

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
from datetime import datetime, timedelta
from pathlib import Path

admin_bp = Blueprint('admin', __name__)

def get_project_root():
    """Get the project root directory"""
    cwd = Path(os.getcwd())
    if cwd.name == 'rest_api':
        return cwd.parent
    return cwd

PID_DIR = get_project_root() / "node_pids"
PID_DIR.mkdir(exist_ok=True)
print(f"[ADMIN] PID directory: {PID_DIR}")

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
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline:
                cmdline_str = ' '.join(cmdline)
                if 'storage_node.py' in cmdline_str and node_id in cmdline:
                    return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def kill_process(pid):
    """Kill a process gracefully, then forcefully if needed"""
    try:
        process = psutil.Process(pid)
        process.terminate()
        try:
            process.wait(timeout=5)
            return True
        except psutil.TimeoutExpired:
            process.kill()
            process.wait()
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
# Capacity Calculation Utilities
# ============================================================================

def calculate_capacity_metrics():
    """
    Calculate storage capacity metrics:
    - total_capacity: Sum of ALL nodes (including offline)
    - usable_capacity: Sum of ONLINE nodes only
    - used_capacity: Sum of storage_used from all nodes
    """
    from db.database import get_db_session
    from db.models import StorageNode
    
    try:
        with get_db_session() as session:
            nodes = session.query(StorageNode).all()
            
            if not nodes:
                return {
                    'total_capacity': 0,
                    'usable_capacity': 0,
                    'used_capacity': 0,
                    'total_nodes': 0,
                    'online_nodes': 0,
                    'offline_nodes': 0
                }
            
            # Calculate total capacity (all nodes)
            total_capacity = sum(node.storage_capacity for node in nodes)
            used_capacity = sum(node.storage_used for node in nodes)
            
            # Determine which nodes are online
            online_threshold = datetime.utcnow() - timedelta(minutes=2)
            online_nodes = []
            offline_nodes = []
            
            for node in nodes:
                is_online = (
                    node.last_heartbeat and 
                    node.last_heartbeat > online_threshold
                )
                if is_online:
                    online_nodes.append(node)
                else:
                    offline_nodes.append(node)
            
            # Calculate usable capacity (online nodes only)
            usable_capacity = sum(node.storage_capacity for node in online_nodes)
            
            return {
                'total_capacity': total_capacity,
                'usable_capacity': usable_capacity,
                'used_capacity': used_capacity,
                'total_nodes': len(nodes),
                'online_nodes': len(online_nodes),
                'offline_nodes': len(offline_nodes)
            }
    
    except Exception as e:
        print(f"[ERROR] Failed to calculate capacity: {e}")
        return {
            'total_capacity': 0,
            'usable_capacity': 0,
            'used_capacity': 0,
            'total_nodes': 0,
            'online_nodes': 0,
            'offline_nodes': 0
        }

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
        from db.database import get_db_session
        from db.models import StorageNode
        
        with get_db_session() as session:
            existing_node = session.query(StorageNode).filter_by(node_id=node_id).first()
            if existing_node:
                return error_response(f"Node {node_id} already exists"), 400
        
        # Create node directory
        cwd = Path(os.getcwd())
        if cwd.name == 'rest_api':
            project_root = cwd.parent
        else:
            project_root = cwd
        
        node_storage_dir = project_root / f'node_storage_{node_id}'
        node_storage_dir.mkdir(exist_ok=True)
        
        storage_capacity = int(storage_gb * 1024**3)
        
        # Register node in database
        with get_db_session() as session:
            new_node = StorageNode(
                node_id=node_id,
                host=host,
                port=port,
                storage_capacity=storage_capacity,
                storage_used=0,
                cpu_cores=4,
                status='offline',
                health_score=100.0,
                last_heartbeat=None
            )
            session.add(new_node)
            session.commit()
        
        # Calculate new capacities
        metrics = calculate_capacity_metrics()
        
        print(f"[ADMIN] ✓ Node {node_id} created and registered")
        print(f"[ADMIN] Total Capacity: {metrics['total_capacity'] / (1024**3):.2f} GB")
        print(f"[ADMIN] Usable Capacity: {metrics['usable_capacity'] / (1024**3):.2f} GB")
        
        return success_response({
            'node_id': node_id,
            'host': host,
            'port': port,
            'storage_gb': storage_gb,
            'storage_dir': str(node_storage_dir),
            'status': 'created',
            'capacity_impact': {
                'total_capacity': metrics['total_capacity'],
                'usable_capacity': metrics['usable_capacity']
            }
        }, message=f"Node {node_id} created successfully. Click Start to launch it.")
    
    except Exception as e:
        print(f"[ERROR] Failed to create node: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to create node: {str(e)}"), 400

@admin_bp.route('/nodes/<node_id>/start', methods=['POST'])
def start_node(node_id):
    """Start a storage node - FIXED with better process detection"""
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
        # IMPROVED: Better process detection
        existing_pid = read_pid_file(node_id)
        
        # First check PID file
        if existing_pid:
            if is_process_running(existing_pid):
                # Process is actually running
                print(f"[ADMIN] Node {node_id} already running with PID {existing_pid}")
                return error_response(
                    f"Node {node_id} is already running (PID: {existing_pid}). "
                    f"Stop it first or use the admin panel to force kill."
                ), 400
            else:
                # PID file exists but process is dead - clean it up
                print(f"[ADMIN] Cleaning up stale PID file for {node_id}")
                delete_pid_file(node_id)
        
        # Double check by scanning all processes
        running_pid = find_node_process(node_id)
        if running_pid:
            print(f"[ADMIN] Found running process for {node_id}: PID {running_pid}")
            write_pid_file(node_id, running_pid)
            return error_response(
                f"Node {node_id} is already running (PID: {running_pid}). "
                f"Stop it first before starting again."
            ), 400
        
        # At this point, we're sure the node is NOT running
        print(f"[ADMIN] Starting node {node_id}...")
        
        cwd = Path(os.getcwd())
        if cwd.name == 'rest_api':
            project_root = cwd.parent
        else:
            project_root = cwd
        
        possible_paths = [
            project_root / 'node' / 'storage_node.py',
            project_root / 'backend' / 'node' / 'storage_node.py',
            project_root / 'clients' / 'storage_node.py',
        ]
        
        node_script = None
        for path in possible_paths:
            if path.exists():
                node_script = str(path.absolute())
                print(f"[ADMIN] Found node script: {node_script}")
                break
        
        if not node_script:
            return error_response("Storage node script not found"), 500
        
        cmd = [sys.executable, node_script, node_id, host, str(port), str(storage_gb)]
        print(f"[ADMIN] Executing: {' '.join(cmd)}")
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(project_root),
            start_new_session=True  # Important: detach from parent
        )
        
        # Write PID immediately
        write_pid_file(node_id, process.pid)
        print(f"[ADMIN] Process started with PID: {process.pid}")
        
        # Wait a bit to ensure it started properly
        time.sleep(3)
        
        # Verify it's still running
        if not is_process_running(process.pid):
            delete_pid_file(node_id)
            # Try to get error output
            try:
                _, stderr = process.communicate(timeout=1)
                error_msg = stderr.decode() if stderr else "Unknown error"
            except:
                error_msg = "Process died immediately after start"
            
            print(f"[ADMIN] ✗ Node failed to start: {error_msg}")
            return error_response(f"Node failed to start: {error_msg}"), 500
        
        print(f"[ADMIN] ✓ Node {node_id} started successfully (PID: {process.pid})")
        
        return success_response({
            'node_id': node_id,
            'pid': process.pid,
            'status': 'started',
            'message': f'Node {node_id} is starting. It will appear online after sending heartbeat.'
        }, message=f"Node {node_id} started successfully")
    
    except Exception as e:
        print(f"[ERROR] Failed to start node: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to start node: {str(e)}"), 500


@admin_bp.route('/nodes/<node_id>/stop', methods=['POST'])
def stop_node(node_id):
    """Stop a running storage node - IMPROVED"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    try:
        print(f"[ADMIN] Attempting to stop node {node_id}")
        
        # Try to get PID from file first
        pid = read_pid_file(node_id)
        
        # If no PID file, scan for running process
        if not pid:
            print(f"[ADMIN] No PID file found, scanning for process...")
            pid = find_node_process(node_id)
            if pid:
                print(f"[ADMIN] Found running process: PID {pid}")
                write_pid_file(node_id, pid)
        
        if not pid:
            print(f"[ADMIN] ✗ No process found for node {node_id}")
            # Clean up just in case
            delete_pid_file(node_id)
            return error_response(
                f"Node {node_id} is not running. No process found."
            ), 400
        
        # Verify process is actually running
        if not is_process_running(pid):
            print(f"[ADMIN] Process {pid} is not running (stale PID)")
            delete_pid_file(node_id)
            return error_response(
                f"Node {node_id} process is not running (stale PID: {pid})"
            ), 400
        
        print(f"[ADMIN] Stopping process {pid}...")
        
        # Kill the process
        if kill_process(pid):
            delete_pid_file(node_id)
            
            # Recalculate capacity
            metrics = calculate_capacity_metrics()
            
            print(f"[ADMIN] ✓ Node {node_id} stopped successfully")
            print(f"[ADMIN] Usable Capacity: {metrics['usable_capacity'] / (1024**3):.2f} GB")
            
            return success_response({
                'node_id': node_id,
                'pid': pid,
                'status': 'stopped',
                'capacity_impact': {
                    'total_capacity': metrics['total_capacity'],
                    'usable_capacity': metrics['usable_capacity']
                }
            }, message=f"Node {node_id} stopped successfully")
        else:
            return error_response(f"Failed to kill process {pid}"), 500
    
    except Exception as e:
        print(f"[ERROR] Failed to stop node: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to stop node: {str(e)}"), 500


# ADD THIS NEW ENDPOINT - Force Kill
@admin_bp.route('/nodes/<node_id>/force-kill', methods=['POST'])
def force_kill_node(node_id):
    """Force kill a node process - for when normal stop doesn't work"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    try:
        print(f"[ADMIN] FORCE KILL requested for node {node_id}")
        
        # Get PID from file
        pid = read_pid_file(node_id)
        
        # Also scan for process
        scanned_pid = find_node_process(node_id)
        
        killed_pids = []
        
        # Try to kill both if found
        if pid and is_process_running(pid):
            print(f"[ADMIN] Force killing PID from file: {pid}")
            try:
                process = psutil.Process(pid)
                process.kill()  # SIGKILL - immediate termination
                process.wait(timeout=5)
                killed_pids.append(pid)
            except:
                pass
        
        if scanned_pid and scanned_pid != pid and is_process_running(scanned_pid):
            print(f"[ADMIN] Force killing scanned PID: {scanned_pid}")
            try:
                process = psutil.Process(scanned_pid)
                process.kill()
                process.wait(timeout=5)
                killed_pids.append(scanned_pid)
            except:
                pass
        
        # Clean up PID file
        delete_pid_file(node_id)
        
        if killed_pids:
            print(f"[ADMIN] ✓ Force killed PIDs: {killed_pids}")
            return success_response({
                'node_id': node_id,
                'killed_pids': killed_pids,
                'status': 'force_killed'
            }, message=f"Node {node_id} force killed successfully")
        else:
            return error_response(f"No running process found for node {node_id}"), 400
    
    except Exception as e:
        print(f"[ERROR] Force kill failed: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Force kill failed: {str(e)}"), 500
@admin_bp.route('/nodes/<node_id>', methods=['DELETE'])
def delete_node(node_id):
    """
    Delete a storage node - SAFE WITH FORCE OPTION
    Query param: force=true to delete even with chunks (data loss)
    """
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    force = request.args.get('force', 'false').lower() == 'true'
    
    try:
        from db.database import get_db_session
        from db.models import StorageNode, Chunk
        
        # Stop node if running
        pid = read_pid_file(node_id)
        if not pid:
            pid = find_node_process(node_id)
        
        if pid and is_process_running(pid):
            print(f"[ADMIN] Stopping running node {node_id} before deletion")
            kill_process(pid)
            delete_pid_file(node_id)
            time.sleep(1)  # Wait for process to die
        
        with get_db_session() as session:
            node = session.query(StorageNode).filter_by(node_id=node_id).first()
            
            if not node:
                return error_response(f"Node {node_id} not found"), 404
            
            # Check for chunks
            chunks = session.query(Chunk).filter_by(primary_node_id=node_id).all()
            chunk_count = len(chunks)
            
            if chunk_count > 0 and not force:
                # Get affected files for better error message
                from db.models import File
                affected_files = []
                for chunk in chunks[:5]:  # Show up to 5 files
                    file = session.query(File).filter_by(file_id=chunk.file_id).first()
                    if file:
                        affected_files.append(file.filename)
                
                error_msg = (
                    f"Cannot delete node {node_id}: it contains {chunk_count} chunks.\n\n"
                    f"Affected files (showing up to 5):\n" + 
                    "\n".join(f"  - {f}" for f in affected_files) +
                    f"\n\nOptions:\n"
                    f"1. Migrate data to other nodes first (recommended)\n"
                    f"2. Use force=true to delete anyway (WARNING: DATA LOSS)"
                )
                
                return error_response(error_msg), 400
            
            # Store capacity before deletion
            node_capacity = node.storage_capacity
            
            if force and chunk_count > 0:
                print(f"[ADMIN] ⚠️  FORCE DELETE: Removing {chunk_count} chunks from node {node_id}")
                
                # Delete all chunks from this node
                for chunk in chunks:
                    session.delete(chunk)
                    print(f"[ADMIN] Deleted chunk {chunk.chunk_id}")
            
            # Delete node from database
            session.delete(node)
            session.commit()
            
            print(f"[ADMIN] ✓ Node {node_id} deleted from database")
        
        # Delete node storage directory
        node_storage_dir = get_project_root() / f'node_storage_{node_id}'
        if node_storage_dir.exists():
            import shutil
            shutil.rmtree(node_storage_dir)
            print(f"[ADMIN] ✓ Deleted storage directory: {node_storage_dir}")
        
        # Recalculate capacities
        metrics = calculate_capacity_metrics()
        
        print(f"[ADMIN] ✓ Total Capacity reduced to: {metrics['total_capacity'] / (1024**3):.2f} GB")
        print(f"[ADMIN] ✓ Usable Capacity: {metrics['usable_capacity'] / (1024**3):.2f} GB")
        
        return success_response({
            'node_id': node_id,
            'status': 'deleted',
            'chunks_deleted': chunk_count if force else 0,
            'capacity_freed': node_capacity,
            'capacity_impact': {
                'total_capacity': metrics['total_capacity'],
                'usable_capacity': metrics['usable_capacity']
            }
        }, message=f"Node {node_id} deleted successfully" + (f" ({chunk_count} chunks removed)" if force and chunk_count > 0 else ""))
    
    except Exception as e:
        print(f"[ERROR] Failed to delete node: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to delete node: {str(e)}"), 500

@admin_bp.route('/nodes/capacity', methods=['GET'])
def get_capacity_metrics():
    """Get detailed capacity metrics"""
    is_valid, message = verify_admin_key(request)
    if not is_valid:
        return error_response(message), 401
    
    try:
        metrics = calculate_capacity_metrics()
        
        return success_response({
            'total_capacity_bytes': metrics['total_capacity'],
            'total_capacity_gb': metrics['total_capacity'] / (1024**3),
            'usable_capacity_bytes': metrics['usable_capacity'],
            'usable_capacity_gb': metrics['usable_capacity'] / (1024**3),
            'used_capacity_bytes': metrics['used_capacity'],
            'used_capacity_gb': metrics['used_capacity'] / (1024**3),
            'total_nodes': metrics['total_nodes'],
            'online_nodes': metrics['online_nodes'],
            'offline_nodes': metrics['offline_nodes'],
            'usage_percentage': (
                (metrics['used_capacity'] / metrics['usable_capacity'] * 100)
                if metrics['usable_capacity'] > 0 else 0
            )
        })
    
    except Exception as e:
        print(f"[ERROR] Failed to get capacity metrics: {e}")
        return error_response(f"Failed to get capacity metrics: {str(e)}"), 500

@admin_bp.route('/nodes', methods=['GET'])
def list_nodes():
    """List all storage nodes with capacity info"""
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
            
            # Add capacity metrics
            metrics = calculate_capacity_metrics()
            
            return success_response({
                'nodes': nodes,
                'capacity_metrics': {
                    'total_capacity': metrics['total_capacity'],
                    'usable_capacity': metrics['usable_capacity'],
                    'used_capacity': metrics['used_capacity'],
                    'online_nodes': metrics['online_nodes'],
                    'offline_nodes': metrics['offline_nodes']
                }
            })
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
    """Get system status with capacity metrics"""
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
            # Add our capacity metrics
            metrics = calculate_capacity_metrics()
            
            return success_response({
                'global_capacity_bytes': metrics['total_capacity'],
                'usable_capacity_bytes': metrics['usable_capacity'],
                'global_used_bytes': response.global_used_bytes,
                'total_users': response.total_users,
                'total_nodes': response.total_nodes,
                'online_nodes': response.online_nodes,
                'offline_nodes': metrics['offline_nodes'],
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
    """Stream system events"""
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