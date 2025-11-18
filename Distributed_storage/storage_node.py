#!/usr/bin/env python3
"""
Storage Node - Independent machine simulation for distributed cloud storage
Handles chunk storage, heartbeat communication, and autonomous operation
"""

import socket
import threading
import json
import os
import time
import hashlib
import struct
import uuid
import shutil
from datetime import datetime

class StorageNode:
    def __init__(self, node_id, host='localhost', port=9001, storage_capacity=1024*1024*1024, cpu_cores=1, bandwidth='1Gbps'):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.storage_capacity = storage_capacity
        self.cpu_cores = cpu_cores
        self.bandwidth = bandwidth
        self.cloud_host = 'localhost'
        self.cloud_port = 8001
        self.storage_dir = f"storage_{node_id}"
        self.running = True
        self.registered = False
        self.last_heartbeat = 0
        
        # Node statistics
        self.stats = {
            'chunks_stored': 0,
            'total_storage_used': 0,
            'uptime_start': datetime.now(),
            'total_requests': 0,
            'successful_requests': 0
        }
        
        # Thread-safe locks
        self.stats_lock = threading.Lock()
        self.storage_lock = threading.Lock()
        
    def boot_sequence(self):
        """Simulate node boot sequence"""
        print(f"🖥️  Node {self.node_id} booting up...")
        
        # Create storage directory and allocate disk space
        self.allocate_storage()
        
        # Check cloud gateway availability
        if self.check_cloud_availability():
            print(f"✅ Cloud Gateway found at {self.cloud_host}:{self.cloud_port}")
            if self.register_with_cloud():
                print(f"✅ Node {self.node_id} registered successfully")
                self.registered = True
            else:
                print(f"❌ Registration failed")
                return False
        else:
            print(f"❌ Cloud Gateway not available at {self.cloud_host}:{self.cloud_port}")
            print("🔄 Will retry registration periodically...")
            return False
        
        return True
    
    def allocate_storage(self):
        """Allocate real disk space for storage"""
        try:
            # Remove existing storage directory
            if os.path.exists(self.storage_dir):
                shutil.rmtree(self.storage_dir)
            
            # Create storage directory
            os.makedirs(self.storage_dir, exist_ok=True)
            
            # Create a large file to reserve disk space
            storage_file = os.path.join(self.storage_dir, 'storage_reserve.dat')
            with open(storage_file, 'wb') as f:
                # Write in chunks to avoid memory issues
                chunk_size = 1024 * 1024  # 1MB chunks
                remaining = self.storage_capacity
                
                while remaining > 0:
                    write_size = min(chunk_size, remaining)
                    f.write(b'\x00' * write_size)
                    remaining -= write_size
            
            print(f"💾 Storage allocated: {self.storage_capacity / (1024**3):.2f} GB at {self.storage_dir}")
            
        except Exception as e:
            print(f"❌ Storage allocation error: {e}")
            raise
    
    def check_cloud_availability(self):
        """Check if Cloud Gateway is reachable"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5 second timeout
            result = sock.connect_ex((self.cloud_host, self.cloud_port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def register_with_cloud(self):
        """Register this node with the Cloud Gateway"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.cloud_host, self.cloud_port))
            
            registration_msg = {
                'type': 'register',
                'node_id': self.node_id,
                'host': self.host,
                'port': self.port,
                'storage_capacity': self.storage_capacity,
                'cpu_cores': self.cpu_cores,
                'bandwidth': self.bandwidth
            }
            
            self.send_message(sock, json.dumps(registration_msg).encode('utf-8'))
            
            # Wait for response
            response_data = self.recv_message(sock)
            if response_data:
                response = json.loads(response_data.decode('utf-8'))
                if response.get('type') == 'registered' and response.get('status') == 'success':
                    sock.close()
                    return True
            
            sock.close()
            return False
            
        except Exception as e:
            print(f"Registration error: {e}")
            return False
    
    def send_heartbeat(self):
        """Send heartbeat to Cloud Gateway"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.cloud_host, self.cloud_port))
            
            heartbeat_msg = {
                'type': 'heartbeat',
                'node_id': self.node_id
            }
            
            self.send_message(sock, json.dumps(heartbeat_msg).encode('utf-8'))
            
            # Wait for ACK
            response_data = self.recv_message(sock)
            if response_data:
                response = json.loads(response_data.decode('utf-8'))
                if response.get('type') == 'heartbeat_ack':
                    self.last_heartbeat = time.time()
                    sock.close()
                    return True
            
            sock.close()
            return False
            
        except Exception as e:
            print(f"Heartbeat error: {e}")
            return False
    
    def handle_chunk_storage(self, conn, addr):
        """Handle chunk storage requests"""
        try:
            data = self.recv_message(conn)
            if not data:
                return
            
            request = json.loads(data.decode('utf-8'))
            if request.get('type') != 'store_chunk':
                return
            
            chunk_id = request.get('chunk_id')
            chunk_data = request.get('chunk_data').encode('latin1')  # Decode from string
            
            # Store chunk on disk
            chunk_path = os.path.join(self.storage_dir, f"{chunk_id}.chunk")
            
            with self.storage_lock:
                with open(chunk_path, 'wb') as f:
                    f.write(chunk_data)
                
                # Update statistics
                with self.stats_lock:
                    self.stats['chunks_stored'] += 1
                    self.stats['total_storage_used'] += len(chunk_data)
                    self.stats['total_requests'] += 1
                    self.stats['successful_requests'] += 1
            
            print(f"💾 Chunk stored: {chunk_id} ({len(chunk_data)} bytes)")
            
            # Send ACK
            response = {
                'type': 'store_ack',
                'status': 'success',
                'chunk_id': chunk_id
            }
            self.send_message(conn, json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"Chunk storage error: {e}")
            with self.stats_lock:
                self.stats['total_requests'] += 1
            
            # Send error response
            response = {
                'type': 'store_ack',
                'status': 'error',
                'message': str(e)
            }
            self.send_message(conn, json.dumps(response).encode('utf-8'))
        finally:
            conn.close()
    
    def handle_retrieve_chunk(self, conn, addr):
        """Handle chunk retrieval requests"""
        try:
            data = self.recv_message(conn)
            if not data:
                return
            
            request = json.loads(data.decode('utf-8'))
            if request.get('type') != 'retrieve_chunk':
                return
            
            chunk_id = request.get('chunk_id')
            chunk_path = os.path.join(self.storage_dir, f"{chunk_id}.chunk")
            
            if os.path.exists(chunk_path):
                with self.storage_lock:
                    with open(chunk_path, 'rb') as f:
                        chunk_data = f.read()
                
                response = {
                    'type': 'retrieve_ack',
                    'status': 'success',
                    'chunk_id': chunk_id,
                    'chunk_data': chunk_data.decode('latin1')  # Encode binary as string
                }
                print(f"📤 Chunk retrieved: {chunk_id}")
            else:
                response = {
                    'type': 'retrieve_ack',
                    'status': 'error',
                    'message': 'Chunk not found'
                }
                print(f"❌ Chunk not found: {chunk_id}")
            
            self.send_message(conn, json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"Chunk retrieval error: {e}")
            response = {
                'type': 'retrieve_ack',
                'status': 'error',
                'message': str(e)
            }
            self.send_message(conn, json.dumps(response).encode('utf-8'))
        finally:
            conn.close()
    
    def display_status(self):
        """Display node status and statistics"""
        while self.running:
            os.system('clear' if os.name == 'posix' else 'cls')
            
            uptime = datetime.now() - self.stats['uptime_start']
            
            print("=" * 60)
            print(f"        STORAGE NODE - {self.node_id}")
            print("=" * 60)
            print(f"Node ID: {self.node_id}")
            print(f"Address: {self.host}:{self.port}")
            print(f"Cloud Gateway: {self.cloud_host}:{self.cloud_port}")
            print(f"Registration Status: {'✅ Registered' if self.registered else '❌ Not Registered'}")
            print(f"Uptime: {str(uptime).split('.')[0]}")
            print()
            
            print("HARDWARE CONFIGURATION:")
            print(f"  Storage Capacity: {self.storage_capacity / (1024**3):.2f} GB")
            print(f"  CPU Cores: {self.cpu_cores}")
            print(f"  Bandwidth: {self.bandwidth}")
            print(f"  Storage Directory: {self.storage_dir}")
            print()
            
            print("PERFORMANCE STATISTICS:")
            print(f"  Chunks Stored: {self.stats['chunks_stored']}")
            print(f"  Storage Used: {self.stats['total_storage_used'] / (1024**2):.2f} MB")
            print(f"  Total Requests: {self.stats['total_requests']}")
            print(f"  Successful Requests: {self.stats['successful_requests']}")
            if self.stats['total_requests'] > 0:
                success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
                print(f"  Success Rate: {success_rate:.1f}%")
            print()
            
            print("SYSTEM STATUS:")
            print(f"  Status: {'🟢 ONLINE' if self.registered else '🔴 OFFLINE'}")
            if self.last_heartbeat > 0:
                print(f"  Last Heartbeat: {int(time.time() - self.last_heartbeat)}s ago")
            print()
            
            print("Commands: Ctrl+C to stop")
            print("=" * 60)
            
            time.sleep(5)  # Update every 5 seconds
    
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
    
    def start_listener(self):
        """Start node listener for chunk operations"""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(10)
            
            print(f"🌐 Node listener started on {self.host}:{self.port}")
            
            while self.running:
                try:
                    conn, addr = server.accept()
                    
                    # Handle different request types
                    data = self.recv_message(conn)
                    if data:
                        request = json.loads(data.decode('utf-8'))
                        request_type = request.get('type')
                        
                        if request_type == 'store_chunk':
                            threading.Thread(target=self.handle_chunk_storage, args=(conn, addr)).start()
                        elif request_type == 'retrieve_chunk':
                            threading.Thread(target=self.handle_retrieve_chunk, args=(conn, addr)).start()
                        else:
                            conn.close()
                    else:
                        conn.close()
                        
                except Exception as e:
                    if self.running:
                        print(f"Listener error: {e}")
                        
        except Exception as e:
            print(f"Failed to start listener: {e}")
    
    def heartbeat_loop(self):
        """Send periodic heartbeats to Cloud Gateway"""
        while self.running:
            try:
                if self.registered:
                    if self.send_heartbeat():
                        print(f"❤️  Heartbeat sent successfully")
                    else:
                        print(f"💔 Heartbeat failed - Cloud may be unreachable")
                        self.registered = False
                else:
                    # Try to register if not registered
                    if self.check_cloud_availability():
                        if self.register_with_cloud():
                            self.registered = True
                            print(f"✅ Re-registered with Cloud Gateway")
                
                time.sleep(30)  # Send heartbeat every 30 seconds
                
            except Exception as e:
                print(f"Heartbeat loop error: {e}")
                time.sleep(10)  # Wait before retrying
    
    def start(self):
        """Start the storage node"""
        print(f"🚀 Starting Storage Node {self.node_id}...")
        
        # Run boot sequence
        if not self.boot_sequence():
            print(f"❌ Boot sequence failed for Node {self.node_id}")
            return
        
        # Start all components
        threading.Thread(target=self.start_listener, daemon=True).start()
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        
        # Start status display (blocking)
        try:
            self.display_status()
        except KeyboardInterrupt:
            print(f"\n🛑 Shutting down Node {self.node_id}...")
            self.running = False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python storage_node.py <node_id> [host] [port] [storage_gb]")
        sys.exit(1)
    
    node_id = sys.argv[1]
    host = sys.argv[2] if len(sys.argv) > 2 else 'localhost'
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 9001
    storage_gb = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    
    storage_capacity = int(storage_gb * 1024 * 1024 * 1024)  # Convert GB to bytes
    
    node = StorageNode(node_id, host, port, storage_capacity)
    node.start()