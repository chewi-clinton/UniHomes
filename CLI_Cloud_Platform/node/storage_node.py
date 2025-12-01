#!/usr/bin/env python3
"""
Storage Node - Stores file chunks on disk using gRPC
FIXED: Proper import paths
"""
import grpc
from concurrent import futures
import os
import sys
import time
import threading
from datetime import datetime

# CRITICAL: Add parent directory to Python path BEFORE imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import from generated and other packages
from generated import cloud_storage_pb2
from generated import cloud_storage_pb2_grpc

class StorageNodeServicer(cloud_storage_pb2_grpc.NodeServiceServicer):
    def __init__(self, node_id, storage_dir):
        self.node_id = node_id
        self.storage_dir = storage_dir
        
        # Create storage directory
        os.makedirs(storage_dir, exist_ok=True)
        print(f"[STORAGE] Directory: {storage_dir}")
    
    def StoreChunk(self, request, context):
        """Store chunk on disk"""
        try:
            chunk_id = request.chunk_id
            chunk_data = request.chunk_data
            
            # Save to disk
            chunk_path = os.path.join(self.storage_dir, f"{chunk_id}.chunk")
            with open(chunk_path, 'wb') as f:
                f.write(chunk_data)
            
            print(f"[STORE] Chunk {chunk_id}: {len(chunk_data)} bytes")
            
            return cloud_storage_pb2.StoreChunkResponse(
                success=True,
                message="Chunk stored successfully"
            )
        
        except Exception as e:
            print(f"[ERROR] Store chunk failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def RetrieveChunk(self, request, context):
        """Retrieve chunk from disk"""
        try:
            chunk_id = request.chunk_id
            chunk_path = os.path.join(self.storage_dir, f"{chunk_id}.chunk")
            
            if not os.path.exists(chunk_path):
                return cloud_storage_pb2.RetrieveChunkResponse(
                    success=False,
                    message="Chunk not found"
                )
            
            with open(chunk_path, 'rb') as f:
                chunk_data = f.read()
            
            print(f"[RETRIEVE] Chunk {chunk_id}: {len(chunk_data)} bytes")
            
            return cloud_storage_pb2.RetrieveChunkResponse(
                success=True,
                chunk_data=chunk_data
            )
        
        except Exception as e:
            print(f"[ERROR] Retrieve chunk failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def DeleteChunk(self, request, context):
        """Delete chunk from disk"""
        try:
            chunk_id = request.chunk_id
            chunk_path = os.path.join(self.storage_dir, f"{chunk_id}.chunk")
            
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
                print(f"[DELETE] Chunk {chunk_id}")
            
            return cloud_storage_pb2.DeleteChunkResponse(
                success=True,
                message="Chunk deleted"
            )
        
        except Exception as e:
            print(f"[ERROR] Delete chunk failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))


def register_with_gateway(node_id, host, port, storage_capacity, gateway_host='localhost:50051'):
    """Register node with cloud gateway"""
    try:
        channel = grpc.insecure_channel(gateway_host)
        stub = cloud_storage_pb2_grpc.NodeServiceStub(channel)
        
        response = stub.RegisterNode(cloud_storage_pb2.RegisterNodeRequest(
            node_id=node_id,
            host=host,
            port=port,
            storage_capacity=storage_capacity,
            cpu_cores=4
        ))
        
        print(f"[REGISTER] {response.message}")
        channel.close()
        return True
    
    except Exception as e:
        print(f"[ERROR] Registration failed: {e}")
        return False


def send_heartbeat(node_id, storage_dir, gateway_host='localhost:50051'):
    """Send periodic heartbeat"""
    while True:
        try:
            time.sleep(30)  # Every 30 seconds
            
            # Calculate storage used
            storage_used = 0
            chunk_count = 0
            
            if os.path.exists(storage_dir):
                for filename in os.listdir(storage_dir):
                    filepath = os.path.join(storage_dir, filename)
                    if os.path.isfile(filepath) and filename.endswith('.chunk'):
                        storage_used += os.path.getsize(filepath)
                        chunk_count += 1
            
            channel = grpc.insecure_channel(gateway_host)
            stub = cloud_storage_pb2_grpc.NodeServiceStub(channel)
            
            response = stub.Heartbeat(cloud_storage_pb2.HeartbeatRequest(
                node_id=node_id,
                storage_used=storage_used,
                chunk_count=chunk_count
            ))
            
            print(f"[HEARTBEAT] {datetime.now().strftime('%H:%M:%S')} - {chunk_count} chunks, {storage_used} bytes")
            channel.close()
        
        except Exception as e:
            print(f"[ERROR] Heartbeat failed: {e}")


def serve(node_id, host, port, storage_capacity_gb):
    """Start the storage node"""
    storage_capacity = int(storage_capacity_gb * 1024**3)
    storage_dir = f'node_storage_{node_id}'
    
    print("=" * 60)
    print(f"STORAGE NODE - {node_id}")
    print("=" * 60)
    print(f"Address: {host}:{port}")
    print(f"Storage: {storage_capacity_gb} GB")
    print(f"Directory: {storage_dir}")
    print("=" * 60)
    
    # Register with gateway
    if register_with_gateway(node_id, host, port, storage_capacity):
        print("[OK] Registered with gateway")
    else:
        print("[WARN] Failed to register, will retry...")
    
    # Start heartbeat thread
    heartbeat_thread = threading.Thread(
        target=send_heartbeat,
        args=(node_id, storage_dir),
        daemon=True
    )
    heartbeat_thread.start()
    
    # Start gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    cloud_storage_pb2_grpc.add_NodeServiceServicer_to_server(
        StorageNodeServicer(node_id, storage_dir),
        server
    )
    server.add_insecure_port(f'[::]:{port}')
    
    print(f"[LISTEN] Node listening on port {port}")
    server.start()
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down storage node...")
        server.stop(0)


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: python storage_node.py <node_id> <host> <port> <storage_gb>")
        print("Example: python storage_node.py node1 localhost 9001 2")
        sys.exit(1)
    
    node_id = sys.argv[1]
    host = sys.argv[2]
    port = int(sys.argv[3])
    storage_gb = float(sys.argv[4])
    
    serve(node_id, host, port, storage_gb)