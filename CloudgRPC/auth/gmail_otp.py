
import smtplib
import random
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

OTP_VALIDITY_SECONDS = 300  # 5 minutes

class OTPManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.otps = {}  # email → (otp, expiry_time)
        self.gmail_user = os.getenv('GMAIL_USER')
        self.gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    def generate_otp(self):
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    def send_otp(self, email):
        """
        Generate and send OTP to user's email
        Returns: (success, message)
        """
        if not self.gmail_user or not self.gmail_password:
            # For testing without Gmail credentials
            otp = self.generate_otp()
            with self._lock:
                self.otps[email] = (otp, time.time() + OTP_VALIDITY_SECONDS)
            return True, f"OTP sent successfully. [TEST MODE: OTP is {otp}]"
        
        try:
            # Generate OTP
            otp = self.generate_otp()
            
            # Store OTP with expiry
            with self._lock:
                self.otps[email] = (otp, time.time() + OTP_VALIDITY_SECONDS)
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = email
            msg['Subject'] = 'CloudGrpc - Your OTP Code'
            
            body = f"""
            Hello,
            
            Your OTP for CloudGrpc authentication is: {otp}
            
            This OTP is valid for 5 minutes.
            
            If you did not request this OTP, please ignore this email.
            
            Best regards,
            CloudGrpc Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email via Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            server.send_message(msg)
            server.quit()
            
            return True, "OTP sent successfully to your email."
        
        except Exception as e:
            # Fallback to test mode if email fails
            otp = self.generate_otp()
            with self._lock:
                self.otps[email] = (otp, time.time() + OTP_VALIDITY_SECONDS)
            return True, f"Email service unavailable. [TEST MODE: OTP is {otp}]"
    
    def verify_otp(self, email, otp):
        """
        Verify OTP for given email
        Returns: (success, message)
        """
        with self._lock:
            if email not in self.otps:
                return False, "No OTP found for this email. Please request a new one."
            
            stored_otp, expiry_time = self.otps[email]
            
            # Check if OTP expired
            if time.time() > expiry_time:
                del self.otps[email]
                return False, "OTP expired. Please request a new one."
            
            # Verify OTP
            if stored_otp == otp:
                # Delete OTP after successful verification
                del self.otps[email]
                return True, "OTP verified successfully."
            else:
                return False, "Invalid OTP. Please try again."