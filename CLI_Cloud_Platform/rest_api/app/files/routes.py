from flask import Blueprint, request, jsonify, Response
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
    
    # Create a generator that yields the metadata and then the file chunks
    def generate_requests():
        # First, send the metadata
        yield cloud_storage_pb2.UploadFileRequest(
            metadata=cloud_storage_pb2.FileMetadata(
                session_token=session_token,
                filename=filename,
                file_size=file_size,
                mime_type=mime_type,
                parent_folder_id=parent_folder_id
            )
        )
        
        # Then, send the file in chunks
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
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
    
    client = get_grpc_client()
    
    try:
        # First, get the file info
        response_stream = client.file_stub.DownloadFile(
            cloud_storage_pb2.DownloadFileRequest(
                session_token=session_token,
                file_id=file_id
            )
        )
        
        # The first message should be the file info
        file_info = None
        for response in response_stream:
            if response.HasField('file_info'):
                file_info = response.file_info
                break
        
        if not file_info:
            return error_response("File not found"), 404
        
        # Now, create a generator that yields the file data
        def generate():
            # We already read the first message (file_info), so we continue with the rest
            for response in response_stream:
                if response.HasField('chunk_data'):
                    yield response.chunk_data
        
        return Response(
            generate(),
            headers={
                'Content-Disposition': f'attachment; filename="{file_info.filename}"',
                'Content-Type': file_info.mime_type,
                'Content-Length': str(file_info.file_size)
            }
        )
    
    except grpc.RpcError as e:
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to download file: {str(e)}"), 500

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