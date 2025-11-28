"""
Generate Python code from proto file
"""
import os
import sys
import subprocess

def generate_proto():
    # Create generated directory if it doesn't exist
    if not os.path.exists('generated'):
        os.makedirs('generated')
        print("✓ Created 'generated' directory")
    
    # Create __init__.py
    init_file = os.path.join('generated', '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('')
        print("✓ Created generated/__init__.py")
    
    # Generate protobuf files
    cmd = [
        sys.executable, '-m', 'grpc_tools.protoc',
        '-I./proto',
        '--python_out=./generated',
        '--grpc_python_out=./generated',
        './proto/cloud_storage.proto'
    ]
    
    print("\n[PROTO] Generating protobuf files...")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\n✓ Protobuf files generated successfully!")
        print("  - generated/cloud_storage_pb2.py")
        print("  - generated/cloud_storage_pb2_grpc.py")
    else:
        print("\n✗ Failed to generate protobuf files")
        print(f"Error: {result.stderr}")
        sys.exit(1)

if __name__ == '__main__':
    generate_proto()