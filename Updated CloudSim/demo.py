#!/usr/bin/env python3
"""
Demo Script - Quick demonstration of the distributed cloud storage system
"""

import os
import sys
import subprocess
import time
import threading

def create_test_file(filename, size_mb=1):
    """Create a test file with specified size"""
    print(f"📄 Creating test file: {filename} ({size_mb} MB)")
    
    with open(filename, 'wb') as f:
        # Write 1MB chunks
        chunk_size = 1024 * 1024
        for _ in range(size_mb):
            f.write(b'X' * chunk_size)

def run_command(cmd, terminal_num):
    """Run a command in a new terminal"""
    print(f"🖥️  Terminal {terminal_num}: {' '.join(cmd)}")
    
    if sys.platform == 'win32':
        # Windows
        subprocess.Popen(['start', 'cmd', '/k', ' '.join(cmd)], shell=True)
    elif sys.platform == 'darwin':
        # macOS
        script = f'tell application "Terminal" to do script "{" ".join(cmd)}"'
        subprocess.Popen(['osascript', '-e', script])
    else:
        # Linux
        subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', ' '.join(cmd) + '; exec bash'])
    
    time.sleep(2)  # Give time for terminal to open

def main():
    print("🚀 Distributed Cloud Storage System Demo")
    print("=" * 60)
    print()
    
    # Check if required files exist
    required_files = ['cloud_gateway.py', 'storage_node.py', 'upload_client.py', 'create_node.py', 'start_node.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Missing required file: {file}")
            sys.exit(1)
    
    print("✅ All required files found")
    print()
    
    # Create test file
    test_file = "demo_test_file.txt"
    create_test_file(test_file, 1)  # 1MB file
    
    print()
    print("🎯 Demo Instructions:")
    print("1. The Cloud Gateway will start in Terminal 1")
    print("2. Node 1 will be created and started in Terminal 2")
    print("3. Node 2 will be created and started in Terminal 3") 
    print("4. The test file will be uploaded in Terminal 4")
    print()
    print("💡 Watch the Cloud Gateway terminal to see nodes registering!")
    print("⚠️  You may need to arrange the terminals to see all activity")
    print()
    
    input("📝 Press Enter to start the demo (this will open 4 terminals)...")
    
    terminal_num = 1
    
    # Terminal 1: Cloud Gateway
    cmd1 = [sys.executable, 'cloud_gateway.py']
    run_command(cmd1, terminal_num)
    terminal_num += 1
    
    time.sleep(3)  # Give gateway time to start
    
    # Terminal 2: Create and start Node 1
    cmd2a = [sys.executable, 'create_node.py', 'demo_node1', '--storage', '1', '--cpu', '1']
    run_command(cmd2a, terminal_num)
    terminal_num += 1
    
    time.sleep(2)
    
    cmd2b = [sys.executable, 'start_node.py', 'demo_node1']
    run_command(cmd2b, terminal_num)
    terminal_num += 1
    
    time.sleep(3)  # Give node time to register
    
    # Terminal 3: Create and start Node 2
    cmd3a = [sys.executable, 'create_node.py', 'demo_node2', '--storage', '2', '--cpu', '1']
    run_command(cmd3a, terminal_num)
    terminal_num += 1
    
    time.sleep(2)
    
    cmd3b = [sys.executable, 'start_node.py', 'demo_node2']
    run_command(cmd3b, terminal_num)
    terminal_num += 1
    
    time.sleep(3)  # Give nodes time to register
    
    # Terminal 4: Upload file
    cmd4 = [sys.executable, 'upload_client.py', test_file]
    run_command(cmd4, terminal_num)
    
    print()
    print("🎉 Demo started! Check the terminals to see the system in action.")
    print("📝 The Cloud Gateway terminal will show nodes registering and storage increasing.")
    print("🖥️  Each node terminal shows its status and statistics.")
    print("📁 The upload terminal will show the file being distributed across nodes.")
    print()
    print("🛑 To stop the demo, close the terminal windows or press Ctrl+C in each.")
    print()
    print("🔍 After the demo, you can check the created files:")
    print(f"   - Test file: {test_file}")
    print("   - Node storage: storage_demo_node1/, storage_demo_node2/")
    print("   - Configuration: nodes_config.json")
    print("   - Database: cloud_db.pkl")

if __name__ == "__main__":
    main()