"""
Database Initialization Script for Payment System
Create this file: backend/db/init_payment_tables.py

Run this script to create payment tables and populate with default tiers:
python backend/db/init_payment_tables.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import init_database, get_db_session
from db.models import StorageTier, Payment, StoragePurchase, PaymentWebhook


def create_default_storage_tiers():
    """Create default storage tiers"""
    default_tiers = [
        {
            'name': 'starter',
            'display_name': 'Starter Pack',
            'storage_bytes': 250 * 1024 * 1024,  # 250 MB
            'price_xaf': 500,  # 500 XAF (~$0.85 USD)
            'description': 'Perfect for light users - add 250 MB to your storage'
        },
        {
            'name': 'pro',
            'display_name': 'Pro Pack',
            'storage_bytes': 512 * 1024 * 1024,  # 512 MB
            'price_xaf': 900,  # 900 XAF (~$1.50 USD)
            'description': 'Great for regular users - add 512 MB to your storage'
        },
        {
            'name': 'premium',
            'display_name': 'Premium Pack',
            'storage_bytes': 1 * 1024 * 1024 * 1024,  # 1 GB
            'price_xaf': 1500,  # 1500 XAF (~$2.50 USD)
            'description': 'Double your storage - add 1 GB'
        },
        {
            'name': 'ultimate',
            'display_name': 'Ultimate Pack',
            'storage_bytes': 2 * 1024 * 1024 * 1024,  # 2 GB
            'price_xaf': 2500,  # 2500 XAF (~$4.20 USD)
            'description': 'Maximum capacity - add 2 GB to your storage'
        }
    ]
    
    with get_db_session() as session:
        # Check if tiers already exist
        existing_count = session.query(StorageTier).count()
        
        if existing_count > 0:
            print(f"[INIT] {existing_count} storage tiers already exist. Skipping creation.")
            return
        
        print("[INIT] Creating default storage tiers...")
        
        for tier_data in default_tiers:
            tier = StorageTier(
                name=tier_data['name'],
                display_name=tier_data['display_name'],
                storage_bytes=tier_data['storage_bytes'],
                price_xaf=tier_data['price_xaf'],
                description=tier_data['description'],
                is_active=True
            )
            session.add(tier)
            
            print(f"  ✓ {tier.display_name}: {tier.storage_bytes / (1024**3):.2f} GB for {tier.price_xaf} XAF")
        
        session.commit()
        print("[INIT] ✓ Default storage tiers created successfully")


def display_tiers():
    """Display all storage tiers"""
    with get_db_session() as session:
        tiers = session.query(StorageTier).filter_by(is_active=True).order_by(StorageTier.price_xaf).all()
        
        if not tiers:
            print("[INFO] No storage tiers found")
            return
        
        print("\n" + "=" * 80)
        print("STORAGE TIERS")
        print("=" * 80)
        
        for tier in tiers:
            storage_gb = tier.storage_bytes / (1024**3)
            storage_mb = tier.storage_bytes / (1024**2)
            
            print(f"\n{tier.display_name} ({tier.name})")
            print(f"  ID: {tier.tier_id}")
            print(f"  Storage: {storage_mb:.0f} MB ({storage_gb:.2f} GB)")
            print(f"  Price: {tier.price_xaf} XAF")
            print(f"  Status: {'Active' if tier.is_active else 'Inactive'}")
            print(f"  Description: {tier.description}")
        
        print("\n" + "=" * 80)


def main():
    """Main initialization"""
    print("=" * 80)
    print("PAYMENT SYSTEM INITIALIZATION")
    print("=" * 80)
    
    # Initialize database (creates all tables including payment tables)
    print("\n[INIT] Initializing database...")
    init_database()
    print("[INIT] ✓ Database initialized")
    
    # Create default storage tiers
    create_default_storage_tiers()
    
    # Display tiers
    display_tiers()
    
    print("\n" + "=" * 80)
    print("INITIALIZATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Configure Campay credentials in .env file")
    print("2. Start the cloud server")
    print("3. Users can now purchase additional storage!")
    print("\n")


if __name__ == '__main__':
    main()