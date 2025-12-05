#!/usr/bin/env python3
"""
Payment CLI Client - Test and manage payments
Create this file: backend/clients/payment_client.py

Usage:
    python payment_client.py tiers                    # List storage tiers
    python payment_client.py buy                      # Interactive purchase
    python payment_client.py history                  # View payment history
    python payment_client.py status <payment_id>      # Check payment status
"""
import grpc
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from generated import cloud_storage_pb2, cloud_storage_pb2_grpc


class PaymentClient:
    """CLI client for payment operations"""
    
    def __init__(self, server_address='localhost:50051'):
        self.server_address = server_address
        self.channel = grpc.insecure_channel(server_address)
        self.payment_stub = cloud_storage_pb2_grpc.PaymentServiceStub(self.channel)
        self.auth_stub = cloud_storage_pb2_grpc.AuthServiceStub(self.channel)
        self.storage_stub = cloud_storage_pb2_grpc.StorageServiceStub(self.channel)
        self.session_token = None
    
    def format_bytes(self, bytes_value):
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB"
    
    def login(self, email):
        """Login user (assumes OTP already verified)"""
        try:
            # For testing, we'll simulate successful login
            # In production, user would complete OTP verification first
            response = self.auth_stub.Login(
                cloud_storage_pb2.LoginRequest(email=email)
            )
            
            if response.success:
                self.session_token = response.session_token
                print(f"✓ Logged in as: {email}")
                return True
            else:
                print(f"✗ Login failed: {response.message}")
                return False
        
        except grpc.RpcError as e:
            print(f"✗ Login error: {e.details()}")
            return False
    
    def get_storage_tiers(self):
        """List available storage tiers"""
        try:
            response = self.payment_stub.GetStorageTiers(
                cloud_storage_pb2.GetStorageTiersRequest()
            )
            
            if response.success:
                print("\n" + "=" * 80)
                print("AVAILABLE STORAGE TIERS")
                print("=" * 80)
                
                for i, tier in enumerate(response.tiers, 1):
                    storage_gb = tier.storage_bytes / (1024**3)
                    storage_mb = tier.storage_bytes / (1024**2)
                    
                    print(f"\n{i}. {tier.display_name}")
                    print(f"   Storage: {storage_mb:.0f} MB ({storage_gb:.2f} GB)")
                    print(f"   Price: {tier.price_xaf} XAF (~${tier.price_xaf / 600:.2f} USD)")
                    print(f"   {tier.description}")
                
                print("\n" + "=" * 80)
                return list(response.tiers)
            else:
                print("✗ Failed to get storage tiers")
                return []
        
        except grpc.RpcError as e:
            print(f"✗ Error: {e.details()}")
            return []
    
    def show_current_storage(self):
        """Show current storage usage"""
        if not self.session_token:
            print("✗ Not logged in")
            return
        
        try:
            response = self.storage_stub.GetStorageInfo(
                cloud_storage_pb2.StorageInfoRequest(session_token=self.session_token)
            )
            
            if response.success:
                print("\n📊 CURRENT STORAGE:")
                print(f"  Allocated: {self.format_bytes(response.allocated_bytes)}")
                print(f"  Used:      {self.format_bytes(response.used_bytes)}")
                print(f"  Available: {self.format_bytes(response.available_bytes)}")
                print(f"  Usage:     {response.usage_percentage:.1f}%")
                
                # Progress bar
                bar_length = 40
                filled = int(bar_length * response.usage_percentage / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                print(f"  [{bar}] {response.usage_percentage:.1f}%\n")
        
        except grpc.RpcError as e:
            print(f"✗ Error getting storage info: {e.details()}")
    
    def initiate_payment(self, tier_id, provider, phone_number):
        """Initiate a payment"""
        if not self.session_token:
            print("✗ Not logged in")
            return None
        
        try:
            print(f"\n💳 Initiating payment...")
            print(f"   Provider: {provider}")
            print(f"   Phone: {phone_number}")
            
            response = self.payment_stub.InitiatePayment(
                cloud_storage_pb2.InitiatePaymentRequest(
                    session_token=self.session_token,
                    tier_id=tier_id,
                    provider=provider,
                    phone_number=phone_number
                )
            )
            
            if response.success:
                print(f"\n✓ Payment initiated successfully!")
                print(f"\n📱 PAYMENT DETAILS:")
                print(f"   Payment ID: {response.payment_id}")
                print(f"   Transaction Ref: {response.transaction_ref}")
                print(f"   Amount: {response.amount_xaf} XAF")
                print(f"\n🔔 Please check your phone and enter your PIN to complete payment.")
                print(f"   You will receive a notification from {provider.upper()}.")
                
                return response.payment_id
            else:
                print(f"✗ Payment initiation failed: {response.message}")
                return None
        
        except grpc.RpcError as e:
            print(f"✗ Payment error: {e.details()}")
            return None
    
    def check_payment_status(self, payment_id):
        """Check payment status"""
        if not self.session_token:
            print("✗ Not logged in")
            return
        
        try:
            response = self.payment_stub.CheckPaymentStatus(
                cloud_storage_pb2.CheckPaymentStatusRequest(
                    session_token=self.session_token,
                    payment_id=payment_id
                )
            )
            
            if response.success:
                # Status icons
                status_icons = {
                    'pending': '⏳',
                    'processing': '⚙️',
                    'completed': '✅',
                    'failed': '❌',
                    'cancelled': '🚫'
                }
                
                icon = status_icons.get(response.status, '❓')
                
                print(f"\n{icon} PAYMENT STATUS: {response.status.upper()}")
                print(f"   {response.message}")
                
                if response.storage_added > 0:
                    storage_added = self.format_bytes(response.storage_added)
                    print(f"\n🎉 Storage Added: {storage_added}")
                    print(f"   Your storage has been increased!")
        
        except grpc.RpcError as e:
            print(f"✗ Error checking status: {e.details()}")
    
    def get_payment_history(self):
        """Get payment history"""
        if not self.session_token:
            print("✗ Not logged in")
            return
        
        try:
            response = self.payment_stub.GetPaymentHistory(
                cloud_storage_pb2.GetPaymentHistoryRequest(
                    session_token=self.session_token,
                    limit=20
                )
            )
            
            if response.success:
                if not response.payments:
                    print("\n📜 No payment history yet")
                    print("   Purchase storage to see your transaction history here.")
                    return
                
                print("\n" + "=" * 80)
                print("PAYMENT HISTORY")
                print("=" * 80)
                
                for payment in response.payments:
                    status_icons = {
                        'completed': '✅',
                        'pending': '⏳',
                        'processing': '⚙️',
                        'failed': '❌',
                        'cancelled': '🚫'
                    }
                    
                    icon = status_icons.get(payment.status, '❓')
                    storage_gb = payment.storage_bytes / (1024**3)
                    
                    print(f"\n{icon} {payment.tier_name}")
                    print(f"   Amount: {payment.amount_xaf} XAF")
                    print(f"   Storage: {storage_gb:.2f} GB")
                    print(f"   Provider: {payment.provider}")
                    print(f"   Status: {payment.status}")
                    print(f"   Date: {payment.created_at[:19]}")
                    
                    if payment.completed_at:
                        print(f"   Completed: {payment.completed_at[:19]}")
                
                print("\n" + "=" * 80)
        
        except grpc.RpcError as e:
            print(f"✗ Error getting history: {e.details()}")
    
    def interactive_purchase(self):
        """Interactive purchase flow"""
        print("\n" + "=" * 80)
        print("PURCHASE ADDITIONAL STORAGE")
        print("=" * 80)
        
        # Show current storage
        self.show_current_storage()
        
        # Get tiers
        tiers = self.get_storage_tiers()
        if not tiers:
            return
        
        # Select tier
        while True:
            try:
                choice = input("\nSelect tier (1-{}) or 'q' to quit: ".format(len(tiers)))
                if choice.lower() == 'q':
                    return
                
                tier_index = int(choice) - 1
                if 0 <= tier_index < len(tiers):
                    selected_tier = tiers[tier_index]
                    break
                else:
                    print("✗ Invalid choice")
            except ValueError:
                print("✗ Please enter a number")
        
        # Select provider
        print("\nPayment Providers:")
        print("1. MTN Mobile Money")
        print("2. Orange Money")
        
        while True:
            provider_choice = input("\nSelect provider (1-2): ")
            if provider_choice == '1':
                provider = 'mtn_momo'
                break
            elif provider_choice == '2':
                provider = 'orange_money'
                break
            else:
                print("✗ Invalid choice")
        
        # Get phone number
        phone = input("\nEnter phone number (237XXXXXXXXX): ").strip()
        
        # Confirm
        print("\n" + "-" * 80)
        print("PURCHASE SUMMARY:")
        print(f"  Tier: {selected_tier.display_name}")
        print(f"  Storage: {selected_tier.storage_bytes / (1024**3):.2f} GB")
        print(f"  Amount: {selected_tier.price_xaf} XAF")
        print(f"  Provider: {provider.replace('_', ' ').title()}")
        print(f"  Phone: {phone}")
        print("-" * 80)
        
        confirm = input("\nProceed with payment? (yes/no): ")
        if confirm.lower() != 'yes':
            print("✗ Payment cancelled")
            return
        
        # Initiate payment
        payment_id = self.initiate_payment(selected_tier.tier_id, provider, phone)
        
        if payment_id:
            # Wait for user to complete payment
            input("\nPress Enter after completing payment on your phone...")
            
            # Check status
            print("\nChecking payment status...")
            self.check_payment_status(payment_id)
            
            # Show updated storage
            self.show_current_storage()
    
    def close(self):
        """Close connection"""
        self.channel.close()


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cloud Storage Payment Client')
    parser.add_argument('command', choices=['tiers', 'buy', 'history', 'status'],
                       help='Command to execute')
    parser.add_argument('--payment-id', help='Payment ID for status command')
    parser.add_argument('--email', help='User email for login')
    parser.add_argument('--server', default='localhost:50051', help='Server address')
    
    args = parser.parse_args()
    
    client = PaymentClient(args.server)
    
    try:
        if args.command == 'tiers':
            # List tiers (no login required)
            client.get_storage_tiers()
        
        elif args.command == 'buy':
            # Interactive purchase
            email = args.email or input("Enter your email: ")
            if client.login(email):
                client.interactive_purchase()
        
        elif args.command == 'history':
            # Payment history
            email = args.email or input("Enter your email: ")
            if client.login(email):
                client.get_payment_history()
        
        elif args.command == 'status':
            # Check payment status
            email = args.email or input("Enter your email: ")
            payment_id = args.payment_id or input("Enter payment ID: ")
            if client.login(email):
                client.check_payment_status(payment_id)
    
    finally:
        client.close()


if __name__ == '__main__':
    main()