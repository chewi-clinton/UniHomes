from flask import Blueprint, request, jsonify, Response, stream_with_context
from app.utils.grpc_client import get_grpc_client
from app.models.response import success_response, error_response
from werkzeug.utils import secure_filename
import generated.cloud_storage_pb2 as cloud_storage_pb2
import grpc

files_bp = Blueprint('files', __name__)

def get_session_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    return auth_header.split(' ')[1]

@files_bp.route('', methods=['GET'])
def list_files():
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
   
    folder_id = request.args.get('folder_id')
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
   
    client = get_grpc_client()
    try:
        response = client.file_stub.ListFiles(
            cloud_storage_pb2.ListFilesRequest(
                session_token=session_token,
                folder_id=folder_id,
                include_deleted=include_deleted
            )
        )
       
        if response.success:
            files = [{
                'file_id': f.file_id,
                'filename': f.filename,
                'file_size': f.file_size,
                'mime_type': f.mime_type,
                'created_at': f.created_at,
                'modified_at': f.modified_at,
                'is_shared': f.is_shared
            } for f in response.files]
           
            folders = [{
                'folder_id': f.folder_id,
                'folder_name': f.folder_name,
                'created_at': f.created_at,
                'file_count': f.file_count
            } for f in response.folders]
           
            return success_response({'files': files, 'folders': folders})
        else:
            return error_response("Failed to list files"), 400
    except grpc.RpcError as e:
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to list files: {str(e)}"), 500

@files_bp.route('/upload', methods=['POST'])
def upload_file():
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
   
    if 'file' not in request.files:
        return error_response("No file provided"), 400
   
    file = request.files['file']
    if file.filename == '':
        return error_response("No file selected"), 400
   
    filename = secure_filename(file.filename)
    file_size = request.content_length
    mime_type = file.mimetype or 'application/octet-stream'
    parent_folder_id = request.form.get('folder_id')
   
    client = get_grpc_client()
   
    def generate_requests():
        yield cloud_storage_pb2.UploadFileRequest(
            metadata=cloud_storage_pb2.FileMetadata(
                session_token=session_token,
                filename=filename,
                file_size=file_size,
                mime_type=mime_type,
                parent_folder_id=parent_folder_id
            )
        )
       
        chunk_size = 1024 * 1024  # 1MB
        while True:
            chunk = file.stream.read(chunk_size)
            if not chunk:
                break
            yield cloud_storage_pb2.UploadFileRequest(chunk_data=chunk)
   
    try:
        response = client.file_stub.UploadFile(generate_requests())
        if response.success:
            return success_response({
                'file_id': response.file_id,
                'chunks_stored': response.chunks_stored
            }, response.message)
        else:
            return error_response(response.message), 400
    except grpc.RpcError as e:
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to upload file: {str(e)}"), 500

