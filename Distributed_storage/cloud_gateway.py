#!/usr/bin/env python3
"""
Cloud Gateway - Main server for distributed cloud storage system
Handles node registration, file uploads, and chunk distribution
"""

import socket
import threading
import json
import os
import time
import hashlib
import pickle
from datetime import datetime, timedelta
import struct
import uuid

class CloudGateway:
    def __init__(self, host='localhost', upload_port=8000, node_port=8001):
        self.host = host
        self.upload_port = upload_port
        self.node_port = node_port
        self.nodes = {}  # node_id: node_info
        self.files = {}  # file_id: file_info
        self.chunks = {}  # chunk_id: chunk_info
        self.running = True
        self.db_file = 'cloud_db.pkl'
        self.load_database()
        
        # Thread-safe locks
        self.nodes_lock = threading.Lock()
        self.files_lock = threading.Lock()
        self.chunks_lock = threading.Lock()
        
    def load_database(self):
        """Load persistent database from disk"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'rb') as f:
                    data = pickle.load(f)
                    self.nodes = data.get('nodes', {})
                    self.files = data.get('files', {})
                    self.chunks = data.get('chunks', {})
        except Exception as e:
            print(f"Database load error: {e}")
    
    def save_database(self):
        """Save database to disk"""
        try:
            with open(self.db_file, 'wb') as f:
                data = {
                    'nodes': self.nodes,
                    'files': self.files,
                    'chunks': self.chunks
                }
                pickle.dump(data, f)
        except Exception as e:
            print(f"Database save error: {e}")
    
    def get_total_storage(self):
        """Get total available storage across all online nodes"""
        total = 0
        with self.nodes_lock:
            for node_id, node_info in self.nodes.items():
                if node_info.get('status') == 'online':
                    total += node_info.get('storage_capacity', 0)
        return total
    
    def get_online_nodes(self):
        """Get count of online nodes"""
        count = 0
        with self.nodes_lock:
            for node_info in self.nodes.values():
                if node_info.get('status') == 'online':
                    count += 1
        return count
    
    def display_status(self):
        """Display current system status"""
        while self.running:
            os.system('clear' if os.name == 'posix' else 'cls')
            print("=" * 60)
            print("        DISTRIBUTED CLOUD STORAGE - CLOUD GATEWAY")
            print("=" * 60)
            print(f"Gateway Address: {self.host}:{self.upload_port} (uploads) | {self.host}:{self.node_port} (nodes)")
            print(f"Status: {'RUNNING' if self.running else 'STOPPED'}")
            print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            print("STORAGE OVERVIEW:")
            total_storage = self.get_total_storage()
            online_nodes = self.get_online_nodes()
            print(f"  Total Storage: {total_storage / (1024**3):.2f} GB")
            print(f"  Online Nodes: {online_nodes}")
            print(f"  Files Stored: {len(self.files)}")
            print(f"  Total Chunks: {len(self.chunks)}")
            print()
            
            print("CONNECTED NODES:")
            with self.nodes_lock:
                for node_id, node_info in self.nodes.items():
                    status = node_info.get('status', 'unknown')
                    host = node_info.get('host', 'unknown')
                    port = node_info.get('port', 'unknown')
                    storage = node_info.get('storage_capacity', 0)
                    last_heartbeat = node_info.get('last_heartbeat', 0)
                    
                    # Check if node is alive (heartbeat within last 60 seconds)
                    is_alive = (time.time() - last_heartbeat) < 60 if last_heartbeat else False
                    status_indicator = "🟢" if status == 'online' and is_alive else "🔴"
                    
                    print(f"  {status_indicator} {node_id}")
                    print(f"    Address: {host}:{port}")
                    print(f"    Storage: {storage / (1024**3):.2f} GB")
                    print(f"    Status: {status}")
                    if last_heartbeat:
                        print(f"    Last Heartbeat: {int(time.time() - last_heartbeat)}s ago")
                    print()
            
            print("RECENT ACTIVITY:")
            print("  Listening for new nodes and upload requests...")
            print()
            
            print("Commands: Ctrl+C to stop")
            print("=" * 60)
            
            time.sleep(5)  # Update every 5 seconds
    
    def handle_node_registration(self, conn, addr):
        """Handle node registration and heartbeat messages"""
        try:
            data = self.recv_message(conn)
            if not data:
                return
            
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get('type')
            
            if msg_type == 'register':
                # New node registration
                node_id = message.get('node_id')
                node_info = {
                    'node_id': node_id,
                    'host': message.get('host'),
                    'port': message.get('port'),
                    'storage_capacity': message.get('storage_capacity', 0),
                    'cpu_cores': message.get('cpu_cores', 1),
                    'bandwidth': message.get('bandwidth', '1Gbps'),
                    'status': 'online',
                    'first_seen': datetime.now().isoformat(),
                    'last_heartbeat': time.time()
                }
                
                with self.nodes_lock:
                    self.nodes[node_id] = node_info
                    self.save_database()
                
                print(f"🟢 New node registered: {node_id} ({message.get('host')}:{message.get('port')})")
                
                # Send acknowledgment
                response = {'type': 'registered', 'status': 'success'}
                self.send_message(conn, json.dumps(response).encode('utf-8'))
                
            elif msg_type == 'heartbeat':
                # Node heartbeat
                node_id = message.get('node_id')
                with self.nodes_lock:
                    if node_id in self.nodes:
                        self.nodes[node_id]['last_heartbeat'] = time.time()
                        self.nodes[node_id]['status'] = 'online'
                
                # Send heartbeat acknowledgment
                response = {'type': 'heartbeat_ack', 'status': 'success'}
                self.send_message(conn, json.dumps(response).encode('utf-8'))
                
        except Exception as e:
            print(f"Node registration error: {e}")
        finally:
            conn.close()
    
    def handle_file_upload(self, conn, addr):
        """Handle file upload requests with chunk distribution"""
        try:
            # Receive upload request
            data = self.recv_message(conn)
            if not data:
                return
            
            request = json.loads(data.decode('utf-8'))
            if request.get('type') != 'upload':
                return
            
            filename = request.get('filename')
            file_size = request.get('file_size')
            file_data = request.get('file_data')
            
            print(f"📁 Upload request: {filename} ({file_size} bytes)")
            
            # Generate file ID and chunk the file
            file_id = str(uuid.uuid4())
            chunks = self.split_file_into_chunks(file_data, filename)
            
            # Select nodes for chunk storage
            available_nodes = []
            with self.nodes_lock:
                for node_id, node_info in self.nodes.items():
                    if node_info.get('status') == 'online':
                        available_nodes.append(node_id)
            
            if not available_nodes:
                response = {'type': 'upload_error', 'message': 'No available nodes'}
                self.send_message(conn, json.dumps(response).encode('utf-8'))
                return
            
            # Store chunks across nodes
            chunk_mapping = {}
            successful_chunks = 0
            
            for i, chunk_data in enumerate(chunks):
                chunk_id = f"{file_id}_chunk_{i}"
                selected_node = available_nodes[i % len(available_nodes)]
                
                # Send chunk to node
                if self.send_chunk_to_node(selected_node, chunk_id, chunk_data):
                    chunk_mapping[chunk_id] = selected_node
                    successful_chunks += 1
                    
                    # Store chunk metadata
                    with self.chunks_lock:
                        self.chunks[chunk_id] = {
                            'chunk_id': chunk_id,
                            'file_id': file_id,
                            'node_id': selected_node,
                            'size': len(chunk_data),
                            'created_at': datetime.now().isoformat()
                        }
                else:
                    print(f"❌ Failed to store chunk {chunk_id} on node {selected_node}")
            
            # Store file metadata
            if successful_chunks == len(chunks):
                with self.files_lock:
                    self.files[file_id] = {
                        'file_id': file_id,
                        'filename': filename,
                        'size': file_size,
                        'chunks': chunk_mapping,
                        'uploaded_at': datetime.now().isoformat(),
                        'status': 'complete'
                    }
                    self.save_database()
                
                response = {
                    'type': 'upload_complete',
                    'file_id': file_id,
                    'chunks_stored': successful_chunks,
                    'total_chunks': len(chunks)
                }
                print(f"✅ File upload complete: {filename} ({successful_chunks}/{len(chunks)} chunks)")
            else:
                response = {
                    'type': 'upload_error',
                    'message': f'Only {successful_chunks}/{len(chunks)} chunks stored'
                }
            
            self.send_message(conn, json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"File upload error: {e}")
            response = {'type': 'upload_error', 'message': str(e)}
            self.send_message(conn, json.dumps(response).encode('utf-8'))
        finally:
            conn.close()
    
    def split_file_into_chunks(self, file_data, filename):
        """Split file data into chunks for distribution"""
        chunk_size = len(file_data) // 3  # Split into 3 chunks
        if chunk_size == 0:
            chunk_size = len(file_data)
        
        chunks = []
        for i in range(0, len(file_data), chunk_size):
            chunk = file_data[i:i + chunk_size]
            chunks.append(chunk)
        
        return chunks
    
    def send_chunk_to_node(self, node_id, chunk_id, chunk_data):
        """Send chunk to specific node with ACK mechanism"""
        try:
            with self.nodes_lock:
                if node_id not in self.nodes:
                    return False
                node_info = self.nodes[node_id]
            
            # Connect to node
            node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            node_socket.settimeout(10)  # 10 second timeout
            node_socket.connect((node_info['host'], node_info['port']))
            
            # Send chunk storage request
            request = {
                'type': 'store_chunk',
                'chunk_id': chunk_id,
                'chunk_data': chunk_data.decode('latin1')  # Encode binary data as string
            }
            
            self.send_message(node_socket, json.dumps(request).encode('utf-8'))
            
            # Wait for ACK
            response_data = self.recv_message(node_socket)
            if response_data:
                response = json.loads(response_data.decode('utf-8'))
                if response.get('type') == 'store_ack' and response.get('status') == 'success':
                    node_socket.close()
                    return True
            
            node_socket.close()
            return False
            
        except Exception as e:
            print(f"Error sending chunk to node {node_id}: {e}")
            return False
    
    def monitor_nodes(self):
        """Monitor node health and detect offline nodes"""
        while self.running:
            try:
                current_time = time.time()
                with self.nodes_lock:
                    for node_id, node_info in list(self.nodes.items()):
                        last_heartbeat = node_info.get('last_heartbeat', 0)
                        if (current_time - last_heartbeat) > 60 and node_info.get('status') == 'online':
                            print(f"🔴 Node {node_id} marked offline (heartbeat timeout)")
                            self.nodes[node_id]['status'] = 'offline'
                            self.save_database()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Node monitoring error: {e}")
    
    def recv_message(self, sock):
        """Receive a message with length prefix"""
        try:
            # First receive the message length
            length_data = sock.recv(4)
            if not length_data:
                return None
            
            msg_length = struct.unpack('!I', length_data)[0]
            
            # Then receive the message data
            data = b''
            while len(data) < msg_length:
                chunk = sock.recv(min(msg_length - len(data), 4096))
                if not chunk:
                    return None
                data += chunk
            
            return data
        except Exception:
            return None
    
    def send_message(self, sock, data):
        """Send a message with length prefix"""
        try:
            # Send message length first
            msg_length = len(data)
            sock.sendall(struct.pack('!I', msg_length))
            
            # Then send the message data
            sock.sendall(data)
            return True
        except Exception:
            return False
    
    def start_node_listener(self):
        """Start listener for node registration and heartbeats"""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.node_port))
            server.listen(10)
            
            print(f"🌐 Node listener started on {self.host}:{self.node_port}")
            
            while self.running:
                try:
                    conn, addr = server.accept()
                    threading.Thread(target=self.handle_node_registration, args=(conn, addr)).start()
                except Exception as e:
                    if self.running:
                        print(f"Node listener error: {e}")
                        
        except Exception as e:
            print(f"Failed to start node listener: {e}")
    
    def start_upload_listener(self):
        """Start listener for file uploads"""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.upload_port))
            server.listen(10)
            
            print(f"📁 Upload listener started on {self.host}:{self.upload_port}")
            
            while self.running:
                try:
                    conn, addr = server.accept()
                    threading.Thread(target=self.handle_file_upload, args=(conn, addr)).start()
                except Exception as e:
                    if self.running:
                        print(f"Upload listener error: {e}")
                        
        except Exception as e:
            print(f"Failed to start upload listener: {e}")
    
    def start(self):
        """Start the cloud gateway"""
        print("🚀 Starting Cloud Gateway...")
        
        # Start all components in separate threads
        threading.Thread(target=self.start_node_listener, daemon=True).start()
        threading.Thread(target=self.start_upload_listener, daemon=True).start()
        threading.Thread(target=self.monitor_nodes, daemon=True).start()
        
        # Start the status display (blocking)
        try:
            self.display_status()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down Cloud Gateway...")
            self.running = False
            self.save_database()

if __name__ == "__main__":
    gateway = CloudGateway()
    gateway.start()