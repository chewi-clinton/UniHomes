#!/usr/bin/env python3
"""
File Upload Client - Upload files to the distributed cloud storage system
"""

import socket
import json
import os
import struct
import sys
from datetime import datetime

class UploadClient:
    def __init__(self, cloud_host='localhost', cloud_port=8000):
        self.cloud_host = cloud_host
        self.cloud_port = cloud_port
    
    def upload_file(self, file_path):
        """Upload a file to the cloud storage"""
        try:
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return False
            
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            print(f"📁 Uploading: {filename}")
            print(f"📊 Size: {file_size} bytes ({file_size / (1024**2):.2f} MB)")
            
            # Read file data
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Connect to cloud gateway
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.cloud_host, self.cloud_port))
            
            # Send upload request
            request = {
                'type': 'upload',
                'filename': filename,
                'file_size': file_size,
                'file_data': file_data.decode('latin1')  # Convert bytes to string for JSON
            }
            
            print(f"🌐 Connecting to Cloud Gateway...")
            self.send_message(sock, json.dumps(request).encode('utf-8'))
            
            # Wait for response
            response_data = self.recv_message(sock)
            if response_data:
                response = json.loads(response_data.decode('utf-8'))
                
                if response.get('type') == 'upload_complete':
                    file_id = response.get('file_id')
                    chunks_stored = response.get('chunks_stored')
                    total_chunks = response.get('total_chunks')
                    
                    print(f"✅ Upload complete!")
                    print(f"📋 File ID: {file_id}")
                    print(f"🧩 Chunks: {chunks_stored}/{total_chunks} stored successfully")
                    print(f"⏱️  Upload time: {datetime.now().strftime('%H:%M:%S')}")
                    
                    sock.close()
                    return True
                
                elif response.get('type') == 'upload_error':
                    error_msg = response.get('message', 'Unknown error')
                    print(f"❌ Upload failed: {error_msg}")
                    
                    sock.close()
                    return False
            
            print(f"❌ No response from Cloud Gateway")
            sock.close()
            return False
            
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
    
    def send_message(self, sock, data):
        """Send a message with length prefix"""
        try:
            # Send message length first
            msg_length = len(data)
            sock.sendall(struct.pack('!I', msg_length))
            
            # Then send the message data
            sock.sendall(data)
            return True
        except Exception as e:
            print(f"Send error: {e}")
            return False
    
    def recv_message(self, sock):
        """Receive a message with length prefix"""
        try:
            # First receive the message length
            length_data = sock.recv(4)
            if not length_data:
                return None
            
            msg_length = struct.unpack('!I', length_data)[0]
            
            # Then receive the message data
            data = b''
            while len(data) < msg_length:
                chunk = sock.recv(min(msg_length - len(data), 4096))
                if not chunk:
                    return None
                data += chunk
            
            return data
        except Exception as e:
            print(f"Receive error: {e}")
            return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_client.py <file_path> [cloud_host] [cloud_port]")
        print("Example: python upload_client.py photo.jpg")
        print("Example: python upload_client.py document.pdf remote_host 8000")
        sys.exit(1)
    
    file_path = sys.argv[1]
    cloud_host = sys.argv[2] if len(sys.argv) > 2 else 'localhost'
    cloud_port = int(sys.argv[3]) if len(sys.argv) > 3 else 8000
    
    client = UploadClient(cloud_host, cloud_port)
    
    print("🚀 File Upload Client")
    print("=" * 50)
    
    success = client.upload_file(file_path)
    
    if success:
        print("\n🎉 File uploaded successfully!")
    else:
        print("\n💥 File upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()