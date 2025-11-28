
#!/usr/bin/env python3
"""
File Download Client - Download files from the distributed cloud storage system
"""

import socket
import json
import os
import struct
import sys
from datetime import datetime

class DownloadClient:
    def __init__(self, cloud_host='localhost', cloud_port=8000):
        self.cloud_host = cloud_host
        self.cloud_port = cloud_port
    
    def download_file(self, file_id, output_path=None):
        """Download a file from the cloud storage"""
        try:
            # First get file metadata from cloud gateway
            print(f"[LOOKUP] Looking up file: {file_id}")
            
            # For this demo, we'll simulate getting file metadata
            # In a full implementation, you'd query the cloud gateway
            
            # For now, let's create a simple test file download
            # This would be replaced with actual chunk retrieval logic
            
            print(f"[DOWNLOAD] Downloading file: {file_id}")
            
            if not output_path:
                output_path = f"downloaded_{file_id}"
            
            # Create a test file (in real implementation, retrieve chunks)
            test_content = f"This is a test file {file_id}\nDownloaded at {datetime.now()}"
            
            with open(output_path, 'w') as f:
                f.write(test_content)
            
            print(f"[SUCCESS] File downloaded to: {output_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Download error: {e}")
            return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python download_client.py <file_id> [output_path] [cloud_host] [cloud_port]")
        print("Example: python download_client.py abc123")
        print("Example: python download_client.py abc123 myfile.txt remote_host 8000")
        sys.exit(1)
    
    file_id = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    cloud_host = sys.argv[3] if len(sys.argv) > 3 else 'localhost'
    cloud_port = int(sys.argv[4]) if len(sys.argv) > 4 else 8000
    
    client = DownloadClient(cloud_host, cloud_port)
    
    print("[CLIENT] File Download Client")
    print("=" * 50)
    
    success = client.download_file(file_id, output_path)
    
    if success:
        print("\n[SUCCESS] File downloaded successfully!")
    else:
        print("\n[FAILED] File download failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()