"""
Helper utilities
"""
import hashlib

def calculate_checksum(data):
    """Calculate SHA256 checksum"""
    return hashlib.sha256(data).hexdigest()

def format_bytes(bytes_value):
    """Format bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def split_file_into_chunks(file_data, num_chunks=4):
    """Split file data into chunks"""
    chunk_size = len(file_data) // num_chunks
    
    if chunk_size == 0:
        return [file_data]
    
    chunks = []
    for i in range(num_chunks):
        if i == num_chunks - 1:
            chunk = file_data[i * chunk_size:]
        else:
            chunk = file_data[i * chunk_size:(i + 1) * chunk_size]
        chunks.append(chunk)
    
    return chunks