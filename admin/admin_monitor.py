#!/usr/bin/env python3
"""
Admin Monitor - Administrative monitoring dashboard (FULLY FUNCTIONAL)
"""
import grpc
import sys
import os
import threading
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from generated import cloud_storage_pb2
from generated import cloud_storage_pb2_grpc
from dotenv import load_dotenv

load_dotenv()


class AdminMonitor:
    def __init__(self, server_address='localhost:50051', admin_key=None):
        self.server_address = server_address
        self.admin_key = admin_key or os.getenv('ADMIN_KEY', 'admin123')
        self.channel = grpc.insecure_channel(server_address)
        self.admin_stub = cloud_storage_pb2_grpc.AdminServiceStub(self.channel)
        self.monitoring = False
    
    def format_bytes(self, bytes_value):
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def get_system_status(self):
        """Get current system status"""
        try:
            response = self.admin_stub.GetSystemStatus(
                cloud_storage_pb2.SystemStatusRequest(admin_key=self.admin_key)
            )
            return response
        except grpc.RpcError as e:
            print(f"✗ Failed to get system status: {e.details()}")
            return None
    
    def display_system_status(self):
        """Display detailed system status"""
        status = self.get_system_status()
        
        if not status:
            return
        
        print("\n" + "=" * 80)
        print("CLOUD STORAGE PLATFORM - SYSTEM STATUS")
        print("=" * 80)
        
        print("\n📊 STORAGE OVERVIEW:")
        print(f"  Total Capacity:     {self.format_bytes(status.global_capacity_bytes)}")
        print(f"  Allocated:          {self.format_bytes(status.global_allocated_bytes)}")
        print(f"  Actually Used:      {self.format_bytes(status.global_used_bytes)}")
        print(f"  Available:          {self.format_bytes(status.global_capacity_bytes - status.global_allocated_bytes)}")
        
        # Storage bars
        if status.global_capacity_bytes > 0:
            bar_length = 50
            
            # Allocation bar
            alloc_pct = (status.global_allocated_bytes / status.global_capacity_bytes) * 100
            alloc_filled = int(bar_length * alloc_pct / 100)
            alloc_bar = '█' * alloc_filled + '░' * (bar_length - alloc_filled)
            print(f"\n  Allocation: [{alloc_bar}] {alloc_pct:.1f}%")
            
            # Usage bar
            if status.global_allocated_bytes > 0:
                usage_pct = (status.global_used_bytes / status.global_allocated_bytes) * 100
                usage_filled = int(bar_length * usage_pct / 100)
                usage_bar = '█' * usage_filled + '░' * (bar_length - usage_filled)
                print(f"  Usage:      [{usage_bar}] {usage_pct:.1f}%")
        
        print("\n👥 USER STATISTICS:")
        print(f"  Total Users:        {status.total_users}")
        
        print("\n💾 STORAGE NODES:")
        print(f"  Total Nodes:        {status.total_nodes}")
        print(f"  Online Nodes:       {status.online_nodes}")
        print(f"  Offline Nodes:      {status.total_nodes - status.online_nodes}")
        
        # Node health indicator
        if status.total_nodes > 0:
            node_health_pct = (status.online_nodes / status.total_nodes) * 100
            if node_health_pct >= 80:
                health_icon = "🟢"
                health_status = "HEALTHY"
            elif node_health_pct >= 50:
                health_icon = "🟡"
                health_status = "DEGRADED"
            else:
                health_icon = "🔴"
                health_status = "CRITICAL"
            
            print(f"  Node Health:        {health_icon} {health_status} ({node_health_pct:.0f}%)")
        
        print("\n📁 FILE STATISTICS:")
        print(f"  Total Files:        {status.total_files}")
        print(f"  Total Chunks:       {status.total_chunks}")
        
        if status.total_files > 0:
            avg_chunks = status.total_chunks / status.total_files
            print(f"  Avg Chunks/File:    {avg_chunks:.1f}")
        
        print("\n🏥 SYSTEM HEALTH:")
        print(f"  Overall Health:     {status.system_health:.1f}%")
        
        print("=" * 80)
    
    def list_all_users(self):
        """List all users in the system"""
        try:
            response = self.admin_stub.ListAllUsers(
                cloud_storage_pb2.ListUsersRequest(admin_key=self.admin_key)
            )
            
            if not response.success:
                print("✗ Failed to retrieve users")
                return
            
            print("\n" + "=" * 80)
            print("USER LIST")
            print("=" * 80)
            
            if not response.users:
                print("\nNo users registered yet.")
                print("=" * 80)
                return
            
            print(f"\n{'Email':<35} {'Name':<20} {'Storage Used':<15} {'Files':<8} {'Last Login':<20}")
            print("-" * 80)
            
            for user in response.users:
                storage_used = self.format_bytes(user.storage_used)
                storage_alloc = self.format_bytes(user.storage_allocated)
                last_login = user.last_login[:19].replace('T', ' ') if user.last_login else 'Never'
                
                print(f"{user.email:<35} {user.name:<20} {storage_used:>8}/{storage_alloc:<15} {user.file_count:<8} {last_login:<20}")
            
            print("=" * 80)
            print(f"\nTotal Users: {len(response.users)}")
            print("=" * 80)
        
        except grpc.RpcError as e:
            print(f"✗ Failed to list users: {e.details()}")
    
    def list_all_nodes(self):
        """List all storage nodes"""
        try:
            response = self.admin_stub.ListAllNodes(
                cloud_storage_pb2.ListNodesRequest(admin_key=self.admin_key)
            )
            
            if not response.success:
                print("✗ Failed to retrieve nodes")
                return
            
            print("\n" + "=" * 80)
            print("STORAGE NODES")
            print("=" * 80)
            
            if not response.nodes:
                print("\nNo storage nodes registered yet.")
                print("=" * 80)
                return
            
            print(f"\n{'Node ID':<15} {'Address':<25} {'Capacity':<12} {'Used':<12} {'Status':<10} {'Health':<8}")
            print("-" * 80)
            
            for node in response.nodes:
                address = f"{node.host}:{node.port}"
                capacity = self.format_bytes(node.storage_capacity)
                used = self.format_bytes(node.storage_used)
                
                # Status indicator
                if node.status == 'online':
                    status_icon = "🟢 Online"
                else:
                    status_icon = "🔴 Offline"
                
                health = f"{node.health_score:.0f}%"
                
                print(f"{node.node_id:<15} {address:<25} {capacity:<12} {used:<12} {status_icon:<10} {health:<8}")
                
                # Last heartbeat
                if node.last_heartbeat:
                    heartbeat = node.last_heartbeat[:19].replace('T', ' ')
                    print(f"  └─ Last seen: {heartbeat}")
            
            print("=" * 80)
            print(f"\nTotal Nodes: {len(response.nodes)}")
            
            online_count = sum(1 for n in response.nodes if n.status == 'online')
            print(f"Online: {online_count} | Offline: {len(response.nodes) - online_count}")
            print("=" * 80)
        
        except grpc.RpcError as e:
            print(f"✗ Failed to list nodes: {e.details()}")
    
    def get_user_details(self, user_id):
        """Get detailed information about a specific user"""
        try:
            response = self.admin_stub.GetUserDetails(
                cloud_storage_pb2.UserDetailsRequest(
                    admin_key=self.admin_key,
                    user_id=user_id
                )
            )
            
            if not response.success:
                print("✗ User not found")
                return
            
            user = response.user
            
            print("\n" + "=" * 80)
            print(f"USER DETAILS: {user.name}")
            print("=" * 80)
            
            print(f"\n📧 Email:           {user.email}")
            print(f"🆔 User ID:         {user.user_id}")
            print(f"📅 Created:         {user.created_at[:19].replace('T', ' ')}")
            print(f"🔐 Last Login:      {user.last_login[:19].replace('T', ' ') if user.last_login else 'Never'}")
            
            print(f"\n💾 Storage:")
            storage_used = self.format_bytes(user.storage_used)
            storage_alloc = self.format_bytes(user.storage_allocated)
            usage_pct = (user.storage_used / user.storage_allocated * 100) if user.storage_allocated > 0 else 0
            
            print(f"  Allocated:        {storage_alloc}")
            print(f"  Used:             {storage_used} ({usage_pct:.1f}%)")
            print(f"  Available:        {self.format_bytes(user.storage_allocated - user.storage_used)}")
            
            # Usage bar
            bar_length = 40
            filled = int(bar_length * usage_pct / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"  [{bar}] {usage_pct:.1f}%")
            
            print(f"\n📁 Files:           {len(response.files)}")
            
            if response.files:
                print("\n  Recent Files:")
                print(f"  {'Filename':<30} {'Size':<12} {'Type':<20}")
                print("  " + "-" * 70)
                
                for file in response.files[:5]:  # Show first 5 files
                    size = self.format_bytes(file.file_size)
                    print(f"  {file.filename:<30} {size:<12} {file.mime_type:<20}")
                
                if len(response.files) > 5:
                    print(f"  ... and {len(response.files) - 5} more files")
            
            print("=" * 80)
        
        except grpc.RpcError as e:
            print(f"✗ Failed to get user details: {e.details()}")
    
    def start_event_monitoring(self):
        """Start monitoring system events in real-time"""
        self.monitoring = True
        
        def monitor():
            try:
                print("\n" + "=" * 80)
                print("REAL-TIME EVENT MONITOR")
                print("=" * 80)
                print("Listening for system events... (Press Ctrl+C to stop)\n")
                
                request = cloud_storage_pb2.StreamEventsRequest(admin_key=self.admin_key)
                
                for event in self.admin_stub.StreamSystemEvents(request):
                    if not self.monitoring:
                        break
                    
                    # Color codes for different event types
                    event_colors = {
                        'USER_ENROLLED': '🟢',
                        'USER_LOGIN': '🔵',
                        'FILE_UPLOADED': '📤',
                        'FILE_DOWNLOADED': '📥',
                        'FILE_DELETED': '🗑️',
                        'NODE_REGISTERED': '💾',
                        'OTP_SENT': '📧',
                        'OTP_VERIFIED': '✅'
                    }
                    
                    icon = event_colors.get(event.event_type, '⚪')
                    
                    print(f"{icon} [{event.timestamp[:19]}] {event.event_type}")
                    print(f"   {event.message}")
                    
                    if event.user_id:
                        print(f"   User: {event.user_id}")
                    
                    if event.details:
                        print(f"   Details: {event.details}")
                    
                    print()
                    
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.CANCELLED:
                    print("\n✓ Monitoring stopped")
                elif e.code() == grpc.StatusCode.PERMISSION_DENIED:
                    print("\n✗ Permission denied. Check admin key.")
                else:
                    print(f"\n✗ Monitoring error: {e.details()}")
            except Exception as e:
                print(f"\n✗ Error: {e}")
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        return monitor_thread
    
    def stop_event_monitoring(self):
        """Stop event monitoring"""
        self.monitoring = False
    
    def close(self):
        """Close connection"""
        self.channel.close()


