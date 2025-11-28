"""
Cloud Server - Main gRPC server handling all services
UPDATED: Dynamic storage that grows with nodes
"""
import grpc
from concurrent import futures
import sys
import os
import queue
import threading
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import generated.cloud_storage_pb2 as cloud_storage_pb2
import generated.cloud_storage_pb2_grpc as cloud_storage_pb2_grpc
from auth.gmail_otp import OTPManager
from user.user_manager import UserManager
from file.file_manager import FileManager
from storage.chunk_distributor import ChunkDistributor
from storage.node_manager import NodeManager
from db.database import init_database
from db.models import SystemEvent as SystemEventModel
from db.database import get_db_session
from utils.helpers import calculate_checksum, split_file_into_chunks
from dotenv import load_dotenv

load_dotenv()

# Admin key for system management
ADMIN_KEY = os.getenv('ADMIN_KEY', 'admin123')

# Initialize managers
otp_manager = OTPManager()
user_manager = UserManager()
file_manager = FileManager()
chunk_distributor = ChunkDistributor()
node_manager = NodeManager()

# Event queue for real-time streaming
event_queue = queue.Queue()


def emit_event(event_type, message, user_id=None, details=None):
    """Emit system event"""
    event = cloud_storage_pb2.SystemEvent(
        event_type=event_type,
        timestamp=datetime.utcnow().isoformat(),
        message=message,
        user_id=user_id or "",
        details=details or ""
    )
    event_queue.put(event)
    
    # Also log to database
    try:
        with get_db_session() as session:
            db_event = SystemEventModel(
                event_type=event_type,
                message=message,
                user_id=user_id,
                metadatass={'details': details} if details else {}
            )
            session.add(db_event)
        print(f"[EVENT] {event_type}: {message}")
    except Exception as e:
        print(f"[ERROR] Failed to log event: {e}")


class AuthServiceServicer(cloud_storage_pb2_grpc.AuthServiceServicer):
    """Authentication Service Implementation"""
    
    def SendOTP(self, request, context):
        """Send OTP to user's email"""
        email = request.email
        
        if not email or '@' not in email:
            return cloud_storage_pb2.SendOTPResponse(
                success=False,
                message="Invalid email address"
            )
        
        success, message = otp_manager.send_otp(email)
        
        if success:
            user_manager.mark_email_verified(email)
            emit_event('OTP_SENT', f'OTP sent to {email}')
        
        return cloud_storage_pb2.SendOTPResponse(
            success=success,
            message=message
        )
    
    def VerifyOTP(self, request, context):
        """Verify OTP"""
        email = request.email
        otp = request.otp
        
        success, message = otp_manager.verify_otp(email, otp)
        
        if success:
            emit_event('OTP_VERIFIED', f'OTP verified for {email}')
        
        return cloud_storage_pb2.VerifyOTPResponse(
            success=success,
            message=message
        )
    
    def Login(self, request, context):
        """Login existing user"""
        email = request.email
        
        success, message, session_token, user_id = user_manager.login_user(email)
        
        if not success:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, message)
        
        emit_event('USER_LOGIN', f'User logged in: {email}', user_id=user_id)
        
        return cloud_storage_pb2.LoginResponse(
            success=True,
            message=message,
            session_token=session_token,
            user_id=user_id
        )
    
    def Enroll(self, request, context):
        """Enroll new user"""
        email = request.email
        full_name = request.full_name
        
        success, message, session_token, user_id = user_manager.enroll_user(email, full_name)
        
        if not success:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, message)
        
        emit_event('USER_ENROLLED', f'New user enrolled: {full_name} ({email})', user_id=user_id)
        
        return cloud_storage_pb2.EnrollResponse(
            success=True,
            message=message,
            session_token=session_token,
            user_id=user_id
        )
    
    def Logout(self, request, context):
        """Logout user"""
        session_token = request.session_token
        
        success, message = user_manager.logout_user(session_token)
        
        return cloud_storage_pb2.LogoutResponse(
            success=success,
            message=message
        )


