"""
REST API Routes for Payment System
Create this file: backend/rest_api/app/payment/routes.py
"""
from flask import Blueprint, request, jsonify
from app.utils.grpc_client import get_grpc_client
from app.models.response import success_response, error_response
import generated.cloud_storage_pb2 as cloud_storage_pb2
import grpc

payment_bp = Blueprint('payment', __name__)

def get_session_token():
    """Extract session token from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    return auth_header.split(' ')[1]


@payment_bp.route('/tiers', methods=['GET'])
def get_storage_tiers():
    """Get all available storage tiers"""
    client = get_grpc_client()
    
    try:
        response = client.payment_stub.GetStorageTiers(
            cloud_storage_pb2.GetStorageTiersRequest()
        )
        
        if response.success:
            tiers = [{
                'tier_id': t.tier_id,
                'name': t.name,
                'display_name': t.display_name,
                'storage_bytes': t.storage_bytes,
                'storage_gb': t.storage_bytes / (1024**3),
                'storage_mb': t.storage_bytes / (1024**2),
                'price_xaf': t.price_xaf,
                'description': t.description
            } for t in response.tiers]
            
            return success_response({'tiers': tiers})
        else:
            return error_response("Failed to get storage tiers"), 400
    
    except grpc.RpcError as e:
        return error_response(f"gRPC error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to get tiers: {str(e)}"), 500


@payment_bp.route('/initiate', methods=['POST'])
def initiate_payment():
    """Initiate a payment for storage purchase"""
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
    
    data = request.get_json()
    tier_id = data.get('tier_id')
    provider = data.get('provider')  # mtn_momo or orange_money
    phone_number = data.get('phone_number')
    
    if not all([tier_id, provider, phone_number]):
        return error_response("Missing required fields: tier_id, provider, phone_number"), 400
    
    # Validate provider
    if provider not in ['mtn_momo', 'orange_money']:
        return error_response("Invalid provider. Must be 'mtn_momo' or 'orange_money'"), 400
    
    client = get_grpc_client()
    
    try:
        response = client.payment_stub.InitiatePayment(
            cloud_storage_pb2.InitiatePaymentRequest(
                session_token=session_token,
                tier_id=tier_id,
                provider=provider,
                phone_number=phone_number
            )
        )
        
        if response.success:
            return success_response({
                'payment_id': response.payment_id,
                'transaction_ref': response.transaction_ref,
                'amount_xaf': response.amount_xaf,
                'payment_url': response.payment_url,
                'message': response.message
            }, message=response.message)
        else:
            return error_response(response.message), 400
    
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            return error_response("Invalid session"), 401
        return error_response(f"Payment error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to initiate payment: {str(e)}"), 500


@payment_bp.route('/status/<payment_id>', methods=['GET'])
def check_payment_status(payment_id):
    """Check the status of a payment"""
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
    
    client = get_grpc_client()
    
    try:
        response = client.payment_stub.CheckPaymentStatus(
            cloud_storage_pb2.CheckPaymentStatusRequest(
                session_token=session_token,
                payment_id=payment_id
            )
        )
        
        if response.success:
            return success_response({
                'payment_id': response.payment_id,
                'status': response.status,
                'storage_added': response.storage_added,
                'storage_added_gb': response.storage_added / (1024**3) if response.storage_added > 0 else 0,
                'message': response.message
            })
        else:
            return error_response(response.message), 400
    
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            return error_response("Invalid session"), 401
        return error_response(f"Status check error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to check status: {str(e)}"), 500


@payment_bp.route('/history', methods=['GET'])
def get_payment_history():
    """Get payment history for the authenticated user"""
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
    
    limit = request.args.get('limit', 50, type=int)
    
    client = get_grpc_client()
    
    try:
        response = client.payment_stub.GetPaymentHistory(
            cloud_storage_pb2.GetPaymentHistoryRequest(
                session_token=session_token,
                limit=limit
            )
        )
        
        if response.success:
            payments = [{
                'payment_id': p.payment_id,
                'tier_name': p.tier_name,
                'amount_xaf': p.amount_xaf,
                'storage_bytes': p.storage_bytes,
                'storage_gb': p.storage_bytes / (1024**3),
                'provider': p.provider,
                'status': p.status,
                'created_at': p.created_at,
                'completed_at': p.completed_at
            } for p in response.payments]
            
            return success_response({'payments': payments})
        else:
            return error_response("Failed to get payment history"), 400
    
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            return error_response("Invalid session"), 401
        return error_response(f"History error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to get history: {str(e)}"), 500


@payment_bp.route('/cancel/<payment_id>', methods=['POST'])
def cancel_payment(payment_id):
    """Cancel a pending payment"""
    session_token = get_session_token()
    if not session_token:
        return error_response("Authentication required"), 401
    
    client = get_grpc_client()
    
    try:
        response = client.payment_stub.CancelPayment(
            cloud_storage_pb2.CancelPaymentRequest(
                session_token=session_token,
                payment_id=payment_id
            )
        )
        
        if response.success:
            return success_response({}, message=response.message)
        else:
            return error_response(response.message), 400
    
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            return error_response("Invalid session"), 401
        return error_response(f"Cancel error: {e.details()}"), 500
    except Exception as e:
        return error_response(f"Failed to cancel payment: {str(e)}"), 500


@payment_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """
    Webhook endpoint for Campay payment notifications
    This should be publicly accessible (no authentication required)
    """
    data = request.get_json()
    
    if not data:
        return error_response("No data provided"), 400
    
    external_ref = data.get('reference')
    status = data.get('status')
    
    if not all([external_ref, status]):
        return error_response("Missing required fields"), 400
    
    print(f"[WEBHOOK] Received: ref={external_ref}, status={status}")
    
    client = get_grpc_client()
    
    try:
        import json
        response = client.payment_stub.ProcessWebhook(
            cloud_storage_pb2.WebhookRequest(
                external_ref=external_ref,
                status=status,
                raw_data=json.dumps(data)
            )
        )
        
        if response.success:
            return success_response({}, message=response.message)
        else:
            return error_response(response.message), 400
    
    except Exception as e:
        print(f"[WEBHOOK] Error: {e}")
        return error_response(f"Webhook error: {str(e)}"), 500


# ============================================================================
# Admin Payment Endpoints
# ============================================================================

def verify_admin_key(request):
    """Verify admin key from request headers"""
    admin_key = request.headers.get('X-Admin-Key')
    if not admin_key:
        return False
    # Compare with configured admin key
    from flask import current_app
    expected_key = current_app.config.get('ADMIN_KEY')
    return admin_key.strip() == expected_key.strip()


@payment_bp.route('/admin/stats', methods=['GET'])
def get_payment_stats():
    """Get payment statistics (admin only)"""
    if not verify_admin_key(request):
        return error_response("Unauthorized"), 401
    
    admin_key = request.headers.get('X-Admin-Key')
    client = get_grpc_client()
    
    try:
        response = client.admin_stub.GetPaymentStats(
            cloud_storage_pb2.PaymentStatsRequest(admin_key=admin_key)
        )
        
        if response.success:
            return success_response({
                'total_payments': response.total_payments,
                'completed_payments': response.completed_payments,
                'pending_payments': response.pending_payments,
                'failed_payments': response.failed_payments,
                'total_revenue_xaf': response.total_revenue_xaf,
                'total_storage_sold_bytes': response.total_storage_sold_bytes,
                'total_storage_sold_gb': response.total_storage_sold_bytes / (1024**3)
            })
        else:
            return error_response("Failed to get stats"), 400
    
    except Exception as e:
        return error_response(f"Failed to get payment stats: {str(e)}"), 500


@payment_bp.route('/admin/payments', methods=['GET'])
def get_all_payments():
    """Get all payments (admin only)"""
    if not verify_admin_key(request):
        return error_response("Unauthorized"), 401
    
    admin_key = request.headers.get('X-Admin-Key')
    limit = request.args.get('limit', 100, type=int)
    status_filter = request.args.get('status', '')
    
    client = get_grpc_client()
    
    try:
        response = client.admin_stub.GetAllPayments(
            cloud_storage_pb2.GetAllPaymentsRequest(
                admin_key=admin_key,
                limit=limit,
                status_filter=status_filter
            )
        )
        
        if response.success:
            payments = [{
                'payment_id': p.payment_id,
                'user_email': p.user_email,
                'tier_name': p.tier_name,
                'amount_xaf': p.amount_xaf,
                'storage_bytes': p.storage_bytes,
                'storage_gb': p.storage_bytes / (1024**3),
                'provider': p.provider,
                'phone_number': p.phone_number,
                'status': p.status,
                'transaction_ref': p.transaction_ref,
                'created_at': p.created_at,
                'completed_at': p.completed_at
            } for p in response.payments]
            
            return success_response({'payments': payments})
        else:
            return error_response("Failed to get payments"), 400
    
    except Exception as e:
        return error_response(f"Failed to get payments: {str(e)}"), 500