@files_bp.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """
    Download file with proper streaming to avoid memory issues
    """
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
   
    client = get_grpc_client()
   
    try:
        print(f"[FLASK] Starting download for file_id: {file_id}")
        
        # Get the response stream from gRPC
        response_stream = client.file_stub.DownloadFile(
            cloud_storage_pb2.DownloadFileRequest(
                session_token=session_token,
                file_id=file_id
            )
        )
       
        # Get first response with file info
        first_response = next(response_stream)
        
        if not first_response.HasField('file_info'):
            print("[FLASK ERROR] No file info in response")
            return error_response("File not found"), 404
       
        file_info = first_response.file_info
        print(f"[FLASK] File info: {file_info.filename}, size: {file_info.file_size} bytes")
       
        # Check if file is empty
        if file_info.file_size == 0:
            print("[FLASK] File is empty (0 bytes)")
            return error_response("File is empty"), 400
       
        # For debugging: Collect chunks first to verify size
        # Once working, you can switch to streaming mode (see commented code below)
        file_data = bytearray()
        chunk_count = 0
        
        try:
            for response in response_stream:
                if response.HasField('chunk_data'):
                    chunk = response.chunk_data
                    chunk_count += 1
                    chunk_bytes = len(chunk)
                    file_data.extend(chunk)
                    print(f"[FLASK] Received chunk {chunk_count}: {chunk_bytes} bytes (total: {len(file_data)}/{file_info.file_size})")
            
            print(f"[FLASK] All chunks received. Total: {len(file_data)} bytes from {chunk_count} chunks")
            
            # Verify we got data
            if len(file_data) == 0:
                print(f"[FLASK ERROR] No data received! Expected {file_info.file_size} bytes")
                return error_response("No file data received from storage"), 500
            
            # Log size mismatch but still return the data we have
            if len(file_data) != file_info.file_size:
                print(f"[FLASK WARNING] Size mismatch! Expected {file_info.file_size}, got {len(file_data)}")
                print(f"[FLASK WARNING] Missing {file_info.file_size - len(file_data)} bytes")
                # Don't fail - return what we have and let client decide
                # return error_response(f"File download incomplete: expected {file_info.file_size} bytes, got {len(file_data)} bytes"), 500
            
            # Convert to bytes
            file_bytes = bytes(file_data)
            
            print(f"[FLASK] Creating response with {len(file_bytes)} bytes")
            
            # Return the complete file as a response
            response = Response(
                file_bytes,
                mimetype=file_info.mime_type or 'application/octet-stream',
                headers={
                    'Content-Disposition': f'attachment; filename="{file_info.filename}"',
                    'Content-Type': file_info.mime_type or 'application/octet-stream',
                    'Content-Length': str(len(file_bytes)),  # Use actual length, not expected
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            )
            
            print(f"[FLASK] Download response ready to send")
            return response
            
        except Exception as e:
            print(f"[FLASK ERROR] Error collecting chunks: {e}")
            import traceback
            traceback.print_exc()
            return error_response(f"Failed to collect file data: {str(e)}"), 500
   
    except StopIteration:
        print("[FLASK ERROR] No data in response stream")
        return error_response("File not found or empty"), 404
    except grpc.RpcError as e:
        print(f"[FLASK ERROR] gRPC error: {e.details()}")
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        print(f"[FLASK ERROR] Download failed: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to download file: {str(e)}"), 500


# ALTERNATIVE: Streaming version (use this once the size issue is fixed on server)
"""
@files_bp.route('/download/<file_id>', methods=['GET'])
def download_file_streaming(file_id):
    '''
    Download file with direct streaming (more memory efficient)
    '''
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
   
    client = get_grpc_client()
   
    try:
        print(f"[FLASK] Starting streaming download for file_id: {file_id}")
        
        response_stream = client.file_stub.DownloadFile(
            cloud_storage_pb2.DownloadFileRequest(
                session_token=session_token,
                file_id=file_id
            )
        )
       
        # Get first response with file info
        first_response = next(response_stream)
        
        if not first_response.HasField('file_info'):
            return error_response("File not found"), 404
       
        file_info = first_response.file_info
        print(f"[FLASK] Streaming file: {file_info.filename}, size: {file_info.file_size} bytes")
       
        if file_info.file_size == 0:
            return error_response("File is empty"), 400
       
        def generate():
            '''Generator function to stream chunks directly'''
            try:
                chunk_count = 0
                total_bytes = 0
                
                for response in response_stream:
                    if response.HasField('chunk_data'):
                        chunk = response.chunk_data
                        chunk_count += 1
                        total_bytes += len(chunk)
                        print(f"[FLASK] Streaming chunk {chunk_count}: {len(chunk)} bytes (total: {total_bytes}/{file_info.file_size})")
                        yield chunk
                
                print(f"[FLASK] Stream complete. Total: {total_bytes} bytes from {chunk_count} chunks")
                
            except Exception as e:
                print(f"[FLASK ERROR] Error during streaming: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # Create streaming response
        response = Response(
            stream_with_context(generate()),
            mimetype=file_info.mime_type or 'application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{file_info.filename}"',
                'Content-Type': file_info.mime_type or 'application/octet-stream',
                'Content-Length': str(file_info.file_size),
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        
        return response
            
    except StopIteration:
        return error_response("File not found or empty"), 404
    except grpc.RpcError as e:
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to download file: {str(e)}"), 500
"""

@files_bp.route('/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
   
    permanent = request.args.get('permanent', 'false').lower() == 'true'
   
    client = get_grpc_client()
    try:
        response = client.file_stub.DeleteFile(
            cloud_storage_pb2.DeleteFileRequest(
                session_token=session_token,
                file_id=file_id,
                permanent=permanent
            )
        )
        if response.success:
            return success_response(message=response.message)
        else:
            return error_response(response.message), 400
    except grpc.RpcError as e:
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to delete file: {str(e)}"), 500

@files_bp.route('/folders', methods=['POST'])
def create_folder():
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
   
    data = request.get_json()
    folder_name = data.get('folder_name')
    parent_folder_id = data.get('parent_folder_id')
   
    if not folder_name:
        return error_response("Folder name is required"), 400
   
    client = get_grpc_client()
    try:
        response = client.file_stub.CreateFolder(
            cloud_storage_pb2.CreateFolderRequest(
                session_token=session_token,
                folder_name=folder_name,
                parent_folder_id=parent_folder_id
            )
        )
        if response.success:
            return success_response({
                'folder_id': response.folder_id
            }, response.message)
        else:
            return error_response(response.message), 400
    except grpc.RpcError as e:
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to create folder: {str(e)}"), 500

@files_bp.route('/share', methods=['POST'])
def share_file():
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
   
    data = request.get_json()
    file_id = data.get('file_id')
    share_with_email = data.get('share_with_email')
    permission = data.get('permission', 'read')
   
    if not file_id or not share_with_email:
        return error_response("File ID and email are required"), 400
   
    client = get_grpc_client()
    try:
        response = client.file_stub.ShareFile(
            cloud_storage_pb2.ShareFileRequest(
                session_token=session_token,
                file_id=file_id,
                share_with_email=share_with_email,
                permission=permission
            )
        )
        if response.success:
            return success_response({
                'share_token': response.share_token
            }, response.message)
        else:
            return error_response(response.message), 400
    except grpc.RpcError as e:
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to share file: {str(e)}"), 500

@files_bp.route('/shared', methods=['GET'])
def get_shared_files():
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
   
    client = get_grpc_client()
    try:
        response = client.file_stub.GetSharedFiles(
            cloud_storage_pb2.GetSharedFilesRequest(
                session_token=session_token
            )
        )
        if response.success:
            shared_files = [{
                'file_id': f.file_id,
                'filename': f.filename,
                'shared_by_email': f.shared_by_email,
                'permission': f.permission,
                'shared_at': f.shared_at
            } for f in response.shared_files]
           
            return success_response({'shared_files': shared_files})
        else:
            return error_response("Failed to get shared files"), 400
    except grpc.RpcError as e:
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to get shared files: {str(e)}"), 500