class FileServiceServicer(cloud_storage_pb2_grpc.FileServiceServicer):
    """File Service Implementation"""
    
    def UploadFile(self, request_iterator, context):
        """Handle file upload with streaming"""
        try:
            # First message contains metadatass
            first_request = next(request_iterator)
            
            if not first_request.HasField('metadatas'):
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "First message must contain metadatas")
            
            metadatas = first_request.metadatas
            session_token = metadatas.session_token
            filename = metadatas.filename
            file_size = metadatas.file_size
            mime_type = metadatas.mime_type
            parent_folder_id = metadatas.parent_folder_id if metadatas.parent_folder_id else None
            
            # Validate session
            user = user_manager.validate_session(session_token)
            if not user:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
            
            # Check storage quota
            if not user_manager.check_storage_available(user.user_id, file_size):
                context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, "Storage quota exceeded")
            
            print(f"[UPLOAD] Starting: {filename} ({file_size} bytes) for user {user.email}")
            
            # Receive file data
            file_data = b''
            for request in request_iterator:
                if request.HasField('chunk_data'):
                    file_data += request.chunk_data
            
            print(f"[UPLOAD] Received {len(file_data)} bytes")
            
            # Create file metadatas
            success, message, file_id = file_manager.create_file(
                user.user_id,
                filename,
                file_size,
                mime_type,
                parent_folder_id
            )
            
            if not success:
                context.abort(grpc.StatusCode.INTERNAL, message)
            
            # Split into chunks
            chunks = split_file_into_chunks(file_data, num_chunks=4)
            print(f"[UPLOAD] Split into {len(chunks)} chunks")
            
            # Select nodes for chunks
            node_mapping, error = chunk_distributor.select_nodes_for_chunks(len(chunks), replication_factor=1)
            if error:
                context.abort(grpc.StatusCode.UNAVAILABLE, error)
            
            # Store chunks on nodes
            chunks_stored = 0
            for i, chunk_data in enumerate(chunks):
                chunk_checksum = calculate_checksum(chunk_data)
                node_info = node_mapping[i]
                
                # Store chunk on primary node
                success = self._store_chunk_on_node(
                    node_info['primary_host'],
                    node_info['primary_port'],
                    file_id,
                    i,
                    chunk_data,
                    chunk_checksum
                )
                
                if success:
                    # Add chunk metadatas
                    file_manager.add_chunk(
                        file_id,
                        i,
                        len(chunk_data),
                        chunk_checksum,
                        node_info['primary'],
                        node_info['replicas']
                    )
                    chunks_stored += 1
                    print(f"[UPLOAD] Chunk {i+1}/{len(chunks)} stored on {node_info['primary']}")
                else:
                    print(f"[ERROR] Failed to store chunk {i}")
            
            # Update user storage
            user_manager.update_storage_usage(user.user_id, file_size)
            
            emit_event(
                'FILE_UPLOADED',
                f'File uploaded: {filename} ({file_size} bytes)',
                user_id=user.user_id,
                details=file_id
            )
            
            return cloud_storage_pb2.UploadFileResponse(
                success=True,
                message="File uploaded successfully",
                file_id=file_id,
                chunks_stored=chunks_stored
            )
        
        except StopIteration:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "No data received")
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            import traceback
            traceback.print_exc()
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def _store_chunk_on_node(self, host, port, file_id, chunk_index, chunk_data, checksum):
        """Store a chunk on a storage node"""
        try:
            channel = grpc.insecure_channel(f'{host}:{port}')
            stub = cloud_storage_pb2_grpc.NodeServiceStub(channel)
            
            chunk_id = f"{file_id}_chunk_{chunk_index}"
            
            response = stub.StoreChunk(cloud_storage_pb2.StoreChunkRequest(
                chunk_id=chunk_id,
                chunk_data=chunk_data,
                checksum=checksum
            ))
            
            channel.close()
            return response.success
        
        except Exception as e:
            print(f"[ERROR] Failed to store chunk on node: {e}")
            return False
    
    def DownloadFile(self, request, context):
        """Handle file download with streaming"""
        try:
            session_token = request.session_token
            file_id = request.file_id
            
            # Validate session
            user = user_manager.validate_session(session_token)
            if not user:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
            
            # Get file metadatas
            file_info = file_manager.get_file(file_id, user.user_id)
            if not file_info:
                context.abort(grpc.StatusCode.NOT_FOUND, "File not found")
            
            print(f"[DOWNLOAD] Starting: {file_info['filename']} for user {user.email}")
            
            # Get chunks
            chunks = file_manager.get_file_chunks(file_id)
            
            # Send file info first
            yield cloud_storage_pb2.DownloadFileResponse(
                file_info=cloud_storage_pb2.FileInfo(
                    filename=file_info['filename'],
                    file_size=file_info['file_size'],
                    mime_type=file_info['mime_type'],
                    total_chunks=len(chunks)
                )
            )
            
            # Stream chunks
            for chunk_info in chunks:
                chunk_data = self._retrieve_chunk_from_node(chunk_info)
                
                if chunk_data:
                    yield cloud_storage_pb2.DownloadFileResponse(
                        chunk_data=chunk_data
                    )
                else:
                    context.abort(grpc.StatusCode.DATA_LOSS, f"Failed to retrieve chunk {chunk_info['chunk_index']}")
            
            emit_event(
                'FILE_DOWNLOADED',
                f'File downloaded: {file_info["filename"]}',
                user_id=user.user_id,
                details=file_id
            )
            
            print(f"[DOWNLOAD] Complete: {file_info['filename']}")
        
        except Exception as e:
            print(f"[ERROR] Download failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def _retrieve_chunk_from_node(self, chunk_info):
        """Retrieve chunk from storage node"""
        try:
            node_info, error = chunk_distributor.get_node_for_retrieval(chunk_info['chunk_id'])
            
            if error:
                print(f"[ERROR] {error}")
                return None
            
            channel = grpc.insecure_channel(f"{node_info['host']}:{node_info['port']}")
            stub = cloud_storage_pb2_grpc.NodeServiceStub(channel)
            
            response = stub.RetrieveChunk(cloud_storage_pb2.RetrieveChunkRequest(
                chunk_id=chunk_info['chunk_id']
            ))
            
            channel.close()
            
            if response.success:
                return response.chunk_data
            return None
        
        except Exception as e:
            print(f"[ERROR] Failed to retrieve chunk: {e}")
            return None
    
    def ListFiles(self, request, context):
        """List files for user"""
        try:
            session_token = request.session_token
            folder_id = request.folder_id if request.folder_id else None
            include_deleted = request.include_deleted
            
            # Validate session
            user = user_manager.validate_session(session_token)
            if not user:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
            
            success, files, folders = file_manager.list_files(user.user_id, folder_id, include_deleted)
            
            # Convert to protobuf
            file_entries = []
            for file in files:
                file_entries.append(cloud_storage_pb2.FileEntry(
                    file_id=file['file_id'],
                    filename=file['filename'],
                    file_size=file['file_size'],
                    mime_type=file['mime_type'],
                    created_at=file['created_at'],
                    modified_at=file['modified_at'],
                    is_shared=file['is_shared']
                ))
            
            folder_entries = []
            for folder in folders:
                folder_entries.append(cloud_storage_pb2.FolderEntry(
                    folder_id=folder['folder_id'],
                    folder_name=folder['folder_name'],
                    created_at=folder['created_at'],
                    file_count=folder['file_count']
                ))
            
            return cloud_storage_pb2.ListFilesResponse(
                success=True,
                files=file_entries,
                folders=folder_entries
            )
        
        except Exception as e:
            print(f"[ERROR] List files failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def DeleteFile(self, request, context):
        """Delete file"""
        try:
            session_token = request.session_token
            file_id = request.file_id
            permanent = request.permanent
            
            # Validate session
            user = user_manager.validate_session(session_token)
            if not user:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
            
            success, message, chunk_ids = file_manager.delete_file(file_id, user.user_id, permanent)
            
            if not success:
                context.abort(grpc.StatusCode.NOT_FOUND, message)
            
            # If permanent delete, remove chunks from nodes
            if permanent and chunk_ids:
                for chunk_id in chunk_ids:
                    self._delete_chunk_from_nodes(chunk_id)
            
            emit_event(
                'FILE_DELETED',
                f'File deleted: {file_id} (permanent={permanent})',
                user_id=user.user_id
            )
            
            return cloud_storage_pb2.DeleteFileResponse(
                success=True,
                message=message
            )
        
        except Exception as e:
            print(f"[ERROR] Delete file failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def _delete_chunk_from_nodes(self, chunk_id):
        """Delete chunk from storage nodes"""
        try:
            node_info, error = chunk_distributor.get_node_for_retrieval(chunk_id)
            if error:
                return
            
            channel = grpc.insecure_channel(f"{node_info['host']}:{node_info['port']}")
            stub = cloud_storage_pb2_grpc.NodeServiceStub(channel)
            
            stub.DeleteChunk(cloud_storage_pb2.DeleteChunkRequest(chunk_id=chunk_id))
            channel.close()
        
        except Exception as e:
            print(f"[ERROR] Failed to delete chunk: {e}")
    
    def GetFilemetadatas(self, request, context):
        """Get file metadatas"""
        try:
            session_token = request.session_token
            file_id = request.file_id
            
            # Validate session
            user = user_manager.validate_session(session_token)
            if not user:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
            
            file_info = file_manager.get_file(file_id, user.user_id)
            if not file_info:
                context.abort(grpc.StatusCode.NOT_FOUND, "File not found")
            
            chunks = file_manager.get_file_chunks(file_id)
            
            return cloud_storage_pb2.FilemetadatasResponse(
                success=True,
                file=cloud_storage_pb2.FileEntry(
                    file_id=file_info['file_id'],
                    filename=file_info['filename'],
                    file_size=file_info['file_size'],
                    mime_type=file_info['mime_type'],
                    created_at=file_info['created_at'],
                    modified_at=file_info['modified_at'],
                    is_shared=file_info['is_shared']
                ),
                chunk_count=len(chunks)
            )
        
        except Exception as e:
            print(f"[ERROR] Get metadatas failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def CreateFolder(self, request, context):
        """Create folder"""
        try:
            session_token = request.session_token
            folder_name = request.folder_name
            parent_folder_id = request.parent_folder_id if request.parent_folder_id else None
            
            # Validate session
            user = user_manager.validate_session(session_token)
            if not user:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
            
            success, message, folder_id = file_manager.create_folder(user.user_id, folder_name, parent_folder_id)
            
            if not success:
                context.abort(grpc.StatusCode.INTERNAL, message)
            
            return cloud_storage_pb2.CreateFolderResponse(
                success=True,
                message=message,
                folder_id=folder_id
            )
        
        except Exception as e:
            print(f"[ERROR] Create folder failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def ShareFile(self, request, context):
        """Share file with another user"""
        try:
            session_token = request.session_token
            file_id = request.file_id
            share_with_email = request.share_with_email
            permission = request.permission
            
            # Validate session
            user = user_manager.validate_session(session_token)
            if not user:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
            
            success, message, share_token = file_manager.share_file(
                file_id, user.user_id, share_with_email, permission
            )
            
            if not success:
                context.abort(grpc.StatusCode.NOT_FOUND, message)
            
            return cloud_storage_pb2.ShareFileResponse(
                success=True,
                message=message,
                share_token=share_token
            )
        
        except Exception as e:
            print(f"[ERROR] Share file failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def GetSharedFiles(self, request, context):
        """Get files shared with user"""
        try:
            session_token = request.session_token
            
            # Validate session
            user = user_manager.validate_session(session_token)
            if not user:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
            
            success, shared_files = file_manager.get_shared_files(user.user_id)
            
            entries = []
            for file in shared_files:
                entries.append(cloud_storage_pb2.SharedFileEntry(
                    file_id=file['file_id'],
                    filename=file['filename'],
                    shared_by_email=file['shared_by_email'],
                    permission=file['permission'],
                    shared_at=file['shared_at']
                ))
            
            return cloud_storage_pb2.GetSharedFilesResponse(
                success=True,
                shared_files=entries
            )
        
        except Exception as e:
            print(f"[ERROR] Get shared files failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))


class StorageServiceServicer(cloud_storage_pb2_grpc.StorageServiceServicer):
    """Storage Service Implementation"""
    
    def GetStorageInfo(self, request, context):
        """Get storage information"""
        try:
            session_token = request.session_token
            
            storage_info = user_manager.get_storage_info(session_token)
            if not storage_info:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
            
            return cloud_storage_pb2.StorageInfoResponse(
                success=True,
                allocated_bytes=storage_info['allocated'],
                used_bytes=storage_info['used'],
                available_bytes=storage_info['available'],
                usage_percentage=storage_info['usage_percentage']
            )
        
        except Exception as e:
            print(f"[ERROR] Get storage info failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def GetStorageUsage(self, request, context):
        """Get detailed storage usage"""
        # Implementation for future enhancement
        return cloud_storage_pb2.StorageUsageResponse(
            success=True,
            total_files=0,
            total_folders=0
        )


class NodeServiceServicer(cloud_storage_pb2_grpc.NodeServiceServicer):
    """Node Service Implementation (for nodes to communicate with gateway)"""
    
    def RegisterNode(self, request, context):
        """Register storage node - DYNAMICALLY increases global storage"""
        try:
            success, message = node_manager.register_node(
                request.node_id,
                request.host,
                request.port,
                request.storage_capacity,
                request.cpu_cores
            )
            
            # Emit event with storage change info
            stats = node_manager.get_storage_statistics()
            if stats:
                emit_event(
                    'NODE_REGISTERED',
                    f'Node registered: {request.node_id} | Global storage: {stats["global_capacity"] / (1024**3):.2f} GB',
                    details=request.node_id
                )
            
            return cloud_storage_pb2.RegisterNodeResponse(
                success=success,
                message=message
            )
        
        except Exception as e:
            print(f"[ERROR] Register node failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def Heartbeat(self, request, context):
        """Handle node heartbeat"""
        try:
            success, message = node_manager.update_heartbeat(
                request.node_id,
                request.storage_used,
                request.chunk_count
            )
            
            return cloud_storage_pb2.HeartbeatResponse(
                success=success,
                message=message
            )
        
        except Exception as e:
            print(f"[ERROR] Heartbeat failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))


class AdminServiceServicer(cloud_storage_pb2_grpc.AdminServiceServicer):
    """Admin Service Implementation"""
    
    def GetSystemStatus(self, request, context):
        """Get system status with DYNAMIC storage"""
        try:
            if request.admin_key != ADMIN_KEY:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid admin key")
            
            # Get DYNAMIC storage statistics
            stats = node_manager.get_storage_statistics()
            
            if not stats:
                context.abort(grpc.StatusCode.INTERNAL, "Failed to get statistics")
            
            # Get file and chunk counts
            with get_db_session() as session:
                from db.models import File, Chunk
                
                total_files = session.query(File).filter_by(deleted_at=None).count()
                total_chunks = session.query(Chunk).count()
            
            return cloud_storage_pb2.SystemStatusResponse(
                success=True,
                global_capacity_bytes=stats['global_capacity'],
                global_allocated_bytes=stats['user_allocated'],
                global_used_bytes=stats['global_used'],
                total_users=len([]),  # Will be implemented
                total_nodes=stats['total_nodes'],
                online_nodes=stats['online_nodes'],
                total_files=total_files,
                total_chunks=total_chunks,
                system_health=100.0 if stats['online_nodes'] > 0 else 0.0
            )
        
        except Exception as e:
            print(f"[ERROR] Get system status failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def StreamSystemEvents(self, request, context):
        """Stream real-time system events"""
        try:
            if request.admin_key != ADMIN_KEY:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid admin key")
            
            print("[ADMIN] Event streaming started")
            
            while True:
                try:
                    event = event_queue.get(timeout=1.0)
                    yield event
                except:
                    if not context.is_active():
                        break
        
        except Exception as e:
            print(f"[ERROR] Event stream failed: {e}")


def serve():
    """Start the cloud server"""
    print("=" * 70)
    print("CLOUD STORAGE PLATFORM - SERVER (DYNAMIC STORAGE)")
    print("=" * 70)
    
    # Initialize database
    init_database()
    
    # Display current storage capacity
    stats = node_manager.get_storage_statistics()
    if stats:
        print(f"Current Global Storage: {stats['global_capacity'] / (1024**3):.2f} GB")
        print(f"Online Nodes: {stats['online_nodes']}/{stats['total_nodes']}")
    else:
        print("Current Global Storage: 0 GB (no nodes registered)")
    print("Storage will grow as nodes are added!")
    
    # Create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=50))
    
    # Add servicers
    cloud_storage_pb2_grpc.add_AuthServiceServicer_to_server(
        AuthServiceServicer(), server
    )
    cloud_storage_pb2_grpc.add_FileServiceServicer_to_server(
        FileServiceServicer(), server
    )
    cloud_storage_pb2_grpc.add_StorageServiceServicer_to_server(
        StorageServiceServicer(), server
    )
    cloud_storage_pb2_grpc.add_NodeServiceServicer_to_server(
        NodeServiceServicer(), server
    )
    cloud_storage_pb2_grpc.add_AdminServiceServicer_to_server(
        AdminServiceServicer(), server
    )
    
    # Start server
    port = os.getenv('GRPC_SERVER_PORT', '50051')
    server.add_insecure_port(f'[::]:{port}')
    
    print(f"Server listening on port {port}")
    print(f"Admin Key: {ADMIN_KEY}")
    print("=" * 70)
    print("\n[READY] Cloud server is ready to accept connections")
    print("[INFO] Global storage grows automatically as nodes register!\n")
    
    server.start()
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down cloud server...")
        server.stop(0)


if __name__ == '__main__':
    serve()