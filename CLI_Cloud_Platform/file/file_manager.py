"""
File Manager - Handles file operations and metadata
"""
import hashlib
from datetime import datetime
from db.models import File, Chunk, Folder, FileShare, User
from db.database import get_db_session
import mimetypes

class FileManager:
    def __init__(self):
        pass
    
    def create_file(self, user_id, filename, file_size, mime_type=None, parent_folder_id=None):
        """Create file metadata"""
        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(filename)
        
        try:
            with get_db_session() as session:
                file = File(
                    user_id=user_id,
                    filename=filename,
                    file_size=file_size,
                    mime_type=mime_type or 'application/octet-stream',
                    parent_folder_id=parent_folder_id
                )
                session.add(file)
                session.flush()
                
                file_id = file.file_id
                print(f"[FILE] Created file metadata: {filename} ({file_id})")
                return True, "File created", file_id
        
        except Exception as e:
            print(f"[ERROR] Failed to create file: {e}")
            return False, str(e), None
    
    def add_chunk(self, file_id, chunk_index, chunk_size, checksum, primary_node_id, replica_nodes=None):
        """Add chunk metadata to file"""
        try:
            with get_db_session() as session:
                chunk = Chunk(
                    file_id=file_id,
                    chunk_index=chunk_index,
                    size=chunk_size,
                    checksum=checksum,
                    primary_node_id=primary_node_id,
                    replica_nodes=replica_nodes or []
                )
                session.add(chunk)
                session.flush()
                
                chunk_id = chunk.chunk_id
                return True, "Chunk added", chunk_id
        
        except Exception as e:
            print(f"[ERROR] Failed to add chunk: {e}")
            return False, str(e), None
    
    def get_file(self, file_id, user_id=None):
        """Get file metadata"""
        try:
            with get_db_session() as session:
                query = session.query(File).filter_by(file_id=file_id, deleted_at=None)
                if user_id:
                    query = query.filter_by(user_id=user_id)
                
                file = query.first()
                if not file:
                    return None
                
                return {
                    'file_id': file.file_id,
                    'filename': file.filename,
                    'file_size': file.file_size,
                    'mime_type': file.mime_type,
                    'created_at': file.created_at.isoformat(),
                    'modified_at': file.modified_at.isoformat(),
                    'is_shared': file.is_shared,
                    'user_id': file.user_id
                }
        
        except Exception as e:
            print(f"[ERROR] Failed to get file: {e}")
            return None
    
    def list_files(self, user_id, folder_id=None, include_deleted=False):
        """List files for user"""
        try:
            with get_db_session() as session:
                # Get files
                query = session.query(File).filter_by(user_id=user_id)
                
                if folder_id:
                    query = query.filter_by(parent_folder_id=folder_id)
                else:
                    query = query.filter_by(parent_folder_id=None)
                
                if not include_deleted:
                    query = query.filter_by(deleted_at=None)
                
                files = query.all()
                
                # Get folders
                folder_query = session.query(Folder).filter_by(user_id=user_id)
                if folder_id:
                    folder_query = folder_query.filter_by(parent_folder_id=folder_id)
                else:
                    folder_query = folder_query.filter_by(parent_folder_id=None)
                
                folders = folder_query.all()
                
                file_list = []
                for file in files:
                    file_list.append({
                        'file_id': file.file_id,
                        'filename': file.filename,
                        'file_size': file.file_size,
                        'mime_type': file.mime_type,
                        'created_at': file.created_at.isoformat(),
                        'modified_at': file.modified_at.isoformat(),
                        'is_shared': file.is_shared
                    })
                
                folder_list = []
                for folder in folders:
                    file_count = session.query(File).filter_by(
                        parent_folder_id=folder.folder_id,
                        deleted_at=None
                    ).count()
                    
                    folder_list.append({
                        'folder_id': folder.folder_id,
                        'folder_name': folder.folder_name,
                        'created_at': folder.created_at.isoformat(),
                        'file_count': file_count
                    })
                
                return True, file_list, folder_list
        
        except Exception as e:
            print(f"[ERROR] Failed to list files: {e}")
            return False, [], []
    
    def delete_file(self, file_id, user_id, permanent=False):
        """
        Delete a file (soft or permanent)
        Returns: (success: bool, message: str, chunk_info: list)
        
        chunk_info contains: [{'chunk_id': str, 'node_id': str, 'node_host': str, 'node_port': int, 'replica_nodes': list}, ...]
        """
        try:
            with get_db_session() as session:
                # Get file
                file = session.query(File).filter_by(
                    file_id=file_id,
                    user_id=user_id
                ).first()
                
                if not file:
                    return False, "File not found", []
                
                # Check if already deleted
                if file.deleted_at and not permanent:
                    return False, "File already deleted", []
                
                file_size = file.file_size
                
                # Get chunk information with node details BEFORE deletion
                chunks = session.query(Chunk).filter_by(file_id=file_id).all()
                chunk_info = []
                
                for chunk in chunks:
                    from db.models import StorageNode
                    primary_node = session.query(StorageNode).filter_by(
                        node_id=chunk.primary_node_id
                    ).first()
                    
                    chunk_data = {
                        'chunk_id': chunk.chunk_id,
                        'node_id': chunk.primary_node_id,
                        'node_host': primary_node.host if primary_node else None,
                        'node_port': primary_node.port if primary_node else None,
                        'replica_nodes': []
                    }
                    
                    # Get replica node information
                    if chunk.replica_nodes:
                        for replica_id in chunk.replica_nodes:
                            replica_node = session.query(StorageNode).filter_by(
                                node_id=replica_id
                            ).first()
                            if replica_node:
                                chunk_data['replica_nodes'].append({
                                    'node_id': replica_id,
                                    'node_host': replica_node.host,
                                    'node_port': replica_node.port
                                })
                    
                    chunk_info.append(chunk_data)
                
                if permanent:
                    # PERMANENT DELETE
                    print(f"[FILE] Permanently deleting: {file.filename} ({file_size} bytes)")
                    print(f"[FILE] Chunks to delete: {len(chunk_info)}")
                    
                    # Delete chunks from database
                    session.query(Chunk).filter_by(file_id=file_id).delete()
                    
                    # Delete file shares
                    session.query(FileShare).filter_by(file_id=file_id).delete()
                    
                    # Delete file from database
                    session.delete(file)
                    
                    # CRITICAL: Free up user's storage quota
                    user = session.query(User).filter_by(user_id=user_id).first()
                    if user:
                        old_usage = user.storage_used
                        user.storage_used = max(0, user.storage_used - file_size)
                        print(f"[STORAGE] Freed {file_size} bytes for user {user_id}")
                        print(f"[STORAGE] User storage: {old_usage} -> {user.storage_used} (allocated: {user.storage_allocated})")
                    
                    session.commit()
                    
                    return True, f"File permanently deleted: {file.filename}", chunk_info
                
                else:
                    # SOFT DELETE
                    print(f"[FILE] Soft deleted: {file.filename}")
                    file.deleted_at = datetime.utcnow()
                    session.commit()
                    
                    # Don't return chunk info for soft delete (chunks stay on nodes)
                    return True, f"File moved to trash: {file.filename}", []
        
        except Exception as e:
            print(f"[ERROR] Delete file failed: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e), []

    def restore_file(self, file_id, user_id):
        """
        Restore a soft-deleted file
        Returns: (success: bool, message: str)
        """
        try:
            with get_db_session() as session:
                file = session.query(File).filter_by(
                    file_id=file_id,
                    user_id=user_id
                ).first()
                
                if not file:
                    return False, "File not found"
                
                if not file.deleted_at:
                    return False, "File is not deleted"
                
                # Restore file
                file.deleted_at = None
                session.commit()
                
                print(f"[FILE] Restored: {file.filename}")
                return True, f"File restored: {file.filename}"
        
        except Exception as e:
            print(f"[ERROR] Restore file failed: {e}")
            return False, str(e)

    def empty_trash(self, user_id):
        """
        Permanently delete all soft-deleted files for a user
        Returns: (success: bool, message: str, total_freed: int, all_chunk_info: list)
        """
        try:
            with get_db_session() as session:
                # Get all soft-deleted files
                deleted_files = session.query(File).filter(
                    File.user_id == user_id,
                    File.deleted_at.isnot(None)
                ).all()
                
                if not deleted_files:
                    return True, "Trash is already empty", 0, []
                
                total_size = sum(f.file_size for f in deleted_files)
                file_count = len(deleted_files)
                all_chunk_info = []
                
                # Collect chunk info and delete all chunks and files
                for file in deleted_files:
                    # Get chunks with node info
                    chunks = session.query(Chunk).filter_by(file_id=file.file_id).all()
                    
                    for chunk in chunks:
                        from db.models import StorageNode
                        primary_node = session.query(StorageNode).filter_by(
                            node_id=chunk.primary_node_id
                        ).first()
                        
                        chunk_data = {
                            'chunk_id': chunk.chunk_id,
                            'node_id': chunk.primary_node_id,
                            'node_host': primary_node.host if primary_node else None,
                            'node_port': primary_node.port if primary_node else None,
                            'replica_nodes': []
                        }
                        
                        if chunk.replica_nodes:
                            for replica_id in chunk.replica_nodes:
                                replica_node = session.query(StorageNode).filter_by(
                                    node_id=replica_id
                                ).first()
                                if replica_node:
                                    chunk_data['replica_nodes'].append({
                                        'node_id': replica_id,
                                        'node_host': replica_node.host,
                                        'node_port': replica_node.port
                                    })
                        
                        all_chunk_info.append(chunk_data)
                    
                    # Delete chunks
                    session.query(Chunk).filter_by(file_id=file.file_id).delete()
                    # Delete shares
                    session.query(FileShare).filter_by(file_id=file.file_id).delete()
                    # Delete file
                    session.delete(file)
                
                # Free up storage quota
                user = session.query(User).filter_by(user_id=user_id).first()
                if user:
                    user.storage_used = max(0, user.storage_used - total_size)
                    print(f"[STORAGE] Emptied trash: freed {total_size} bytes for user {user_id}")
                
                session.commit()
                
                return True, f"Permanently deleted {file_count} files", total_size, all_chunk_info
        
        except Exception as e:
            print(f"[ERROR] Empty trash failed: {e}")
            return False, str(e), 0, []
    
    def get_file_chunks(self, file_id):
        """Get all chunks for a file"""
        try:
            with get_db_session() as session:
                chunks = session.query(Chunk).filter_by(file_id=file_id).order_by(Chunk.chunk_index).all()
                
                chunk_list = []
                for chunk in chunks:
                    chunk_list.append({
                        'chunk_id': chunk.chunk_id,
                        'chunk_index': chunk.chunk_index,
                        'size': chunk.size,
                        'checksum': chunk.checksum,
                        'primary_node_id': chunk.primary_node_id,
                        'replica_nodes': chunk.replica_nodes or []
                    })
                
                return chunk_list
        
        except Exception as e:
            print(f"[ERROR] Failed to get chunks: {e}")
            return []
    
    def create_folder(self, user_id, folder_name, parent_folder_id=None):
        """Create a new folder"""
        try:
            with get_db_session() as session:
                folder = Folder(
                    user_id=user_id,
                    folder_name=folder_name,
                    parent_folder_id=parent_folder_id
                )
                session.add(folder)
                session.flush()
                
                folder_id = folder.folder_id
                print(f"[FILE] Created folder: {folder_name}")
                return True, "Folder created", folder_id
        
        except Exception as e:
            print(f"[ERROR] Failed to create folder: {e}")
            return False, str(e), None
    
    def share_file(self, file_id, user_id, share_with_email, permission='read'):
        """Share file with another user"""
        try:
            with get_db_session() as session:
                # Check if file exists and belongs to user
                file = session.query(File).filter_by(file_id=file_id, user_id=user_id).first()
                if not file:
                    return False, "File not found", None
                
                # Get target user
                target_user = session.query(User).filter_by(email=share_with_email).first()
                if not target_user:
                    return False, "User not found", None
                
                # Create share
                import secrets
                share_token = secrets.token_urlsafe(16)
                
                share = FileShare(
                    file_id=file_id,
                    shared_by_user_id=user_id,
                    shared_with_user_id=target_user.user_id,
                    share_token=share_token,
                    permission=permission
                )
                session.add(share)
                
                # Mark file as shared
                file.is_shared = True
                
                print(f"[FILE] Shared file {file.filename} with {share_with_email}")
                return True, "File shared successfully", share_token
        
        except Exception as e:
            print(f"[ERROR] Failed to share file: {e}")
            return False, str(e), None
    
    def get_shared_files(self, user_id):
        """Get files shared with user"""
        try:
            with get_db_session() as session:
                shares = session.query(FileShare).filter_by(shared_with_user_id=user_id).all()
                
                shared_files = []
                for share in shares:
                    file = session.query(File).filter_by(file_id=share.file_id).first()
                    shared_by = session.query(User).filter_by(user_id=share.shared_by_user_id).first()
                    
                    if file and shared_by:
                        shared_files.append({
                            'file_id': file.file_id,
                            'filename': file.filename,
                            'shared_by_email': shared_by.email,
                            'permission': share.permission,
                            'shared_at': share.created_at.isoformat()
                        })
                
                return True, shared_files
        
        except Exception as e:
            print(f"[ERROR] Failed to get shared files: {e}")
            return False, []
    
    def calculate_checksum(self, data):
        """Calculate SHA256 checksum"""
        return hashlib.sha256(data).hexdigest()