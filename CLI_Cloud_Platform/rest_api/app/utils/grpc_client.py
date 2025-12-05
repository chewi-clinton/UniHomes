import os
import sys
import grpc

# Adjust path to find the generated protobuf modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# Import generated protobuf files
from generated import cloud_storage_pb2, cloud_storage_pb2_grpc


class GrpcClient:
    def __init__(self, server_address):
        self.server_address = server_address
        self.channel = grpc.insecure_channel(server_address)
        
        # Service stubs
        self.auth_stub = cloud_storage_pb2_grpc.AuthServiceStub(self.channel)
        self.file_stub = cloud_storage_pb2_grpc.FileServiceStub(self.channel)
        self.storage_stub = cloud_storage_pb2_grpc.StorageServiceStub(self.channel)
        self.admin_stub = cloud_storage_pb2_grpc.AdminServiceStub(self.channel)
        self.payment_stub = cloud_storage_pb2_grpc.PaymentServiceStub(self.channel)  # Fully added

    def close(self):
        """Close the gRPC channel"""
        self.channel.close()


# Global gRPC client instance
grpc_client = None


def init_grpc_client(app):
    """Initialize the global gRPC client from Flask app config"""
    global grpc_client
    server_address = app.config.get('GRPC_SERVER', 'localhost:50051')
    grpc_client = GrpcClient(server_address)
    print(f"[gRPC] Client initialized → {server_address}")


def get_grpc_client():
    """Return the singleton gRPC client"""
    if grpc_client is None:
        raise RuntimeError("gRPC client not initialized. Call init_grpc_client() first.")
    return grpc_client