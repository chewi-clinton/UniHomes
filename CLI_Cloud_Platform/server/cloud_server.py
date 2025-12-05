import grpc
from concurrent import futures
import sys
import os
import queue
import threading
from datetime import datetime, timezone, timedelta
import json
import traceback

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


def get_utcnow():
    """Get current UTC datetime in a cross-version compatible way"""
    if sys.version_info >= (3, 11):
        return datetime.now(timezone.utc)
    else:
        return datetime.utcnow()


def emit_event(event_type, message, user_id=None, details=None):
    """Emit system event"""
    timestamp = get_utcnow().isoformat()
    
    event = cloud_storage_pb2.SystemEvent(
        event_type=event_type,
        timestamp=timestamp,
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
                metadatas={'details': details} if details else {}
            )
            session.add(db_event)
            session.commit()
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


class PaymentServiceServicer(cloud_storage_pb2_grpc.PaymentServiceServicer):
    """Payment Service Implementation"""
   
    def _get_user_from_session_token(self, session_token, db_session):
        """Get user from session token"""
        from db.models import Session as DBSession, User
        db_session_obj = db_session.query(DBSession).filter_by(session_token=session_token).first()
        if not db_session_obj:
            return None
        user = db_session.query(User).filter_by(user_id=db_session_obj.user_id).first()
        return user
   
    def GetStorageTiers(self, request, context):
        """Get all available storage tiers"""
        try:
            from payment.payment_manager import payment_manager
           
            tiers = payment_manager.get_storage_tiers()
           
            tier_messages = []
            for tier in tiers:
                tier_messages.append(cloud_storage_pb2.StorageTier(
                    tier_id=tier['tier_id'],
                    name=tier['name'],
                    display_name=tier['display_name'],
                    storage_bytes=tier['storage_bytes'],
                    price_xaf=tier['price_xaf'],
                    description=tier.get('description', '')
                ))
           
            return cloud_storage_pb2.GetStorageTiersResponse(
                success=True,
                tiers=tier_messages
            )
       
        except Exception as e:
            print(f"[ERROR] Get tiers failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
   
    def InitiatePayment(self, request, context):
        """Initiate a payment for storage purchase"""
        try:
            session_token = request.session_token
            tier_id = request.tier_id
            provider = request.provider
            phone_number = request.phone_number
           
            # Validate session and get user
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
               
                user_id = user.user_id
                user_email = user.email
           
            print(f"[PAYMENT] User {user_email} initiating payment")
            print(f"[PAYMENT] Tier: {tier_id}, Provider: {provider}, Phone: {phone_number}")
           
            # Initiate payment
            from payment.payment_manager import payment_manager
            success, message, data = payment_manager.initiate_payment(
                user_id, tier_id, provider, phone_number
            )
           
            if success and data:
                emit_event(
                    'PAYMENT_INITIATED',
                    f'Payment initiated: {data["amount_xaf"]} XAF',
                    user_id=user_id,
                    details=data['payment_id']
                )
               
                return cloud_storage_pb2.InitiatePaymentResponse(
                    success=True,
                    message=message,
                    payment_id=data['payment_id'],
                    transaction_ref=data['transaction_ref'],
                    payment_url='', # Not used with Campay direct collection
                    amount_xaf=data['amount_xaf']
                )
            else:
                context.abort(grpc.StatusCode.FAILED_PRECONDITION, message)
       
        except Exception as e:
            print(f"[ERROR] Initiate payment failed: {e}")
            traceback.print_exc()
            context.abort(grpc.StatusCode.INTERNAL, str(e))
   
    def CheckPaymentStatus(self, request, context):
        """Check payment status"""
        try:
            session_token = request.session_token
            payment_id = request.payment_id
           
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
               
                user_id = user.user_id
           
            from payment.payment_manager import payment_manager
            success, status, data = payment_manager.check_payment_status(payment_id, user_id)
           
            if not success:
                context.abort(grpc.StatusCode.NOT_FOUND, status)
           
            if data and status == 'completed':
                emit_event(
                    'PAYMENT_COMPLETED',
                    f'Payment completed: {data["amount_xaf"]} XAF',
                    user_id=user_id,
                    details=payment_id
                )
           
            return cloud_storage_pb2.CheckPaymentStatusResponse(
                success=True,
                payment_id=payment_id,
                status=data['status'],
                message=data['message'],
                storage_added=data['storage_bytes']
            )
       
        except Exception as e:
            print(f"[ERROR] Check payment status failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
   
    def GetPaymentHistory(self, request, context):
        """Get payment history for user"""
        try:
            session_token = request.session_token
            limit = request.limit if request.limit > 0 else 50
           
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
               
                user_id = user.user_id
           
            from payment.payment_manager import payment_manager
            payments = payment_manager.get_payment_history(user_id, limit)
           
            payment_records = []
            for p in payments:
                payment_records.append(cloud_storage_pb2.PaymentRecord(
                    payment_id=p['payment_id'],
                    tier_name=p['tier_name'],
                    amount_xaf=p['amount_xaf'],
                    storage_bytes=p['storage_bytes'],
                    provider=p['provider'],
                    status=p['status'],
                    created_at=p['created_at'],
                    completed_at=p['completed_at'] or ''
                ))
           
            return cloud_storage_pb2.GetPaymentHistoryResponse(
                success=True,
                payments=payment_records
            )
       
        except Exception as e:
            print(f"[ERROR] Get payment history failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
   
    def CancelPayment(self, request, context):
        """Cancel a pending payment"""
        try:
            session_token = request.session_token
            payment_id = request.payment_id
           
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
               
                user_id = user.user_id
           
            from payment.payment_manager import payment_manager
            success, message = payment_manager.cancel_payment(payment_id, user_id)
           
            if success:
                emit_event(
                    'PAYMENT_CANCELLED',
                    f'Payment cancelled: {payment_id}',
                    user_id=user_id
                )
               
                return cloud_storage_pb2.CancelPaymentResponse(
                    success=True,
                    message=message
                )
            else:
                context.abort(grpc.StatusCode.FAILED_PRECONDITION, message)
       
        except Exception as e:
            print(f"[ERROR] Cancel payment failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
   
    def ProcessWebhook(self, request, context):
        """Process payment webhook from Campay"""
        try:
            external_ref = request.external_ref
            status = request.status
            raw_data = request.raw_data
           
            print(f"[WEBHOOK] Processing: ref={external_ref}, status={status}")
           
            data = json.loads(raw_data) if raw_data else {}
           
            from payment.payment_manager import payment_manager
            success, message = payment_manager.process_webhook(external_ref, status, data)
           
            return cloud_storage_pb2.WebhookResponse(
                success=success,
                message=message
            )
       
        except Exception as e:
            print(f"[ERROR] Webhook processing failed: {e}")
            traceback.print_exc()
            return cloud_storage_pb2.WebhookResponse(
                success=False,
                message=f"Webhook error: {str(e)}"
            )


class FileServiceServicer(cloud_storage_pb2_grpc.FileServiceServicer):
    """File Service Implementation"""
    
    def _get_user_from_session_token(self, session_token, db_session):
        """Get user from session token within the provided database session"""
        from db.models import Session as DBSession, User
        db_session_obj = db_session.query(DBSession).filter_by(session_token=session_token).first()
        if not db_session_obj:
            return None
        user = db_session.query(User).filter_by(user_id=db_session_obj.user_id).first()
        return user
    
    def _check_file_access(self, file_id, user_id, db_session):
        """
        Check if user has access to file (either owns it or has it shared with them)
        Returns: (has_access: bool, file_info: dict or None, is_owner: bool)
        """
        from db.models import File, FileShare, User
        
        file = db_session.query(File).filter_by(
            file_id=file_id,
            deleted_at=None
        ).first()
        
        if not file:
            print(f"[ACCESS_CHECK] File {file_id} not found or deleted")
            return False, None, False
        
        if file.user_id == user_id:
            print(f"[ACCESS_CHECK] User {user_id} is owner of file {file_id}")
            file_info = {
                'file_id': file.file_id,
                'filename': file.filename,
                'file_size': file.file_size,
                'mime_type': file.mime_type,
                'created_at': file.created_at.isoformat(),
                'modified_at': file.modified_at.isoformat(),
                'is_shared': file.is_shared
            }
            return True, file_info, True
        
        share = db_session.query(FileShare).filter_by(
            file_id=file_id,
            shared_with_user_id=user_id
        ).first()
        
        if share:
            if share.expires_at and share.expires_at < datetime.utcnow():
                print(f"[ACCESS_CHECK] Share expired for user {user_id} on file {file_id}")
                return False, None, False
            
            print(f"[ACCESS_CHECK] User {user_id} has shared access to file {file_id}")
            file_info = {
                'file_id': file.file_id,
                'filename': file.filename,
                'file_size': file.file_size,
                'mime_type': file.mime_type,
                'created_at': file.created_at.isoformat(),
                'modified_at': file.modified_at.isoformat(),
                'is_shared': file.is_shared
            }
            return True, file_info, False
        
        print(f"[ACCESS_CHECK] User {user_id} has no access to file {file_id}")
        return False, None, False
    
    def UploadFile(self, request_iterator, context):
        """Handle file upload with streaming"""
        try:
            first_request = next(request_iterator)
            
            if not first_request.HasField('metadata'):
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "First message must contain metadata")
            
            metadata = first_request.metadata
            session_token = metadata.session_token
            filename = metadata.filename
            file_size = metadata.file_size
            mime_type = metadata.mime_type
            parent_folder_id = metadata.parent_folder_id if metadata.parent_folder_id else None
            
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
                
                user_id = user.user_id
                user_email = user.email
                
                if not user_manager.check_storage_available(user_id, file_size):
                    context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, "Storage quota exceeded")
                
                print(f"[UPLOAD] Starting: {filename} ({file_size} bytes) for user {user_email}")
                
                file_data = b''
                for request in request_iterator:
                    if request.HasField('chunk_data'):
                        file_data += request.chunk_data
                
                print(f"[UPLOAD] Received {len(file_data)} bytes")
                
                success, message, file_id = file_manager.create_file(
                    user_id,
                    filename,
                    file_size,
                    mime_type,
                    parent_folder_id
                )
                
                if not success:
                    context.abort(grpc.StatusCode.INTERNAL, message)
                
                chunks = split_file_into_chunks(file_data, num_chunks=4)
                print(f"[UPLOAD] Split into {len(chunks)} chunks")
                
                node_mapping, error = chunk_distributor.select_nodes_for_chunks(len(chunks), replication_factor=1)
                if error:
                    context.abort(grpc.StatusCode.UNAVAILABLE, error)
                
                chunks_stored = 0
                for i, chunk_data in enumerate(chunks):
                    chunk_checksum = calculate_checksum(chunk_data)
                    node_info = node_mapping[i]
                    
                    success = self._store_chunk_on_node(
                        node_info['primary_host'],
                        node_info['primary_port'],
                        file_id,
                        i,
                        chunk_data,
                        chunk_checksum
                    )
                    
                    if success:
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
                
                user_manager.update_storage_usage(user_id, file_size)
                
                emit_event(
                    'FILE_UPLOADED',
                    f'File uploaded: {filename} ({file_size} bytes)',
                    user_id=user_id,
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
        
    def _delete_chunk_from_node(self, chunk_id, node_id, host, port):
        try:
            print(f"[DELETE_CHUNK] Attempting to delete chunk {chunk_id} from node {node_id} at {host}:{port}")
            channel = grpc.insecure_channel(f'{host}:{port}')
            stub = cloud_storage_pb2_grpc.NodeServiceStub(channel)
            response = stub.DeleteChunk(cloud_storage_pb2.DeleteChunkRequest(chunk_id=chunk_id))
            channel.close()
            if response.success:
                print(f"[DELETE] Successfully deleted chunk {chunk_id} from node {node_id}")
                return True
            else:
                print(f"[DELETE] Failed to delete chunk {chunk_id} from node {node_id}: {response.message}")
                return False
        except grpc.RpcError as e:
            print(f"[ERROR] gRPC error deleting chunk {chunk_id} from node {node_id}: {e.details()}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to delete chunk {chunk_id} from node {node_id}: {e}")
            traceback.print_exc()
            return False
            
    def DownloadFile(self, request, context):
        """Handle file download with streaming - supports shared files"""
        try:
            session_token = request.session_token
            file_id = request.file_id
            
            print(f"[DOWNLOAD] Request received for file: {file_id}")
            
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    print(f"[ERROR] Invalid session token: {session_token}")
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
                
                user_id = user.user_id
                user_email = user.email
                
                print(f"[DOWNLOAD] User {user_email} ({user_id}) requesting file {file_id}")
                
                has_access, file_info, is_owner = self._check_file_access(file_id, user_id, db_session)
                
                if not has_access:
                    print(f"[ERROR] User {user_id} has no access to file {file_id}")
                    context.abort(grpc.StatusCode.PERMISSION_DENIED, "Access denied: File not found or not shared with you")
                
                access_type = "owner" if is_owner else "shared"
                print(f"[DOWNLOAD] Starting: {file_info['filename']} for user {user_email} (access: {access_type})")
                
                chunks = file_manager.get_file_chunks(file_id)
                print(f"[DOWNLOAD] Found {len(chunks)} chunks for file {file_id}")
                
                yield cloud_storage_pb2.DownloadFileResponse(
                    file_info=cloud_storage_pb2.FileInfo(
                        filename=file_info['filename'],
                        file_size=file_info['file_size'],
                        mime_type=file_info['mime_type'],
                        total_chunks=len(chunks)
                    )
                )
                
                for chunk_info in chunks:
                    print(f"[DOWNLOAD] Retrieving chunk {chunk_info['chunk_index']}")
                    chunk_data = self._retrieve_chunk_from_node(chunk_info, file_id)
                    
                    if chunk_data:
                        print(f"[DOWNLOAD] Retrieved chunk {chunk_info['chunk_index']} ({len(chunk_data)} bytes)")
                        yield cloud_storage_pb2.DownloadFileResponse(
                            chunk_data=chunk_data
                        )
                    else:
                        print(f"[ERROR] Failed to retrieve chunk {chunk_info['chunk_index']}")
                        context.abort(grpc.StatusCode.DATA_LOSS, f"Failed to retrieve chunk {chunk_info['chunk_index']}")
                
                emit_event(
                    'FILE_DOWNLOADED',
                    f'File downloaded: {file_info["filename"]} ({access_type})',
                    user_id=user_id,
                    details=file_id
                )
                
                print(f"[DOWNLOAD] Complete: {file_info['filename']}")
        
        except Exception as e:
            print(f"[ERROR] Download failed: {e}")
            traceback.print_exc()
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def _retrieve_chunk_from_node(self, chunk_info, file_id):
        """Retrieve chunk from storage node"""
        try:
            chunk_index = chunk_info.get('chunk_index')
            if chunk_index is None:
                print(f"[CHUNK] Missing chunk_index")
                return None
            
            chunk_id = f"{file_id}_chunk_{chunk_index}"
            print(f"[CHUNK] Retrieving chunk {chunk_id}")
            
            node_info, error = chunk_distributor.get_node_for_retrieval(chunk_info['chunk_id'])
            if error:
                print(f"[CHUNK] Error: {error}")
                return None
            
            print(f"[CHUNK] Using node {node_info['host']}:{node_info['port']}")
            
            channel = grpc.insecure_channel(f"{node_info['host']}:{node_info['port']}")
            stub = cloud_storage_pb2_grpc.NodeServiceStub(channel)
            
            response = stub.RetrieveChunk(cloud_storage_pb2.RetrieveChunkRequest(
                chunk_id=chunk_id
            ))
            
            channel.close()
            
            if response.success:
                print(f"[CHUNK] Retrieved chunk {chunk_id} ({len(response.chunk_data)} bytes)")
                return response.chunk_data
            else:
                print(f"[CHUNK] Node error: {response.message}")
                return None
        
        except Exception as e:
            print(f"[ERROR] Retrieve chunk failed: {e}")
            traceback.print_exc()
            return None
    
    def ListFiles(self, request, context):
        """List files for user"""
        try:
            session_token = request.session_token
            folder_id = request.folder_id if request.folder_id else None
            include_deleted = request.include_deleted
            
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
                
                user_id = user.user_id
                
                success, files, folders = file_manager.list_files(user_id, folder_id, include_deleted)
                
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
        """Delete file - now properly deletes chunks from storage nodes"""
        try:
            session_token = request.session_token
            file_id = request.file_id
            permanent = request.permanent
            
            print(f"[gRPC] DeleteFile request: file_id={file_id}, permanent={permanent}")
            
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
                
                user_id = user.user_id
                
                print(f"[gRPC] User {user_id} deleting file {file_id}")
                
                success, message, chunk_info = file_manager.delete_file(file_id, user_id, permanent)
                
                if not success:
                    print(f"[gRPC] Delete failed: {message}")
                    context.abort(grpc.StatusCode.NOT_FOUND, message)
                
                print(f"[gRPC] File deleted from database: {message}")
                
                if permanent and chunk_info:
                    print(f"[gRPC] Deleting {len(chunk_info)} chunks from storage nodes...")
                    
                    deleted_count = 0
                    failed_count = 0
                    
                    for chunk in chunk_info:
                        chunk_id = chunk['chunk_id']
                        
                        if chunk['node_host'] and chunk['node_port']:
                            print(f"[gRPC] Deleting chunk {chunk_id} from primary node {chunk['node_id']}")
                            success = self._delete_chunk_from_node(
                                chunk_id,
                                chunk['node_id'],
                                chunk['node_host'],
                                chunk['node_port']
                            )
                            if success:
                                deleted_count += 1
                            else:
                                failed_count += 1
                        
                        for replica in chunk.get('replica_nodes', []):
                            if replica['node_host'] and replica['node_port']:
                                print(f"[gRPC] Deleting chunk {chunk_id} from replica node {replica['node_id']}")
                                self._delete_chunk_from_node(
                                    chunk_id,
                                    replica['node_id'],
                                    replica['node_host'],
                                    replica['node_port']
                                )
                    
                    print(f"[gRPC] Chunk cleanup complete: {deleted_count} deleted, {failed_count} failed")
                    
                    if failed_count > 0:
                        message += f" (Warning: {failed_count} chunks failed to delete from nodes)"
                else:
                    print(f"[gRPC] Soft delete - chunks remain on nodes")
                
                emit_event(
                    'FILE_DELETED',
                    f'File deleted: {file_id} (permanent={permanent})',
                    user_id=user_id
                )
                
                return cloud_storage_pb2.DeleteFileResponse(
                    success=True,
                    message=message
                )
        
        except Exception as e:
            print(f"[ERROR] Delete file failed: {e}")
            traceback.print_exc()
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def GetFileMetadata(self, request, context):
        """Get file metadata"""
        try:
            session_token = request.session_token
            file_id = request.file_id
            
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
                
                user_id = user.user_id
                
                file_info = file_manager.get_file(file_id, user_id)
                if not file_info:
                    context.abort(grpc.StatusCode.NOT_FOUND, "File not found")
                
                chunks = file_manager.get_file_chunks(file_id)
                
                return cloud_storage_pb2.FileMetadataResponse(
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
            print(f"[ERROR] Get metadata failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def CreateFolder(self, request, context):
        """Create folder"""
        try:
            session_token = request.session_token
            folder_name = request.folder_name
            parent_folder_id = request.parent_folder_id if request.parent_folder_id else None
            
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
                
                user_id = user.user_id
                
                success, message, folder_id = file_manager.create_folder(user_id, folder_name, parent_folder_id)
                
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
            
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
                
                user_id = user.user_id
                
                success, message, share_token = file_manager.share_file(
                    file_id, user_id, share_with_email, permission
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
            
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
                
                user_id = user.user_id
                
                success, shared_files = file_manager.get_shared_files(user_id)
                
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
    
    def _get_user_from_session_token(self, session_token, db_session):
        """Get user from session token within the provided database session"""
        from db.models import Session as DBSession, User
        db_session_obj = db_session.query(DBSession).filter_by(session_token=session_token).first()
        if not db_session_obj:
            return None
        user = db_session.query(User).filter_by(user_id=db_session_obj.user_id).first()
        return user
    
    def GetStorageInfo(self, request, context):
        """Get storage information"""
        try:
            session_token = request.session_token
            
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
                
                allocated = user.storage_allocated
                used = user.storage_used
                available = max(0, allocated - used)
                usage_percentage = (used / allocated * 100) if allocated > 0 else 0
                
                return cloud_storage_pb2.StorageInfoResponse(
                    success=True,
                    allocated_bytes=allocated,
                    used_bytes=used,
                    available_bytes=available,
                    usage_percentage=usage_percentage
                )
        
        except Exception as e:
            print(f"[ERROR] Get storage info failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def GetStorageUsage(self, request, context):
        """Get detailed storage usage"""
        try:
            session_token = request.session_token
            
            with get_db_session() as db_session:
                user = self._get_user_from_session_token(session_token, db_session)
                if not user:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")
                
                return cloud_storage_pb2.StorageUsageResponse(
                    success=True,
                    total_files=0,
                    total_folders=0
                )
        
        except Exception as e:
            print(f"[ERROR] Get storage usage failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))


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
    """Admin Service Implementation - FULLY FUNCTIONAL"""
    
    def GetSystemStatus(self, request, context):
        """Get system status with DYNAMIC storage"""
        try:
            if request.admin_key != ADMIN_KEY:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid admin key")
            
            stats = node_manager.get_storage_statistics()
            
            if not stats:
                context.abort(grpc.StatusCode.INTERNAL, "Failed to get statistics")
            
            with get_db_session() as session:
                from db.models import File, Chunk, User
                
                total_files = session.query(File).filter_by(deleted_at=None).count()
                total_chunks = session.query(Chunk).count()
                total_users = session.query(User).count()
            
            return cloud_storage_pb2.SystemStatusResponse(
                success=True,
                global_capacity_bytes=stats['global_capacity'],
                global_allocated_bytes=stats['user_allocated'],
                global_used_bytes=stats['global_used'],
                total_users=total_users,
                total_nodes=stats['total_nodes'],
                online_nodes=stats['online_nodes'],
                total_files=total_files,
                total_chunks=total_chunks,
                system_health=100.0 if stats['online_nodes'] > 0 else 0.0
            )
        
        except Exception as e:
            print(f"[ERROR] Get system status failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def ListAllUsers(self, request, context):
        """List all users - NOW IMPLEMENTED"""
        try:
            if request.admin_key != ADMIN_KEY:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid admin key")
            
            with get_db_session() as session:
                from db.models import User, File
                
                users = session.query(User).all()
                
                user_list = []
                for user in users:
                    file_count = session.query(File).filter_by(
                        user_id=user.user_id,
                        deleted_at=None
                    ).count()
                    
                    user_list.append(cloud_storage_pb2.UserInfo(
                        user_id=user.user_id,
                        email=user.email,
                        name=user.name,
                        storage_allocated=user.storage_allocated,
                        storage_used=user.storage_used,
                        created_at=user.created_at.isoformat(),
                        last_login=user.last_login.isoformat() if user.last_login else "",
                        file_count=file_count
                    ))
                
                return cloud_storage_pb2.ListUsersResponse(
                    success=True,
                    users=user_list
                )
        
        except Exception as e:
            print(f"[ERROR] List users failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    def ListAllNodes(self, request, context):
        try:
            if request.admin_key != ADMIN_KEY:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid admin key")
            
            with get_db_session() as session:
                from db.models import StorageNode, Chunk
                
                nodes = session.query(StorageNode).all()
                
                online_threshold = get_utcnow() - timedelta(minutes=2)
                
                node_list = []
                for node in nodes:
                    chunk_count = session.query(Chunk).filter_by(
                        primary_node_id=node.node_id
                    ).count()
                    
                    if node.last_heartbeat:
                        if node.last_heartbeat.tzinfo is None:
                            threshold_naive = online_threshold.replace(tzinfo=None)
                            is_online = node.last_heartbeat > threshold_naive
                        else:
                            is_online = node.last_heartbeat > online_threshold
                    else:
                        is_online = False
                    
                    status = 'online' if is_online else 'offline'
                    
                    node_list.append(cloud_storage_pb2.NodeInfo(
                        node_id=node.node_id,
                        host=node.host,
                        port=node.port,
                        storage_capacity=node.storage_capacity,
                        storage_used=node.storage_used,
                        status=status,
                        last_heartbeat=node.last_heartbeat.isoformat() if node.last_heartbeat else "",
                        chunk_count=chunk_count,
                        health_score=node.health_score
                    ))
                
                return cloud_storage_pb2.ListNodesResponse(
                    success=True,
                    nodes=node_list
                )
        
        except Exception as e:
            print(f"[ERROR] List nodes failed: {e}")
            traceback.print_exc()
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        
    def GetUserDetails(self, request, context):
        """Get detailed user information - NOW IMPLEMENTED"""
        try:
            if request.admin_key != ADMIN_KEY:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid admin key")
                
            user_id = request.user_id
            
            with get_db_session() as session:
                from db.models import User, File
                
                user = session.query(User).filter_by(user_id=user_id).first()
                
                if not user:
                    context.abort(grpc.StatusCode.NOT_FOUND, "User not found")
                
                files = session.query(File).filter_by(
                    user_id=user_id,
                    deleted_at=None
                ).order_by(File.created_at.desc()).all()
                
                file_entries = []
                for file in files:
                    file_entries.append(cloud_storage_pb2.FileEntry(
                        file_id=file.file_id,
                        filename=file.filename,
                        file_size=file.file_size,
                        mime_type=file.mime_type,
                        created_at=file.created_at.isoformat(),
                        modified_at=file.modified_at.isoformat(),
                        is_shared=file.is_shared
                    ))
                
                return cloud_storage_pb2.UserDetailsResponse(
                    success=True,
                    user=cloud_storage_pb2.UserInfo(
                        user_id=user.user_id,
                        email=user.email,
                        name=user.name,
                        storage_allocated=user.storage_allocated,
                        storage_used=user.storage_used,
                        created_at=user.created_at.isoformat(),
                        last_login=user.last_login.isoformat() if user.last_login else "",
                        file_count=len(files)
                    ),
                    files=file_entries
                )
            
        except Exception as e:
            print(f"[ERROR] Get user details failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        
    def StreamSystemEvents(self, request, context):
        """Stream real-time system events"""
        try:
            if request.admin_key != ADMIN_KEY:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid admin key")
            
            print("[ADMIN] Event streaming started")
            
            last_keepalive = datetime.now()
            keepalive_interval = timedelta(seconds=60)
            
            while context.is_active():
                try:
                    event = event_queue.get(timeout=2.0)
                    print(f"[ADMIN] Streaming event: {event.event_type}")
                    yield event
                    last_keepalive = datetime.now()
                    
                except queue.Empty:
                    now = datetime.now()
                    if now - last_keepalive > keepalive_interval:
                        keepalive = cloud_storage_pb2.SystemEvent(
                            event_type='KEEPALIVE',
                            timestamp=now.isoformat(),
                            message='Connection active',
                            user_id='',
                            details=''
                        )
                        yield keepalive
                        last_keepalive = now
                    continue
                    
                except Exception as e:
                    print(f"[ERROR] Error reading from event queue: {e}")
                    break
            
            print("[ADMIN] Event streaming ended")
        
        except Exception as e:
            print(f"[ERROR] Event stream failed: {e}")
            traceback.print_exc()
    
    def UpdateGlobalStorage(self, request, context):
        """Update global storage capacity"""
        try:
            if request.admin_key != ADMIN_KEY:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid admin key")
            
            stats = node_manager.get_storage_statistics()
            
            return cloud_storage_pb2.UpdateStorageResponse(
                success=True,
                message="Storage is managed dynamically by nodes",
                old_capacity_bytes=stats['global_capacity'],
                new_capacity_bytes=stats['global_capacity']
            )
        
        except Exception as e:
            print(f"[ERROR] Update storage failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def GetPaymentStats(self, request, context):
        """Get payment statistics (admin)"""
        try:
            if request.admin_key != ADMIN_KEY:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid admin key")
           
            from payment.payment_manager import payment_manager
            stats = payment_manager.get_payment_stats()
           
            return cloud_storage_pb2.PaymentStatsResponse(
                success=True,
                total_payments=stats.get('total_payments', 0),
                completed_payments=stats.get('completed_payments', 0),
                pending_payments=stats.get('pending_payments', 0),
                failed_payments=stats.get('failed_payments', 0),
                total_revenue_xaf=stats.get('total_revenue_xaf', 0),
                total_storage_sold_bytes=stats.get('total_storage_sold_bytes', 0)
            )
       
        except Exception as e:
            print(f"[ERROR] Get payment stats failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
   
    def GetAllPayments(self, request, context):
        """Get all payments (admin)"""
        try:
            if request.admin_key != ADMIN_KEY:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid admin key")
           
            limit = request.limit if request.limit > 0 else 100
            status_filter = request.status_filter if request.status_filter else None
           
            from payment.payment_manager import payment_manager
            payments = payment_manager.get_all_payments(limit, status_filter)
           
            payment_records = []
            for p in payments:
                payment_records.append(cloud_storage_pb2.AdminPaymentRecord(
                    payment_id=p['payment_id'],
                    user_email=p['user_email'],
                    tier_name=p['tier_name'],
                    amount_xaf=p['amount_xaf'],
                    storage_bytes=p['storage_bytes'],
                    provider=p['provider'],
                    phone_number=p['phone_number'],
                    status=p['status'],
                    transaction_ref=p['transaction_ref'],
                    created_at=p['created_at'],
                    completed_at=p['completed_at'] or ''
                ))
           
            return cloud_storage_pb2.GetAllPaymentsResponse(
                success=True,
                payments=payment_records
            )
       
        except Exception as e:
            print(f"[ERROR] Get all payments failed: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))


def serve():
    """Start the cloud server"""
    print("=" * 70)
    print("CLOUD STORAGE PLATFORM - SERVER (DYNAMIC STORAGE + PAYMENT SYSTEM)")
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
    
    # ADD THIS LINE - Payment Service Registration
    cloud_storage_pb2_grpc.add_PaymentServiceServicer_to_server(
        PaymentServiceServicer(), server
    )
    
    # Start server
    port = os.getenv('GRPC_SERVER_PORT', '50051')
    server.add_insecure_port(f'[::]:{port}')
    
    print(f"Server listening on port {port}")
    print(f"Admin Key: {ADMIN_KEY}")
    print("=" * 70)
    print("\n[READY] Cloud server with Payment System is ready to accept connections")
    print("[INFO] Global storage grows automatically as nodes register!\n")
    
    server.start()
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down cloud server...")
        server.stop(0)


if __name__ == '__main__':
    serve()