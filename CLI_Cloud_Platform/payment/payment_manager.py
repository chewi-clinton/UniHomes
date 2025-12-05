"""
Payment Manager - Handles payment processing and storage allocation
"""
import secrets
import threading
from datetime import datetime
from typing import Tuple, List, Optional, Dict
from db.models import (
    StorageTier, Payment, StoragePurchase, PaymentWebhook, User
)
from db.database import get_db_session
from payment.campay_client import campay_client


class PaymentManager:
    """Manages payment operations and storage purchases"""
    
    def __init__(self):
        self._lock = threading.Lock()
    
    def get_storage_tiers(self) -> List[Dict]:
        """Get all active storage tiers"""
        try:
            with get_db_session() as session:
                tiers = session.query(StorageTier).filter_by(is_active=True).order_by(StorageTier.price_xaf).all()
                
                return [{
                    'tier_id': tier.tier_id,
                    'name': tier.name,
                    'display_name': tier.display_name,
                    'storage_bytes': tier.storage_bytes,
                    'storage_gb': tier.storage_bytes / (1024**3),
                    'price_xaf': tier.price_xaf,
                    'description': tier.description
                } for tier in tiers]
        
        except Exception as e:
            print(f"[PAYMENT] Failed to get tiers: {e}")
            return []
    
    def initiate_payment(
        self,
        user_id: str,
        tier_id: str,
        provider: str,
        phone_number: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Initiate a payment transaction
        
        Returns:
            (success, message, payment_data)
        """
        try:
            with get_db_session() as session:
                # Get user
                user = session.query(User).filter_by(user_id=user_id).first()
                if not user:
                    return False, "User not found", None
                
                # Get tier
                tier = session.query(StorageTier).filter_by(tier_id=tier_id, is_active=True).first()
                if not tier:
                    return False, "Invalid storage tier", None
                
                # Validate phone number
                provider_name = "MTN" if provider == "mtn_momo" else "ORANGE"
                if not campay_client.validate_phone_number(phone_number, provider_name):
                    return False, f"Invalid {provider_name} phone number format", None
                
                # Generate transaction reference
                transaction_ref = f"CS-{secrets.token_hex(8).upper()}"
                
                # DEMO MODE: Check if Campay is in demo mode
                actual_amount = tier.price_xaf
                is_demo = campay_client.is_demo
                
                # Create payment record with ACTUAL amount (what user thinks they're paying)
                payment = Payment(
                    user_id=user_id,
                    tier_id=tier_id,
                    amount_xaf=actual_amount,  # Store the REAL price
                    storage_bytes=tier.storage_bytes,
                    provider=provider,
                    phone_number=phone_number,
                    transaction_ref=transaction_ref,
                    status='pending'
                )
                session.add(payment)
                session.flush()
                
                payment_id = payment.payment_id
                
                print(f"[PAYMENT] Initiating payment {payment_id} for user {user.email}")
                print(f"[PAYMENT] Amount: {tier.price_xaf} XAF, Storage: {tier.storage_bytes / (1024**3):.2f} GB")
                
                if is_demo:
                    print(f"[PAYMENT] 🧪 DEMO MODE: User sees {actual_amount} XAF but will be charged {campay_client.demo_amount} XAF")
                
                # Initiate payment with Campay (it will handle demo amount internally)
                success, message, campay_data = campay_client.initiate_collection(
                    amount=tier.price_xaf,  # Pass the real amount
                    phone_number=phone_number,
                    external_reference=transaction_ref,
                    description=f"Storage purchase: {tier.display_name}",
                    provider=provider_name
                )
                
                if success and campay_data:
                    # Update payment with Campay reference
                    payment.external_ref = campay_data.get('reference')
                    payment.status = 'processing'
                    
                    # Store demo mode info in metadata
                    payment.metadata = {
                        'raw_response': campay_data.get('raw_response', {}),
                        'is_demo': campay_data.get('is_demo', False),
                        'actual_amount': campay_data.get('actual_amount', actual_amount),
                        'charged_amount': campay_data.get('charged_amount', actual_amount)
                    }
                    
                    payment.processed_at = datetime.utcnow()
                    
                    session.commit()
                    
                    print(f"[PAYMENT] ✓ Payment initiated: {payment_id}")
                    print(f"[PAYMENT] Campay ref: {payment.external_ref}")
                    
                    if is_demo:
                        print(f"[PAYMENT] 🧪 Demo: Showing {actual_amount} XAF, Charging {campay_client.demo_amount} XAF")
                    
                    return True, "Payment initiated. Please complete on your phone.", {
                        'payment_id': payment_id,
                        'transaction_ref': transaction_ref,
                        'amount_xaf': actual_amount,  # Return REAL amount to show user
                        'campay_ref': payment.external_ref,
                        'is_demo': is_demo
                    }
                else:
                    # Payment initiation failed
                    payment.status = 'failed'
                    payment.error_message = message
                    session.commit()
                    
                    print(f"[PAYMENT] ✗ Payment initiation failed: {message}")
                    return False, message, None
        
        except Exception as e:
            print(f"[PAYMENT] Error initiating payment: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Payment error: {str(e)}", None
    
    def check_payment_status(self, payment_id: str, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Check payment status and process if completed"""
        try:
            with get_db_session() as session:
                payment = session.query(Payment).filter_by(
                    payment_id=payment_id,
                    user_id=user_id
                ).first()
                
                if not payment:
                    return False, "Payment not found", None
                
                if payment.status in ['completed', 'failed', 'cancelled']:
                    return True, payment.status, {
                        'payment_id': payment_id,
                        'status': payment.status,
                        'amount_xaf': payment.amount_xaf,
                        'storage_bytes': payment.storage_bytes if payment.status == 'completed' else 0,
                        'message': payment.error_message if payment.error_message else 'Payment ' + payment.status
                    }
                
                if payment.external_ref:
                    success, campay_status, campay_data = campay_client.check_transaction_status(
                        payment.external_ref
                    )
                    
                    if success:
                        print(f"[PAYMENT] Campay status for {payment_id}: {campay_status}")
                        
                        if campay_status == 'SUCCESSFUL':
                            self._process_successful_payment(session, payment)
                            return True, 'completed', {
                                'payment_id': payment_id,
                                'status': 'completed',
                                'amount_xaf': payment.amount_xaf,
                                'storage_bytes': payment.storage_bytes,
                                'message': 'Payment completed successfully. Storage has been added to your account.'
                            }
                        
                        elif campay_status == 'FAILED':
                            payment.status = 'failed'
                            payment.error_message = 'Payment failed on provider side'
                            if campay_data:
                                payment.payment_metadata = campay_data
                            session.commit()
                        
                        elif campay_status == 'PENDING':
                            payment.status = 'processing'
                            session.commit()
                
                return True, payment.status, {
                    'payment_id': payment_id,
                    'status': payment.status,
                    'amount_xaf': payment.amount_xaf,
                    'storage_bytes': 0,
                    'message': self._get_status_message(payment.status)
                }
        
        except Exception as e:
            print(f"[PAYMENT] Error checking status: {e}")
            import traceback
            traceback.print_exc()
            return False, "Error checking payment status", None
    
    def _process_successful_payment(self, session, payment: Payment):
        """Process a successful payment and allocate storage"""
        try:
            user = session.query(User).filter_by(user_id=payment.user_id).first()
            if not user:
                raise Exception("User not found")
            
            old_allocation = user.storage_allocated
            user.storage_allocated += payment.storage_bytes
            
            payment.status = 'completed'
            payment.completed_at = datetime.utcnow()
            
            purchase = StoragePurchase(
                user_id=payment.user_id,
                payment_id=payment.payment_id,
                storage_bytes=payment.storage_bytes,
                previous_allocation=old_allocation,
                new_allocation=user.storage_allocated
            )
            session.add(purchase)
            session.commit()
            
            print(f"[PAYMENT] Storage allocated to user {user.email}")
            print(f"[PAYMENT] Old: {old_allocation / (1024**3):.2f} GB → New: {user.storage_allocated / (1024**3):.2f} GB")
        
        except Exception as e:
            print(f"[PAYMENT] Error processing payment: {e}")
            raise
    
    def _get_status_message(self, status: str) -> str:
        """Get user-friendly status message"""
        messages = {
            'pending': 'Payment is pending. Please complete on your phone.',
            'processing': 'Payment is being processed. This may take a few moments.',
            'completed': 'Payment completed successfully.',
            'failed': 'Payment failed. Please try again.',
            'cancelled': 'Payment was cancelled.'
        }
        return messages.get(status, 'Unknown status')
    
    def get_payment_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get payment history for a user"""
        try:
            with get_db_session() as session:
                payments = session.query(Payment, StorageTier).join(
                    StorageTier, Payment.tier_id == StorageTier.tier_id
                ).filter(
                    Payment.user_id == user_id
                ).order_by(
                    Payment.created_at.desc()
                ).limit(limit).all()
                
                return [{
                    'payment_id': p.payment_id,
                    'tier_name': t.display_name,
                    'amount_xaf': p.amount_xaf,
                    'storage_bytes': p.storage_bytes,
                    'storage_gb': p.storage_bytes / (1024**3),
                    'provider': p.provider,
                    'status': p.status,
                    'transaction_ref': p.transaction_ref,
                    'created_at': p.created_at.isoformat(),
                    'completed_at': p.completed_at.isoformat() if p.completed_at else None
                } for p, t in payments]
        
        except Exception as e:
            print(f"[PAYMENT] Error getting history: {e}")
            return []
    
    def cancel_payment(self, payment_id: str, user_id: str) -> Tuple[bool, str]:
        """Cancel a pending payment"""
        try:
            with get_db_session() as session:
                payment = session.query(Payment).filter_by(
                    payment_id=payment_id,
                    user_id=user_id
                ).first()
                
                if not payment:
                    return False, "Payment not found"
                
                if payment.status not in ['pending', 'processing']:
                    return False, f"Cannot cancel payment with status: {payment.status}"
                
                payment.status = 'cancelled'
                session.commit()
                
                print(f"[PAYMENT] Payment {payment_id} cancelled")
                return True, "Payment cancelled successfully"
        
        except Exception as e:
            print(f"[PAYMENT] Error cancelling payment: {e}")
            return False, f"Failed to cancel payment: {str(e)}"
    
    def process_webhook(self, external_ref: str, status: str, raw_data: Dict) -> Tuple[bool, str]:
        """Process webhook callback from Campay"""
        try:
            with get_db_session() as session:
                webhook = PaymentWebhook(
                    external_ref=external_ref,
                    status=status,
                    raw_data=raw_data
                )
                session.add(webhook)
                
                payment = session.query(Payment).filter_by(external_ref=external_ref).first()
                
                if payment:
                    webhook.payment_id = payment.payment_id
                    
                    print(f"[WEBHOOK] Processing for payment {payment.payment_id}: {status}")
                    
                    if status == 'SUCCESSFUL' and payment.status != 'completed':
                        self._process_successful_payment(session, payment)
                        webhook.processed = True
                        webhook.processed_at = datetime.utcnow()
                        session.commit()
                        return True, "Payment processed successfully"
                    
                    elif status == 'FAILED':
                        payment.status = 'failed'
                        payment.error_message = 'Payment failed (webhook)'
                        payment.payment_metadata = raw_data
                        webhook.processed = True
                        webhook.processed_at = datetime.utcnow()
                        session.commit()
                        return True, "Payment marked as failed"
                    
                    else:
                        session.commit()
                        return True, f"Webhook received for status: {status}"
                else:
                    print(f"[WEBHOOK] Payment not found for ref: {external_ref}")
                    session.commit()
                    return False, "Payment not found"
        
        except Exception as e:
            print(f"[WEBHOOK] Error processing webhook: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Webhook processing error: {str(e)}"
    
    # Admin methods
    def get_payment_stats(self) -> Dict:
        """Get payment statistics (admin)"""
        try:
            with get_db_session() as session:
                total = session.query(Payment).count()
                completed = session.query(Payment).filter_by(status='completed').count()
                pending = session.query(Payment).filter(
                    Payment.status.in_(['pending', 'processing'])
                ).count()
                failed = session.query(Payment).filter_by(status='failed').count()
                
                completed_payments = session.query(Payment).filter_by(status='completed').all()
                total_revenue = sum(p.amount_xaf for p in completed_payments)
                total_storage_sold = sum(p.storage_bytes for p in completed_payments)
                
                return {
                    'total_payments': total,
                    'completed_payments': completed,
                    'pending_payments': pending,
                    'failed_payments': failed,
                    'total_revenue_xaf': total_revenue,
                    'total_storage_sold_bytes': total_storage_sold,
                    'total_storage_sold_gb': total_storage_sold / (1024**3)
                }
        
        except Exception as e:
            print(f"[PAYMENT] Error getting stats: {e}")
            return {}
    
    def get_all_payments(self, limit: int = 100, status_filter: Optional[str] = None) -> List[Dict]:
        """Get all payments (admin)"""
        try:
            with get_db_session() as session:
                query = session.query(Payment, User, StorageTier).join(
                    User, Payment.user_id == User.user_id
                ).join(
                    StorageTier, Payment.tier_id == StorageTier.tier_id
                )
                
                if status_filter:
                    query = query.filter(Payment.status == status_filter)
                
                payments = query.order_by(Payment.created_at.desc()).limit(limit).all()
                
                return [{
                    'payment_id': p.payment_id,
                    'user_email': u.email,
                    'user_name': u.name,
                    'tier_name': t.display_name,
                    'amount_xaf': p.amount_xaf,
                    'storage_bytes': p.storage_bytes,
                    'provider': p.provider,
                    'phone_number': p.phone_number,
                    'status': p.status,
                    'transaction_ref': p.transaction_ref,
                    'external_ref': p.external_ref,
                    'created_at': p.created_at.isoformat(),
                    'completed_at': p.completed_at.isoformat() if p.completed_at else None
                } for p, u, t in payments]
        
        except Exception as e:
            print(f"[PAYMENT] Error getting all payments: {e}")
            return []


# Global instance
payment_manager = PaymentManager()