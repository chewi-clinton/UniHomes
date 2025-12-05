"""
Campay API Integration for Mobile Money Payments - WITH DEMO MODE
Update your backend/payment/campay_client.py with this version
"""
import requests
import os
import json
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional


class CampayClient:
    """Client for Campay API integration"""
    
    def __init__(self):
        self.app_username = os.getenv('CAMPAY_APP_USERNAME')
        self.app_password = os.getenv('CAMPAY_APP_PASSWORD')
        self.base_url = os.getenv('CAMPAY_BASE_URL', 'https://demo.campay.net/api')
        self.token = None
        self.token_expires = None
        
        # DEMO MODE: Detect if using demo environment
        self.is_demo = 'demo' in self.base_url.lower()
        self.demo_amount = 10  # Maximum amount for demo: 10 XAF
        
        if not self.app_username or not self.app_password:
            print("[CAMPAY] Warning: Campay credentials not configured")
        
        if self.is_demo:
            print(f"[CAMPAY] 🧪 DEMO MODE ENABLED - All payments will be charged {self.demo_amount} XAF")
    
    def _get_token(self) -> Optional[str]:
        """Get or refresh authentication token"""
        # Check if we have a valid token
        if self.token and self.token_expires and datetime.now() < self.token_expires:
            return self.token
        
        # Get new token
        try:
            response = requests.post(
                f'{self.base_url}/token/',
                json={
                    'username': self.app_username,
                    'password': self.app_password
                },
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                # Token expires in 24 hours, refresh 1 hour before
                self.token_expires = datetime.now() + timedelta(hours=23)
                print(f"[CAMPAY] ✓ Token obtained successfully")
                return self.token
            else:
                print(f"[CAMPAY] ✗ Failed to get token: {response.text}")
                return None
        
        except Exception as e:
            print(f"[CAMPAY] ✗ Token request error: {e}")
            return None
    
    def initiate_collection(
        self,
        amount: int,
        phone_number: str,
        external_reference: str,
        description: str = "Storage purchase",
        provider: str = "MTN"
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Initiate a payment collection
        
        Args:
            amount: Amount in XAF (ACTUAL amount user is paying)
            phone_number: Customer phone number (237XXXXXXXXX format)
            external_reference: Your internal transaction reference
            description: Payment description
            provider: "MTN" or "ORANGE"
        
        Returns:
            (success, message, data)
        """
        token = self._get_token()
        if not token:
            return False, "Failed to authenticate with Campay", None
        
        # Format phone number (remove spaces, ensure country code)
        phone = phone_number.replace(' ', '').replace('+', '')
        if not phone.startswith('237'):
            phone = '237' + phone
        
        # DEMO MODE: Use demo amount but keep real amount in metadata
        actual_amount = amount
        charge_amount = self.demo_amount if self.is_demo else amount
        
        if self.is_demo and amount > self.demo_amount:
            print(f"[CAMPAY] 🧪 Demo Mode: Showing {actual_amount} XAF but charging {charge_amount} XAF")
            description = f"{description} (Demo: {actual_amount} XAF)"
        
        try:
            payload = {
                "amount": str(charge_amount),  # Charge demo amount
                "currency": "XAF",
                "from": phone,
                "description": description,
                "external_reference": external_reference
            }
            
            print(f"[CAMPAY] Initiating collection: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f'{self.base_url}/collect/',
                json=payload,
                headers={
                    'Authorization': f'Token {token}',
                    'Content-Type': 'application/json'
                }
            )
            
            print(f"[CAMPAY] Response status: {response.status_code}")
            print(f"[CAMPAY] Response body: {response.text}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # Campay returns reference in the response
                campay_ref = data.get('reference')
                
                result_data = {
                    'reference': campay_ref,
                    'status': data.get('status', 'PENDING'),
                    'operator': data.get('operator'),
                    'raw_response': data,
                    'actual_amount': actual_amount,  # Store real amount
                    'charged_amount': charge_amount,  # Store what was actually charged
                    'is_demo': self.is_demo
                }
                
                return True, "Payment initiated successfully", result_data
            else:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    pass
                
                return False, f"Payment initiation failed: {error_msg}", None
        
        except Exception as e:
            print(f"[CAMPAY] ✗ Collection error: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Payment error: {str(e)}", None
    
    def check_transaction_status(self, reference: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Check the status of a transaction
        
        Args:
            reference: Campay transaction reference
        
        Returns:
            (success, status, data)
        """
        token = self._get_token()
        if not token:
            return False, "UNKNOWN", None
        
        try:
            response = requests.get(
                f'{self.base_url}/transaction/{reference}/',
                headers={
                    'Authorization': f'Token {token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'UNKNOWN')
                
                # Campay statuses: SUCCESSFUL, FAILED, PENDING
                return True, status, data
            else:
                return False, "UNKNOWN", None
        
        except Exception as e:
            print(f"[CAMPAY] ✗ Status check error: {e}")
            return False, "UNKNOWN", None
    
    def get_balance(self) -> Optional[Dict]:
        """Get merchant balance"""
        token = self._get_token()
        if not token:
            return None
        
        try:
            response = requests.get(
                f'{self.base_url}/balance/',
                headers={
                    'Authorization': f'Token {token}'
                }
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        
        except Exception as e:
            print(f"[CAMPAY] ✗ Balance check error: {e}")
            return None
    
    def validate_phone_number(self, phone: str, provider: str = "MTN") -> bool:
        """
        Validate phone number format for Cameroon
        
        Args:
            phone: Phone number
            provider: "MTN" or "ORANGE"
        
        Returns:
            True if valid
        """
        # Remove spaces and + sign
        phone = phone.replace(' ', '').replace('+', '')
        
        # Check if it starts with 237 (Cameroon code)
        if phone.startswith('237'):
            phone = phone[3:]
        
        # Check if it's 9 digits
        if len(phone) != 9:
            return False
        
        # MTN prefixes: 67, 650-654, 680-683
        # Orange prefixes: 69, 655-659
        if provider.upper() == "MTN":
            mtn_prefixes = ['67', '650', '651', '652', '653', '654', '680', '681', '682', '683']
            return any(phone.startswith(prefix) for prefix in mtn_prefixes)
        
        elif provider.upper() == "ORANGE":
            orange_prefixes = ['69', '655', '656', '657', '658', '659']
            return any(phone.startswith(prefix) for prefix in orange_prefixes)
        
        return False


# Create a global instance
campay_client = CampayClient()