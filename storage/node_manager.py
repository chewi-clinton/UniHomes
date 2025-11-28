"""
Node Manager - Node health monitoring and management
"""
from datetime import datetime, timedelta
from db.models import StorageNode
from db.database import get_db_session

class NodeManager:
    def __init__(self):
        pass
    
    def register_node(self, node_id, host, port, storage_capacity, cpu_cores):
        """Register a new storage node"""
        try:
            with get_db_session() as session:
                # Check if node exists
                existing = session.query(StorageNode).filter_by(node_id=node_id).first()
                
                if existing:
                    # Update existing node
                    existing.host = host
                    existing.port = port
                    existing.storage_capacity = storage_capacity
                    existing.cpu_cores = cpu_cores
                    existing.status = 'online'
                    existing.last_heartbeat = datetime.utcnow()
                    print(f"[NODE] Updated node: {node_id}")
                else:
                    # Create new node
                    node = StorageNode(
                        node_id=node_id,
                        host=host,
                        port=port,
                        storage_capacity=storage_capacity,
                        cpu_cores=cpu_cores,
                        status='online',
                        last_heartbeat=datetime.utcnow()
                    )
                    session.add(node)
                    print(f"[NODE] Registered new node: {node_id}")
                
                return True, "Node registered successfully"
        
        except Exception as e:
            print(f"[ERROR] Failed to register node: {e}")
            return False, str(e)
    
    def update_heartbeat(self, node_id, storage_used, chunk_count):
        """Update node heartbeat"""
        try:
            with get_db_session() as session:
                node = session.query(StorageNode).filter_by(node_id=node_id).first()
                if not node:
                    return False, "Node not found"
                
                node.last_heartbeat = datetime.utcnow()
                node.storage_used = storage_used
                node.status = 'online'
                
                return True, "Heartbeat updated"
        
        except Exception as e:
            print(f"[ERROR] Failed to update heartbeat: {e}")
            return False, str(e)
    
    def get_node_info(self, node_id):
        """Get node information"""
        try:
            with get_db_session() as session:
                node = session.query(StorageNode).filter_by(node_id=node_id).first()
                if not node:
                    return None
                
                return {
                    'node_id': node.node_id,
                    'host': node.host,
                    'port': node.port,
                    'storage_capacity': node.storage_capacity,
                    'storage_used': node.storage_used,
                    'status': node.status
                }
        except Exception as e:
            print(f"[ERROR] Failed to get node info: {e}")
            return None
    
    def mark_node_offline(self, node_id):
        """Mark node as offline"""
        try:
            with get_db_session() as session:
                node = session.query(StorageNode).filter_by(node_id=node_id).first()
                if node:
                    node.status = 'offline'
                    print(f"[NODE] Marked offline: {node_id}")
                    return True
                return False
        except Exception as e:
            print(f"[ERROR] Failed to mark node offline: {e}")
            return False