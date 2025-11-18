
#!/usr/bin/env python3
"""
Start Node Utility - Start a storage node
"""

import os
import sys
import subprocess
import json

def main():
    if len(sys.argv) < 2:
        print("Usage: python start_node.py <node_id>")
        print("Example: python start_node.py node1")
        sys.exit(1)
    
    node_id = sys.argv[1]
    
    # Check if node configuration exists
    config_file = 'nodes_config.json'
    if not os.path.exists(config_file):
        print(f"[ERROR] No node configurations found. Create a node first with create_node.py")
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        nodes_config = json.load(f)
    
    if node_id not in nodes_config:
        print(f"[ERROR] Node {node_id} not found!")
        print("Available nodes:")
        for nid in nodes_config.keys():
            print(f"  - {nid}")
        sys.exit(1)
    
    node_config = nodes_config[node_id]
    
    print(f"[START] Starting Node {node_id}...")
    
    # Build command to start storage node
    cmd = [
        sys.executable, 'storage_node.py',
        node_id,
        node_config['host'],
        str(node_config['port']),
        str(node_config['storage_capacity_gb'])
    ]
    
    try:
        # Start the storage node process
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print(f"\n[STOP] Node {node_id} stopped.")
    except Exception as e:
        print(f"[ERROR] Error starting node: {e}")

if __name__ == "__main__":
    main()
