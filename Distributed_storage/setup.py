
#!/usr/bin/env python3
"""
Setup Script - Make all Python files executable and prepare the system
"""

import os
import sys
import stat

def make_executable(filepath):
    """Make a file executable"""
    try:
        current_stat = os.stat(filepath)
        os.chmod(filepath, current_stat.st_mode | stat.S_IEXEC)
        print(f"[SUCCESS] Made executable: {filepath}")
    except Exception as e:
        print(f"[ERROR] Failed to make executable: {filepath} - {e}")

def main():
    print("[SETUP] Setting up Distributed Cloud Storage System")
    print("=" * 50)
    
    # List of Python files to make executable
    python_files = [
        'cloud_gateway.py',
        'storage_node.py',
        'upload_client.py',
        'download_client.py',
        'create_node.py',
        'start_node.py',
        'demo.py'
    ]
    
    print("[INFO] Making Python files executable...")
    for file in python_files:
        if os.path.exists(file):
            make_executable(file)
        else:
            print(f"[ERROR] File not found: {file}")
    
    print()
    print("[CLEANUP] Cleaning up any existing storage directories...")
    
    # Clean up existing storage directories
    for item in os.listdir('.'):
        if item.startswith('storage_') and os.path.isdir(item):
            import shutil
            try:
                shutil.rmtree(item)
                print(f"[REMOVED] Removed: {item}")
            except Exception as e:
                print(f"[ERROR] Failed to remove {item}: {e}")
    
    # Clean up database files
    db_files = ['cloud_db.pkl', 'nodes_config.json']
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                print(f"[REMOVED] Removed: {db_file}")
            except Exception as e:
                print(f"[ERROR] Failed to remove {db_file}: {e}")
    
    print()
    print("[SUCCESS] Setup complete!")
    print()
    print("[START] Quick Start:")
    print("1. Start Cloud Gateway: python cloud_gateway.py")
    print("2. Create node: python create_node.py node1 --storage 1")
    print("3. Start node: python start_node.py node1")
    print("4. Upload file: python upload_client.py <file>")
    print()
    print("[DEMO] Or run the demo: python demo.py")

if __name__ == "__main__":
    main()
