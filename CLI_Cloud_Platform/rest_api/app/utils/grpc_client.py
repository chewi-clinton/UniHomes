import os
import sys
import grpc
import json
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# Now import from the generated folder
from generated import cloud_storage_pb2, cloud_storage_pb2_grpc

class GrpcClient:
    def __init__(self, server_address):
        self.server_address = server_address
        self.channel = grpc.insecure_channel(server_address)
        self.auth_stub = cloud_storage_pb2_grpc.AuthServiceStub(self.channel)
        self.file_stub = cloud_storage_pb2_grpc.FileServiceStub(self.channel)
        self.storage_stub = cloud_storage_pb2_grpc.StorageServiceStub(self.channel)
        self.admin_stub = cloud_storage_pb2_grpc.AdminServiceStub(self.channel)
    
    def close(self):
        self.channel.close()

# Global gRPC client
grpc_client = None

def init_grpc_client(app):
    global grpc_client
    grpc_client = GrpcClient(app.config['GRPC_SERVER'])

def get_grpc_client():
    return grpc_client