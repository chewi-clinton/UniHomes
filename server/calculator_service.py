import grpc
from concurrent import futures
import sys
import os

# Add parent directory to path to import generated modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from generated import calculator_pb2
from generated import calculator_pb2_grpc
from auth.gmail_otp import OTPManager
from user.user_manager import UserManager

# Initialize managers
otp_manager = OTPManager()
user_manager = UserManager()

class AuthServiceServicer(calculator_pb2_grpc.AuthServiceServicer):
    """Implementation of AuthService"""
    
    def Login(self, request, context):
        """Send OTP to user's email"""
        email = request.email
        
        if not email or '@' not in email:
            return calculator_pb2.LoginResponse(
                success=False,
                message="Invalid email address."
            )
        
        # Send OTP
        success, message = otp_manager.send_otp(email)
        
        if success:
            # Mark email as verified (pending OTP confirmation)
            user_manager.mark_email_verified(email)
        
        return calculator_pb2.LoginResponse(
            success=success,
            message=message
        )
    
    def VerifyOtp(self, request, context):
        """Verify OTP entered by user"""
        email = request.email
        otp = request.otp
        
        success, message = otp_manager.verify_otp(email, otp)
        
        return calculator_pb2.VerifyOtpResponse(
            success=success,
            message=message
        )
    
    def Enroll(self, request, context):
        """Enroll a new user with storage allocation"""
        email = request.email
        full_name = request.full_name
        
        # Check if email is verified
        if not user_manager.is_email_verified(email):
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Email not verified. Please complete login and OTP verification first."
            )
        
        # Check if storage is available
        if not user_manager.can_allocate_new_user():
            context.abort(
                grpc.StatusCode.RESOURCE_EXHAUSTED,
                "System storage exhausted. Cannot allocate storage for new users."
            )
        
        # Enroll user
        success, message, token = user_manager.enroll_user(email, full_name)
        
        if not success:
            if "exhausted" in message.lower():
                context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, message)
            else:
                context.abort(grpc.StatusCode.FAILED_PRECONDITION, message)
        
        return calculator_pb2.EnrollResponse(
            success=True,
            message=message,
            session_token=token
        )


class CalculatorServicer(calculator_pb2_grpc.CalculatorServicer):
    """Implementation of Calculator service"""
    
    def _validate_token(self, token, context):
        """Validate session token and return user"""
        if not token:
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Session token is required."
            )
        
        user = user_manager.get_user_by_token(token)
        if not user:
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Invalid session token."
            )
        
        return user
    
    def Add(self, request, context):
        """Add two numbers"""
        user = self._validate_token(request.session_token, context)
        
        result = request.a + request.b
        return calculator_pb2.AddResponse(
            success=True,
            message=f"Addition performed successfully for user {user['name']}",
            result=result
        )
    
    def Sub(self, request, context):
        """Subtract two numbers"""
        user = self._validate_token(request.session_token, context)
        
        result = request.a - request.b
        return calculator_pb2.SubResponse(
            success=True,
            message=f"Subtraction performed successfully for user {user['name']}",
            result=result
        )
    
    def Mul(self, request, context):
        """Multiply two numbers"""
        user = self._validate_token(request.session_token, context)
        
        result = request.a * request.b
        return calculator_pb2.MulResponse(
            success=True,
            message=f"Multiplication performed successfully for user {user['name']}",
            result=result
        )
    
    def Div(self, request, context):
        """Divide two numbers"""
        user = self._validate_token(request.session_token, context)
        
        if request.b == 0:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Division by zero is not allowed."
            )
        
        result = request.a // request.b
        return calculator_pb2.DivResponse(
            success=True,
            message=f"Division performed successfully for user {user['name']}",
            result=result
        )
    
    def Mod(self, request, context):
        """Modulo operation"""
        user = self._validate_token(request.session_token, context)
        
        if request.b == 0:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Modulo by zero is not allowed."
            )
        
        result = request.a % request.b
        return calculator_pb2.ModResponse(
            success=True,
            message=f"Modulo performed successfully for user {user['name']}",
            result=result
        )


def serve():
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add servicers
    calculator_pb2_grpc.add_AuthServiceServicer_to_server(
        AuthServiceServicer(), server
    )
    calculator_pb2_grpc.add_CalculatorServicer_to_server(
        CalculatorServicer(), server
    )
    
    # Bind to port
    server.add_insecure_port('[::]:50051')
    
    print("CloudGrpc Server starting on port 50051...")
    print(f"Global storage: 6 GB | Per-user allocation: 1 GB | Max users: 6")
    
    server.start()
    print("Server started successfully!")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()