# storage/node_manager.py
from datetime import datetime, timedelta
from db.models import StorageNode, User
from db.database import get_db_session


class NodeManager:
    def __init__(self):
        pass

    def register_node(self, node_id, host, port, storage_capacity, cpu_cores):
        try:
            with get_db_session() as session:
                existing = session.query(StorageNode).filter_by(node_id=node_id).first()
                if existing:
                    existing.host = host
                    existing.port = port
                    existing.storage_capacity = storage_capacity
                    existing.cpu_cores = cpu_cores
                    existing.status = 'online'
                    existing.last_heartbeat = datetime.utcnow()
                    print(f"[NODE] Updated node: {node_id}")
                else:
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

    def get_storage_statistics(self):
        """This method was MISSING — now fixed!"""
        try:
            with get_db_session() as session:
                nodes = session.query(StorageNode).all()
                users = session.query(User).all()

                total_capacity = sum(node.storage_capacity for node in nodes)
                total_used = sum(node.storage_used for node in nodes)
                total_allocated = sum(user.storage_allocated for user in users)
                total_user_used = sum(user.storage_used for user in users)

                online_threshold = datetime.utcnow() - timedelta(minutes=2)
                online_nodes = sum(
                    1 for node in nodes
                    if node.last_heartbeat and node.last_heartbeat > online_threshold
                )

                return {
                    'global_capacity': total_capacity,
                    'global_used': total_used,
                    'global_available': total_capacity - total_used,
                    'user_allocated': total_allocated,
                    'user_used': total_user_used,
                    'total_nodes': len(nodes),
                    'online_nodes': online_nodes,
                    'offline_nodes': len(nodes) - online_nodes,
                }
        except Exception as e:
            print(f"[ERROR] Failed to get storage statistics: {e}")
            return None

    def get_all_nodes(self):
        try:
            with get_db_session() as session:
                nodes = session.query(StorageNode).all()
                online_threshold = datetime.utcnow() - timedelta(minutes=2)
                node_list = []
                for node in nodes:
                    is_online = node.last_heartbeat and node.last_heartbeat > online_threshold
                    node_list.append({
                        'node_id': node.node_id,
                        'host': node.host,
                        'port': node.port,
                        'storage_capacity': node.storage_capacity,
                        'storage_used': node.storage_used,
                        'status': 'online' if is_online else 'offline',
                        'last_heartbeat': node.last_heartbeat.isoformat() if node.last_heartbeat else None,
                    })
                return node_list
        except Exception as e:
            print(f"[ERROR] Failed to get nodes: {e}")
            return []