#!/usr/bin/env python3
"""
Create Node Utility - Create and configure a new storage node
"""

import os
import sys
import json
import shutil

class NodeCreator:
    def __init__(self):
        self.nodes_config_file = 'nodes_config.json'
        self.load_existing_nodes()
    
    def load_existing_nodes(self):
        """Load existing node configurations"""
        if os.path.exists(self.nodes_config_file):
            with open(self.nodes_config_file, 'r') as f:
                self.existing_nodes = json.load(f)
        else:
            self.existing_nodes = {}
    
    def save_nodes_config(self):
        """Save node configurations"""
        with open(self.nodes_config_file, 'w') as f:
            json.dump(self.existing_nodes, f, indent=2)
    
    def create_node(self, node_id, host='localhost', port=None, storage_gb=1, cpu_cores=1, bandwidth='1Gbps'):
        """Create a new storage node configuration"""
        
        # Check if node already exists
        if node_id in self.existing_nodes:
            print(f"[ERROR] Node {node_id} already exists!")
            return False
        
        # Auto-assign port if not specified
        if port is None:
            port = 9001 + len(self.existing_nodes)
        
        # Create node configuration
        node_config = {
            'node_id': node_id,
            'host': host,
            'port': port,
            'storage_capacity_gb': storage_gb,
            'cpu_cores': cpu_cores,
            'bandwidth': bandwidth,
            'storage_dir': f"storage_{node_id}",
            'created_at': str(__import__('datetime').datetime.now()),
            'status': 'created'
        }
        
        # Add to configurations
        self.existing_nodes[node_id] = node_config
        self.save_nodes_config()
        
        # Create storage directory
        storage_dir = f"storage_{node_id}"
        if os.path.exists(storage_dir):
            shutil.rmtree(storage_dir)
        os.makedirs(storage_dir, exist_ok=True)
        
        print(f"[SUCCESS] Node {node_id} created successfully!")
        print(f"[INFO] Configuration:")
        print(f"   Host: {host}:{port}")
        print(f"   Storage: {storage_gb} GB")
        print(f"   CPU Cores: {cpu_cores}")
        print(f"   Bandwidth: {bandwidth}")
        print(f"   Storage Directory: {storage_dir}")
        
        return True
    
    def list_nodes(self):
        """List all created nodes"""
        print("[INFO] Created Nodes:")
        print("=" * 60)
        
        if not self.existing_nodes:
            print("No nodes created yet.")
            return
        
        for node_id, config in self.existing_nodes.items():
            print(f"[NODE] {node_id}")
            print(f"   Address: {config['host']}:{config['port']}")
            print(f"   Storage: {config['storage_capacity_gb']} GB")
            print(f"   CPU: {config['cpu_cores']} cores")
            print(f"   Bandwidth: {config['bandwidth']}")
            print(f"   Status: {config['status']}")
            print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python create_node.py <node_id> [options]")
        print("Options:")
        print("  --host <hostname>     Default: localhost")
        print("  --port <port>         Default: auto-assigned")
        print("  --storage <gb>        Default: 1")
        print("  --cpu <cores>         Default: 1")
        print("  --bandwidth <speed>   Default: 1Gbps")
        print("  --list                List existing nodes")
        print()
        print("Examples:")
        print("  python create_node.py node1")
        print("  python create_node.py node2 --storage 2 --cpu 2")
        print("  python create_node.py node3 --host remote_host --port 9010")
        print("  python create_node.py --list")
        sys.exit(1)
    
    creator = NodeCreator()
    
    if sys.argv[1] == '--list':
        creator.list_nodes()
        return
    
    node_id = sys.argv[1]
    
    # Parse command line arguments
    host = 'localhost'
    port = None
    storage_gb = 1
    cpu_cores = 1
    bandwidth = '1Gbps'
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--host' and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--port' and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--storage' and i + 1 < len(sys.argv):
            storage_gb = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--cpu' and i + 1 < len(sys.argv):
            cpu_cores = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--bandwidth' and i + 1 < len(sys.argv):
            bandwidth = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    creator.create_node(node_id, host, port, storage_gb, cpu_cores, bandwidth)

if __name__ == "__main__":
    main()