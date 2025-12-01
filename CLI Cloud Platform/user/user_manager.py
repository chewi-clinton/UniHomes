"""
User Manager - Handles user operations, sessions, and storage quotas
"""
import secrets
import threading
from datetime import datetime, timedelta
from db.models import User, Session
from db.database import get_db_session

PER_USER_ALLOCATION = 1_073_741_824  # 1 GB
SESSION_EXPIRY_HOURS = 24

class UserManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.verified_emails = {}  # email → expiry_time (for OTP window)
    
    def mark_email_verified(self, email):
        """Mark email as verified with 5-minute expiry"""
        with self._lock:
            self.verified_emails[email] = datetime.utcnow() + timedelta(minutes=5)
    
    def is_email_verified(self, email):
        """Check if email has been verified and is within validity window"""
        with self._lock:
            if email not in self.verified_emails:
                return False
            expiry_time = self.verified_emails[email]
            if datetime.utcnow() > expiry_time:
                del self.verified_emails[email]
                return False
            return True
    
    def user_exists(self, email):
        """Check if user already exists"""
        with get_db_session() as session:
            user = session.query(User).filter_by(email=email).first()
            return user is not None
    
    def enroll_user(self, email, name):
        """
        Enroll a new user with storage allocation
        Returns: (success, message, session_token, user_id)
        """
        # Check if email is verified
        if not self.is_email_verified(email):
            return False, "Email not verified. Please complete OTP verification first.", None, None
        
        # Check if user already exists
        if self.user_exists(email):
            return False, "User already enrolled. Please use Login option.", None, None
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        
        try:
            with get_db_session() as db_session:
                # Create new user
                user = User(
                    email=email,
                    name=name,
                    storage_allocated=PER_USER_ALLOCATION,
                    storage_used=0
                )
                db_session.add(user)
                db_session.flush()
                
                # Create session
                session = Session(
                    user_id=user.user_id,
                    session_token=session_token,
                    expires_at=datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)
                )
                db_session.add(session)
                db_session.flush()
                
                user_id = user.user_id
                
                # Remove from verified emails
                with self._lock:
                    if email in self.verified_emails:
                        del self.verified_emails[email]
                
                print(f"[USER] New user enrolled: {name} ({email})")
                return True, f"Successfully enrolled {name}. Allocated 1 GB storage.", session_token, user_id
        
        except Exception as e:
            print(f"[ERROR] Failed to enroll user: {e}")
            return False, f"Enrollment failed: {str(e)}", None, None
    
    def login_user(self, email):
        """
        Login an existing user and generate new session token
        Returns: (success, message, session_token, user_id)
        """
        # Check if email is verified
        if not self.is_email_verified(email):
            return False, "Email not verified. Please complete OTP verification.", None, None
        
        try:
            with get_db_session() as db_session:
                # Check if user exists
                user = db_session.query(User).filter_by(email=email).first()
                if not user:
                    return False, "User not enrolled. Please enroll first.", None, None
                
                # Generate new session token
                session_token = secrets.token_urlsafe(32)
                
                # Create new session
                session = Session(
                    user_id=user.user_id,
                    session_token=session_token,
                    expires_at=datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)
                )
                db_session.add(session)
                
                # Update last login
                user.last_login = datetime.utcnow()
                
                user_id = user.user_id
                user_name = user.name
                
                # Remove from verified emails
                with self._lock:
                    if email in self.verified_emails:
                        del self.verified_emails[email]
                
                print(f"[USER] User logged in: {user_name} ({email})")
                return True, f"Successfully logged in as {user_name}.", session_token, user_id
        
        except Exception as e:
            print(f"[ERROR] Failed to login user: {e}")
            return False, f"Login failed: {str(e)}", None, None
    
    def logout_user(self, session_token):
        """Logout user by invalidating session"""
        try:
            with get_db_session() as db_session:
                session = db_session.query(Session).filter_by(session_token=session_token).first()
                if session:
                    db_session.delete(session)
                    print(f"[USER] User logged out: {session.user_id}")
                    return True, "Successfully logged out."
                return False, "Invalid session token."
        except Exception as e:
            print(f"[ERROR] Failed to logout user: {e}")
            return False, f"Logout failed: {str(e)}"
    
    def validate_session(self, session_token):
        """
        Validate session token and return user
        Returns: user object or None
        """
        try:
            with get_db_session() as db_session:
                session = db_session.query(Session).filter_by(session_token=session_token).first()
                
                if not session:
                    return None
                
                # Check if session expired
                if datetime.utcnow() > session.expires_at:
                    db_session.delete(session)
                    return None
                
                # Update last activity
                session.last_activity = datetime.utcnow()
                
                # Get user
                user = db_session.query(User).filter_by(user_id=session.user_id).first()
                return user
        
        except Exception as e:
            print(f"[ERROR] Failed to validate session: {e}")
            return None
    
    def get_storage_info(self, session_token):
        """Get storage information for user"""
        user = self.validate_session(session_token)
        if not user:
            return None
        
        allocated = user.storage_allocated
        used = user.storage_used
        available = allocated - used
        usage_percentage = (used / allocated * 100) if allocated > 0 else 0
        
        return {
            'success': True,
            'user_id': user.user_id,
            'email': user.email,
            'name': user.name,
            'allocated': allocated,
            'used': used,
            'available': available,
            'usage_percentage': usage_percentage
        }
    
    def update_storage_usage(self, user_id, bytes_to_add):
        """Update storage usage for a user"""
        try:
            with get_db_session() as db_session:
                user = db_session.query(User).filter_by(user_id=user_id).first()
                if not user:
                    return False, "User not found"
                
                new_used = user.storage_used + bytes_to_add
                
                # Check if exceeds allocation
                if new_used > user.storage_allocated:
                    return False, "Storage quota exceeded"
                
                user.storage_used = new_used
                return True, "Storage updated"
        
        except Exception as e:
            print(f"[ERROR] Failed to update storage: {e}")
            return False, str(e)
    
    def check_storage_available(self, user_id, required_bytes):
        """Check if user has enough storage available"""
        try:
            with get_db_session() as db_session:
                user = db_session.query(User).filter_by(user_id=user_id).first()
                if not user:
                    return False
                
                available = user.storage_allocated - user.storage_used
                return available >= required_bytes
        
        except Exception as e:
            print(f"[ERROR] Failed to check storage: {e}")
            return False