def admin_menu():
    """Interactive admin menu"""
    print("=" * 80)
    print("Cloud Storage Platform - Admin Monitor")
    print("=" * 80)
    
    admin_key = input("Enter admin key (or press Enter for default): ").strip()
    if not admin_key:
        admin_key = os.getenv('ADMIN_KEY', 'admin123')
        print(f"Using default admin key from environment")
    
    monitor = AdminMonitor(admin_key=admin_key)
    monitor_thread = None
    
    while True:
        print("\n" + "=" * 80)
        print("ADMIN MENU")
        print("=" * 80)
        print("1. View System Status")
        print("2. List All Users")
        print("3. List Storage Nodes")
        print("4. Get User Details (by ID)")
        print("5. Start Real-Time Event Monitoring")
        print("6. Stop Event Monitoring")
        print("7. Refresh Display")
        print("8. Exit")
        print("=" * 80)
        
        choice = input("Select option (1-8): ").strip()
        
        if choice == '1':
            monitor.display_system_status()
        
        elif choice == '2':
            monitor.list_all_users()
        
        elif choice == '3':
            monitor.list_all_nodes()
        
        elif choice == '4':
            user_id = input("Enter User ID: ").strip()
            if user_id:
                monitor.get_user_details(user_id)
            else:
                print("✗ User ID required")
        
        elif choice == '5':
            if monitor_thread and monitor_thread.is_alive():
                print("✗ Monitoring already active!")
            else:
                monitor_thread = monitor.start_event_monitoring()
                input("\nPress Enter to return to menu (monitoring continues in background)...\n")
        
        elif choice == '6':
            monitor.stop_event_monitoring()
            print("✓ Event monitoring stopped")
        
        elif choice == '7':
            monitor.display_system_status()
        
        elif choice == '8':
            print("\n✓ Shutting down admin monitor...")
            monitor.stop_event_monitoring()
            monitor.close()
            break
        
        else:
            print("✗ Invalid choice! Please select 1-8.")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cloud Storage Admin Monitor')
    parser.add_argument('--server', default='localhost:50051', help='Server address')
    parser.add_argument('--admin-key', help='Admin key')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    parser.add_argument('--monitor', action='store_true', help='Start event monitoring')
    parser.add_argument('--users', action='store_true', help='List all users')
    parser.add_argument('--nodes', action='store_true', help='List all nodes')
    
    args = parser.parse_args()
    
    admin_key = args.admin_key or os.getenv('ADMIN_KEY', 'admin123')
    monitor = AdminMonitor(args.server, admin_key)
    
    if args.status:
        # Just show status and exit
        monitor.display_system_status()
        monitor.close()
        return 0
    
    if args.users:
        # List users and exit
        monitor.list_all_users()
        monitor.close()
        return 0
    
    if args.nodes:
        # List nodes and exit
        monitor.list_all_nodes()
        monitor.close()
        return 0
    
    if args.monitor:
        # Start monitoring and wait
        monitor.start_event_monitoring()
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n✓ Monitoring stopped")
            monitor.close()
            return 0
    
    # Interactive menu
    try:
        admin_menu()
        return 0
    except KeyboardInterrupt:
        print("\n\n✓ Admin monitor terminated by user.")
        return 0


if __name__ == '__main__':
    sys.exit(main())