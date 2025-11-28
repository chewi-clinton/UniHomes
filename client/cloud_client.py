"""
Cloud Client - gRPC client for interacting with cloud storage
"""
import grpc
import os
from pathlib import Path

from generated import cloud_storage_pb2
from generated import cloud_storage_pb2_grpc


class CloudClient:
    def __init__(self, server_address='localhost:50051'):
        self.server_address = server_address
        self.channel = grpc.insecure_channel(server_address)
        
        # Initialize service stubs
        self.auth_stub = cloud_storage_pb2_grpc.AuthServiceStub(self.channel)
        self.file_stub = cloud_storage_pb2_grpc.FileServiceStub(self.channel)
        self.storage_stub = cloud_storage_pb2_grpc.StorageServiceStub(self.channel)
        
        # Session management
        self.session_token = None
        self.user_id = None
        self.email = None
    
    # ============================================================================
    # Authentication Methods
    # ============================================================================
    
    def send_otp(self, email):
        """Send OTP to email"""
        try:
            response = self.auth_stub.SendOTP(
                cloud_storage_pb2.SendOTPRequest(email=email)
            )
            return response.success, response.message
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}"
    
    def verify_otp(self, email, otp):
        """Verify OTP"""
        try:
            response = self.auth_stub.VerifyOTP(
                cloud_storage_pb2.VerifyOTPRequest(email=email, otp=otp)
            )
            return response.success, response.message
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}"
    
    def enroll(self, email, full_name):
        """Enroll new user"""
        try:
            response = self.auth_stub.Enroll(
                cloud_storage_pb2.EnrollRequest(email=email, full_name=full_name)
            )
            
            if response.success:
                self.session_token = response.session_token
                self.user_id = response.user_id
                self.email = email
            
            return response.success, response.message
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}"
    
    def login(self, email):
        """Login existing user"""
        try:
            response = self.auth_stub.Login(
                cloud_storage_pb2.LoginRequest(email=email)
            )
            
            if response.success:
                self.session_token = response.session_token
                self.user_id = response.user_id
                self.email = email
            
            return response.success, response.message
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}"
    
    def logout(self):
        """Logout current user"""
        if not self.session_token:
            return False, "Not logged in"
        
        try:
            response = self.auth_stub.Logout(
                cloud_storage_pb2.LogoutRequest(session_token=self.session_token)
            )
            
            if response.success:
                self.session_token = None
                self.user_id = None
                self.email = None
            
            return response.success, response.message
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}"
    
    # ============================================================================
    # File Operations
    # ============================================================================
    
    def upload_file(self, file_path, parent_folder_id=None):
        """Upload a file to cloud storage"""
        if not self.session_token:
            return False, "Not logged in", None
        
        if not os.path.exists(file_path):
            return False, "File not found", None
        
        try:
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            filename = os.path.basename(file_path)
            file_size = len(file_data)
            
            # Detect MIME type
            import mimetypes
            mime_type, _ = mimetypes.guess_type(filename)
            mime_type = mime_type or 'application/octet-stream'
            
            # Create request iterator
            def request_iterator():
                # First message: metadata
                yield cloud_storage_pb2.UploadFileRequest(
                    metadata=cloud_storage_pb2.FileMetadata(
                        session_token=self.session_token,
                        filename=filename,
                        file_size=file_size,
                        mime_type=mime_type,
                        parent_folder_id=parent_folder_id or ""
                    )
                )
                
                # Subsequent messages: chunks
                chunk_size = 64 * 1024  # 64KB chunks
                for i in range(0, file_size, chunk_size):
                    chunk = file_data[i:i + chunk_size]
                    yield cloud_storage_pb2.UploadFileRequest(chunk_data=chunk)
            
            # Upload file
            response = self.file_stub.UploadFile(request_iterator())
            
            return response.success, response.message, response.file_id
        
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}", None
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    def download_file(self, file_id, output_path=None):
        """Download a file from cloud storage"""
        if not self.session_token:
            return False, "Not logged in"
        
        try:
            # Request file download
            request = cloud_storage_pb2.DownloadFileRequest(
                session_token=self.session_token,
                file_id=file_id
            )
            
            response_stream = self.file_stub.DownloadFile(request)
            
            # First response contains file info
            first_response = next(response_stream)
            
            if not first_response.HasField('file_info'):
                return False, "Invalid response from server"
            
            file_info = first_response.file_info
            filename = file_info.filename
            
            # Determine output path
            if not output_path:
                output_path = filename
            elif os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
            
            # Download file chunks
            file_data = b''
            for response in response_stream:
                if response.HasField('chunk_data'):
                    file_data += response.chunk_data
            
            # Write file
            with open(output_path, 'wb') as f:
                f.write(file_data)
            
            return True, f"File downloaded to {output_path}"
        
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def list_files(self, folder_id=None, include_deleted=False):
        """List files in cloud storage"""
        if not self.session_token:
            return False, "Not logged in", [], []
        
        try:
            response = self.file_stub.ListFiles(
                cloud_storage_pb2.ListFilesRequest(
                    session_token=self.session_token,
                    folder_id=folder_id or "",
                    include_deleted=include_deleted
                )
            )
            
            files = []
            for file in response.files:
                files.append({
                    'file_id': file.file_id,
                    'filename': file.filename,
                    'file_size': file.file_size,
                    'mime_type': file.mime_type,
                    'created_at': file.created_at,
                    'modified_at': file.modified_at,
                    'is_shared': file.is_shared
                })
            
            folders = []
            for folder in response.folders:
                folders.append({
                    'folder_id': folder.folder_id,
                    'folder_name': folder.folder_name,
                    'created_at': folder.created_at,
                    'file_count': folder.file_count
                })
            
            return True, "Success", files, folders
        
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}", [], []
    
    def delete_file(self, file_id, permanent=False):
        """Delete a file"""
        if not self.session_token:
            return False, "Not logged in"
        
        try:
            response = self.file_stub.DeleteFile(
                cloud_storage_pb2.DeleteFileRequest(
                    session_token=self.session_token,
                    file_id=file_id,
                    permanent=permanent
                )
            )
            
            return response.success, response.message
        
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}"
    
    def get_file_metadata(self, file_id):
        """Get file metadata"""
        if not self.session_token:
            return False, "Not logged in", None
        
        try:
            response = self.file_stub.GetFileMetadata(
                cloud_storage_pb2.FileMetadataRequest(
                    session_token=self.session_token,
                    file_id=file_id
                )
            )
            
            if response.success:
                file_info = {
                    'file_id': response.file.file_id,
                    'filename': response.file.filename,
                    'file_size': response.file.file_size,
                    'mime_type': response.file.mime_type,
                    'created_at': response.file.created_at,
                    'modified_at': response.file.modified_at,
                    'is_shared': response.file.is_shared,
                    'chunk_count': response.chunk_count
                }
                return True, "Success", file_info
            
            return False, "Failed to get metadata", None
        
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}", None
    
    def create_folder(self, folder_name, parent_folder_id=None):
        """Create a folder"""
        if not self.session_token:
            return False, "Not logged in", None
        
        try:
            response = self.file_stub.CreateFolder(
                cloud_storage_pb2.CreateFolderRequest(
                    session_token=self.session_token,
                    folder_name=folder_name,
                    parent_folder_id=parent_folder_id or ""
                )
            )
            
            return response.success, response.message, response.folder_id
        
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}", None
    
    def share_file(self, file_id, share_with_email, permission='read'):
        """Share a file with another user"""
        if not self.session_token:
            return False, "Not logged in", None
        
        try:
            response = self.file_stub.ShareFile(
                cloud_storage_pb2.ShareFileRequest(
                    session_token=self.session_token,
                    file_id=file_id,
                    share_with_email=share_with_email,
                    permission=permission
                )
            )
            
            return response.success, response.message, response.share_token
        
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}", None
    
    def get_shared_files(self):
        """Get files shared with current user"""
        if not self.session_token:
            return False, "Not logged in", []
        
        try:
            response = self.file_stub.GetSharedFiles(
                cloud_storage_pb2.GetSharedFilesRequest(
                    session_token=self.session_token
                )
            )
            
            shared_files = []
            for file in response.shared_files:
                shared_files.append({
                    'file_id': file.file_id,
                    'filename': file.filename,
                    'shared_by_email': file.shared_by_email,
                    'permission': file.permission,
                    'shared_at': file.shared_at
                })
            
            return True, "Success", shared_files
        
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}", []
    
    # ============================================================================
    # Storage Information
    # ============================================================================
    
    def get_storage_info(self):
        """Get storage information for current user"""
        if not self.session_token:
            return False, "Not logged in", None
        
        try:
            response = self.storage_stub.GetStorageInfo(
                cloud_storage_pb2.StorageInfoRequest(
                    session_token=self.session_token
                )
            )
            
            if response.success:
                storage_info = {
                    'allocated_bytes': response.allocated_bytes,
                    'used_bytes': response.used_bytes,
                    'available_bytes': response.available_bytes,
                    'usage_percentage': response.usage_percentage
                }
                return True, "Success", storage_info
            
            return False, "Failed to get storage info", None
        
        except grpc.RpcError as e:
            return False, f"RPC Error: {e.details()}", None
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    def is_logged_in(self):
        """Check if user is logged in"""
        return self.session_token is not None
    
    def format_bytes(self, bytes_value):
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def close(self):
        """Close the client connection"""
        self.channel.close()