"""
Chunk Distributor - Intelligent chunk placement algorithm
"""
import random
from db.models import StorageNode
from db.database import get_db_session
from datetime import datetime, timedelta

class ChunkDistributor:
    def __init__(self):
        pass
    
    def select_nodes_for_chunks(self, num_chunks, replication_factor=1):
        """
        Select best nodes for storing chunks
        Returns: list of node_ids for each chunk
        """
        try:
            with get_db_session() as session:
                # Get online nodes with available space
                nodes = session.query(StorageNode).filter(
                    StorageNode.status == 'online',
                    StorageNode.storage_used < StorageNode.storage_capacity
                ).all()
                
                if not nodes:
                    return None, "No available storage nodes"
                
                # Filter nodes that responded recently (last 2 minutes)
                recent_threshold = datetime.utcnow() - timedelta(minutes=2)
                online_nodes = [
                    n for n in nodes 
                    if n.last_heartbeat and n.last_heartbeat > recent_threshold
                ]
                
                if not online_nodes:
                    return None, "No online storage nodes"
                
                # Sort by available space and health
                sorted_nodes = sorted(
                    online_nodes,
                    key=lambda n: (
                        n.storage_capacity - n.storage_used,
                        n.health_score
                    ),
                    reverse=True
                )
                
                # Select nodes for each chunk (round-robin with replication)
                chunk_node_mapping = []
                for i in range(num_chunks):
                    primary_node = sorted_nodes[i % len(sorted_nodes)]
                    
                    # Select replica nodes if replication > 1
                    replicas = []
                    if replication_factor > 1:
                        available_replicas = [
                            n for n in sorted_nodes 
                            if n.node_id != primary_node.node_id
                        ]
                        replica_count = min(replication_factor - 1, len(available_replicas))
                        replicas = random.sample(available_replicas, replica_count)
                    
                    chunk_node_mapping.append({
                        'primary': primary_node.node_id,
                        'replicas': [r.node_id for r in replicas],
                        'primary_host': primary_node.host,
                        'primary_port': primary_node.port
                    })
                
                return chunk_node_mapping, None
        
        except Exception as e:
            print(f"[ERROR] Failed to select nodes: {e}")
            return None, str(e)
    
    def get_node_for_retrieval(self, chunk_id):
        """Get best node for retrieving a chunk"""
        try:
            from db.models import Chunk
            with get_db_session() as session:
                chunk = session.query(Chunk).filter_by(chunk_id=chunk_id).first()
                if not chunk:
                    return None, "Chunk not found"
                
                # Try primary node first
                primary_node = session.query(StorageNode).filter_by(
                    node_id=chunk.primary_node_id,
                    status='online'
                ).first()
                
                if primary_node:
                    return {
                        'node_id': primary_node.node_id,
                        'host': primary_node.host,
                        'port': primary_node.port
                    }, None
                
                # Try replica nodes
                if chunk.replica_nodes:
                    for replica_id in chunk.replica_nodes:
                        replica_node = session.query(StorageNode).filter_by(
                            node_id=replica_id,
                            status='online'
                        ).first()
                        if replica_node:
                            return {
                                'node_id': replica_node.node_id,
                                'host': replica_node.host,
                                'port': replica_node.port
                            }, None
                
                return None, "No available nodes for chunk"
        
        except Exception as e:
            print(f"[ERROR] Failed to get node: {e}")
            return None, str(e)