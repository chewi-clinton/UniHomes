import threading
import secrets
import time

GLOBAL_STORAGE_BYTES = 6_000_000_000  # 6 GB
PER_USER_ALLOCATION = 1_000_000_000   # 1 GB
MAX_USERS = 6
OTP_VALIDITY_SECONDS = 300  # 5 minutes

class UserManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.global_used = 0
        self.users = {}  # email → { name, token, allocated }
        self.verified_emails = {}  # email → expiry_time (for OTP window)
    
    def is_email_verified(self, email):
        """Check if email has been verified and is within validity window"""
        with self._lock:
            if email not in self.verified_emails:
                return False
            expiry_time = self.verified_emails[email]
            if time.time() > expiry_time:
                # OTP expired, remove it
                del self.verified_emails[email]
                return False
            return True
    
    def mark_email_verified(self, email):
        """Mark email as verified with 5-minute expiry"""
        with self._lock:
            self.verified_emails[email] = time.time() + OTP_VALIDITY_SECONDS
    
    def can_allocate_new_user(self):
        """Check if there's enough global storage for a new user"""
        with self._lock:
            return (self.global_used + PER_USER_ALLOCATION <= GLOBAL_STORAGE_BYTES and 
                    len(self.users) < MAX_USERS)
    
    def enroll_user(self, email, name):
        """
        Enroll a new user with storage allocation
        Returns: (success, message, token)
        """
        with self._lock:
            # Check if email is verified
            if email not in self.verified_emails:
                return False, "Email not verified. Please login first.", None
            
            # Check if OTP is still valid
            if time.time() > self.verified_emails[email]:
                del self.verified_emails[email]
                return False, "OTP expired. Please login again.", None
            
            # Check if user already exists
            if email in self.users:
                return False, "User already enrolled.", None
            
            # Check if we can allocate storage
            if not (self.global_used + PER_USER_ALLOCATION <= GLOBAL_STORAGE_BYTES):
                return False, "System storage exhausted. Cannot allocate storage for new users.", None
            
            if len(self.users) >= MAX_USERS:
                return False, "System storage exhausted. Cannot allocate storage for new users.", None
            
            # Generate session token
            token = secrets.token_urlsafe(32)
            
            # Allocate storage and create user
            self.global_used += PER_USER_ALLOCATION
            self.users[email] = {
                'name': name,
                'token': token,
                'allocated': PER_USER_ALLOCATION
            }
            
            # Remove from verified emails (one-time use)
            del self.verified_emails[email]
            
            return True, f"Successfully enrolled {name}. Allocated 1 GB storage.", token
    
    def get_user_by_token(self, token):
        """Get user information by session token"""
        with self._lock:
            for email, user_data in self.users.items():
                if user_data['token'] == token:
                    return {
                        'email': email,
                        'name': user_data['name'],
                        'allocated': user_data['allocated']
                    }
            return None
    
    def get_storage_info(self):
        """Get current storage usage information"""
        with self._lock:
            return {
                'global_capacity': GLOBAL_STORAGE_BYTES,
                'global_used': self.global_used,
                'global_available': GLOBAL_STORAGE_BYTES - self.global_used,
                'total_users': len(self.users),
                'max_users': MAX_USERS
            }