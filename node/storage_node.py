"""
Node Manager - Node health monitoring and management
With DYNAMIC global storage that grows with nodes
"""
from datetime import datetime, timedelta
from db.models import StorageNode, SystemEvent
from db.database import get_db_session

class NodeManager:
    def __init__(self):
        pass
    
    def register_node(self, node_id, host, port, storage_capacity, cpu_cores):
        """Register a new storage node - DYNAMICALLY increases global storage"""
        try:
            with get_db_session() as session:
                # Check if node exists
                existing = session.query(StorageNode).filter_by(node_id=node_id).first()
                
                if existing:
                    # Update existing node
                    old_capacity = existing.storage_capacity
                    existing.host = host
                    existing.port = port
                    existing.storage_capacity = storage_capacity
                    existing.cpu_cores = cpu_cores
                    existing.status = 'online'
                    existing.last_heartbeat = datetime.utcnow()
                    
                    capacity_change = storage_capacity - old_capacity
                    
                    # Log event
                    event = SystemEvent(
                        event_type='NODE_UPDATED',
                        message=f'Node {node_id} updated: capacity changed by {capacity_change} bytes',
                        metadata={'node_id': node_id, 'capacity_change': capacity_change}
                    )
                    session.add(event)
                    
                    print(f"[NODE] Updated node: {node_id}")
                    print(f"[STORAGE] Global storage changed by: {capacity_change / (1024**3):.2f} GB")
                else:
                    # Create new node - ADDS to global storage
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
                    
                    # Log event
                    event = SystemEvent(
                        event_type='NODE_REGISTERED',
                        message=f'Node {node_id} registered: +{storage_capacity} bytes to global storage',
                        metadata={'node_id': node_id, 'storage_added': storage_capacity}
                    )
                    session.add(event)
                    
                    print(f"[NODE] Registered new node: {node_id}")
                    print(f"[STORAGE] Global storage increased by: {storage_capacity / (1024**3):.2f} GB")
                
                # Calculate new global storage
                total_capacity = self.get_global_storage_capacity()
                print(f"[STORAGE] Total global storage: {total_capacity / (1024**3):.2f} GB")
                
                return True, "Node registered successfully"
        
        except Exception as e:
            print(f"[ERROR] Failed to register node: {e}")
            return False, str(e)
    
    def get_global_storage_capacity(self):
        """Get total storage capacity across ALL nodes (dynamic)"""
        try:
            with get_db_session() as session:
                nodes = session.query(StorageNode).all()
                total_capacity = sum(node.storage_capacity for node in nodes)
                return total_capacity
        except Exception as e:
            print(f"[ERROR] Failed to get global capacity: {e}")
            return 0
    
    def get_global_storage_used(self):
        """Get total storage used across ALL nodes"""
        try:
            with get_db_session() as session:
                nodes = session.query(StorageNode).all()
                total_used = sum(node.storage_used for node in nodes)
                return total_used
        except Exception as e:
            print(f"[ERROR] Failed to get global usage: {e}")
            return 0
    
    def get_global_storage_available(self):
        """Get total available storage across ALL nodes"""
        capacity = self.get_global_storage_capacity()
        used = self.get_global_storage_used()
        return capacity - used
    
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
                    
                    # Log event
                    event = SystemEvent(
                        event_type='NODE_OFFLINE',
                        message=f'Node {node_id} went offline',
                        metadata={'node_id': node_id}
                    )
                    session.add(event)
                    
                    return True
                return False
        except Exception as e:
            print(f"[ERROR] Failed to mark node offline: {e}")
            return False
    
    def remove_node(self, node_id):
        """Remove node from system - DECREASES global storage"""
        try:
            with get_db_session() as session:
                node = session.query(StorageNode).filter_by(node_id=node_id).first()
                if not node:
                    return False, "Node not found"
                
                storage_removed = node.storage_capacity
                
                # Check if node has chunks stored
                from db.models import Chunk
                chunks = session.query(Chunk).filter_by(primary_node_id=node_id).count()
                
                if chunks > 0:
                    return False, f"Cannot remove node: {chunks} chunks still stored on this node"
                
                session.delete(node)
                
                # Log event
                event = SystemEvent(
                    event_type='NODE_REMOVED',
                    message=f'Node {node_id} removed: -{storage_removed} bytes from global storage',
                    metadata={'node_id': node_id, 'storage_removed': storage_removed}
                )
                session.add(event)
                
                print(f"[NODE] Removed node: {node_id}")
                print(f"[STORAGE] Global storage decreased by: {storage_removed / (1024**3):.2f} GB")
                
                # Calculate new global storage
                total_capacity = self.get_global_storage_capacity()
                print(f"[STORAGE] Total global storage: {total_capacity / (1024**3):.2f} GB")
                
                return True, "Node removed successfully"
        
        except Exception as e:
            print(f"[ERROR] Failed to remove node: {e}")
            return False, str(e)
    
    def get_all_nodes(self):
        """Get all nodes with statistics"""
        try:
            with get_db_session() as session:
                nodes = session.query(StorageNode).all()
                
                node_list = []
                for node in nodes:
                    # Check if node is really online (heartbeat within last 2 minutes)
                    is_online = False
                    if node.last_heartbeat:
                        time_since_heartbeat = datetime.utcnow() - node.last_heartbeat
                        is_online = time_since_heartbeat < timedelta(minutes=2)
                    
                    node_list.append({
                        'node_id': node.node_id,
                        'host': node.host,
                        'port': node.port,
                        'storage_capacity': node.storage_capacity,
                        'storage_used': node.storage_used,
                        'storage_available': node.storage_capacity - node.storage_used,
                        'status': 'online' if is_online else 'offline',
                        'last_heartbeat': node.last_heartbeat.isoformat() if node.last_heartbeat else None,
                        'health_score': node.health_score,
                        'cpu_cores': node.cpu_cores
                    })
                
                return node_list
        
        except Exception as e:
            print(f"[ERROR] Failed to get all nodes: {e}")
            return []
    
    def get_storage_statistics(self):
        """Get comprehensive storage statistics"""
        try:
            with get_db_session() as session:
                nodes = session.query(StorageNode).all()
                
                total_capacity = sum(node.storage_capacity for node in nodes)
                total_used = sum(node.storage_used for node in nodes)
                total_available = total_capacity - total_used
                
                online_nodes = sum(1 for node in nodes if node.status == 'online')
                offline_nodes = len(nodes) - online_nodes
                
                # Get user storage info
                from db.models import User
                users = session.query(User).all()
                total_allocated = sum(user.storage_allocated for user in users)
                total_user_used = sum(user.storage_used for user in users)
                
                return {
                    'global_capacity': total_capacity,
                    'global_used': total_used,
                    'global_available': total_available,
                    'total_nodes': len(nodes),
                    'online_nodes': online_nodes,
                    'offline_nodes': offline_nodes,
                    'user_allocated': total_allocated,
                    'user_used': total_user_used,
                    'allocation_percentage': (total_allocated / total_capacity * 100) if total_capacity > 0 else 0,
                    'usage_percentage': (total_used / total_capacity * 100) if total_capacity > 0 else 0
                }
        
        except Exception as e:
            print(f"[ERROR] Failed to get storage statistics: {e}")
            return None