import grpc
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from generated import calculator_pb2
from generated import calculator_pb2_grpc


class CloudGrpcClient:
    def __init__(self, host='localhost:50051'):
        self.channel = grpc.insecure_channel(host)
        self.auth_stub = calculator_pb2_grpc.AuthServiceStub(self.channel)
        self.calc_stub = calculator_pb2_grpc.CalculatorStub(self.channel)
        self.session_token = None
        self.current_user = None
    
    def send_otp(self, email):
        """Send OTP to email"""
        try:
            response = self.auth_stub.SendOtp(
                calculator_pb2.SendOtpRequest(email=email)
            )
            print(f"✓ {response.message}")
            return response.success
        except grpc.RpcError as e:
            print(f"✗ Failed to send OTP: {e.details()}")
            return False
    
    def verify_otp(self, email, otp):
        """Verify OTP"""
        try:
            response = self.auth_stub.VerifyOtp(
                calculator_pb2.VerifyOtpRequest(email=email, otp=otp)
            )
            print(f"✓ {response.message}")
            return response.success
        except grpc.RpcError as e:
            print(f"✗ OTP verification failed: {e.details()}")
            return False
    
    def login(self, email):
        """Login existing user"""
        try:
            response = self.auth_stub.Login(
                calculator_pb2.LoginRequest(email=email)
            )
            self.session_token = response.session_token
            print(f"✓ {response.message}")
            return True
        except grpc.RpcError as e:
            print(f"✗ Login failed: [{e.code().name}] {e.details()}")
            return False
    
    def enroll(self, email, full_name):
        """Enroll new user"""
        try:
            response = self.auth_stub.Enroll(
                calculator_pb2.EnrollRequest(email=email, full_name=full_name)
            )
            self.session_token = response.session_token
            self.current_user = full_name
            print(f"✓ {response.message}")
            print(f"✓ Session token received!")
            return True
        except grpc.RpcError as e:
            print(f"✗ Enrollment failed: [{e.code().name}] {e.details()}")
            return False
    
    def get_storage_info(self):
        """Get user's storage information"""
        try:
            response = self.auth_stub.GetStorageInfo(
                calculator_pb2.StorageInfoRequest(session_token=self.session_token)
            )
            return {
                'success': response.success,
                'allocated': response.allocated_bytes,
                'used': response.used_bytes,
                'available': response.available_bytes,
                'usage_percentage': response.usage_percentage
            }
        except grpc.RpcError as e:
            print(f"✗ Failed to get storage info: [{e.code().name}] {e.details()}")
            return None
    
    def add(self, a, b):
        """Add two numbers"""
        try:
            response = self.calc_stub.Add(
                calculator_pb2.AddRequest(session_token=self.session_token, a=a, b=b)
            )
            return response.result
        except grpc.RpcError as e:
            print(f"✗ Add failed: [{e.code().name}] {e.details()}")
            return None
    
    def sub(self, a, b):
        """Subtract two numbers"""
        try:
            response = self.calc_stub.Sub(
                calculator_pb2.SubRequest(session_token=self.session_token, a=a, b=b)
            )
            return response.result
        except grpc.RpcError as e:
            print(f"✗ Sub failed: [{e.code().name}] {e.details()}")
            return None
    
    def mul(self, a, b):
        """Multiply two numbers"""
        try:
            response = self.calc_stub.Mul(
                calculator_pb2.MulRequest(session_token=self.session_token, a=a, b=b)
            )
            return response.result
        except grpc.RpcError as e:
            print(f"✗ Mul failed: [{e.code().name}] {e.details()}")
            return None
    
    def div(self, a, b):
        """Divide two numbers"""
        try:
            response = self.calc_stub.Div(
                calculator_pb2.DivRequest(session_token=self.session_token, a=a, b=b)
            )
            return response.result
        except grpc.RpcError as e:
            print(f"✗ Div failed: [{e.code().name}] {e.details()}")
            return None
    
    def mod(self, a, b):
        """Modulo operation"""
        try:
            response = self.calc_stub.Mod(
                calculator_pb2.ModRequest(session_token=self.session_token, a=a, b=b)
            )
            return response.result
        except grpc.RpcError as e:
            print(f"✗ Mod failed: [{e.code().name}] {e.details()}")
            return None
    
    def close(self):
        """Close the channel"""
        self.channel.close()


def format_bytes(bytes_value):
    """Format bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"


def display_storage_info(client):
    """Display user's storage information"""
    storage_info = client.get_storage_info()
    
    if storage_info:
        print("\n" + "="*60)
        print("STORAGE INFORMATION")
        print("="*60)
        print(f"Allocated:  {format_bytes(storage_info['allocated'])}")
        print(f"Used:       {format_bytes(storage_info['used'])}")
        print(f"Available:  {format_bytes(storage_info['available'])}")
        print(f"Usage:      {storage_info['usage_percentage']:.2f}%")
        
        # Visual progress bar
        bar_length = 40
        filled_length = int(bar_length * storage_info['usage_percentage'] / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"[{bar}] {storage_info['usage_percentage']:.2f}%")
        print("="*60)


def calculator_menu(client):
    """Interactive calculator menu"""
    while True:
        print("\n" + "="*60)
        print("CALCULATOR OPERATIONS")
        print("="*60)
        print("1. Addition")
        print("2. Subtraction")
        print("3. Multiplication")
        print("4. Division")
        print("5. Modulo")
        print("6. Run Concurrent Operations Demo")
        print("7. View Storage Information")
        print("8. Logout")
        print("="*60)
        
        choice = input("Select operation (1-8): ").strip()
        
        if choice == '8':
            print("\n✓ Logged out successfully!")
            break
        
        if choice == '7':
            display_storage_info(client)
            continue
        
        if choice == '6':
            run_concurrent_demo(client)
            continue
        
        if choice not in ['1', '2', '3', '4', '5']:
            print("✗ Invalid choice! Please select 1-8.")
            continue
        
        try:
            a = int(input("Enter first number: ").strip())
            b = int(input("Enter second number: ").strip())
            
            result = None
            if choice == '1':
                result = client.add(a, b)
                op = "+"
            elif choice == '2':
                result = client.sub(a, b)
                op = "-"
            elif choice == '3':
                result = client.mul(a, b)
                op = "*"
            elif choice == '4':
                result = client.div(a, b)
                op = "//"
            elif choice == '5':
                result = client.mod(a, b)
                op = "%"
            
            if result is not None:
                print(f"\n✓ Result: {a} {op} {b} = {result}")
        
        except ValueError:
            print("✗ Invalid input! Please enter valid numbers.")
        except Exception as e:
            print(f"✗ Error: {e}")


def run_concurrent_demo(client):
    """Run concurrent calculator operations"""
    print("\n" + "="*60)
    print("CONCURRENT OPERATIONS DEMO")
    print("="*60)
    print("Running 4 operations concurrently...")
    
    operations = [
        ('add', 633, 27),
        ('sub', 633, 27),
        ('div', 633, 27),
        ('mod', 633, 27)
    ]
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for op, a, b in operations:
            if op == 'add':
                future = executor.submit(client.add, a, b)
            elif op == 'sub':
                future = executor.submit(client.sub, a, b)
            elif op == 'div':
                future = executor.submit(client.div, a, b)
            elif op == 'mod':
                future = executor.submit(client.mod, a, b)
            futures.append((op, a, b, future))
        
        # Display results
        for op, a, b, future in futures:
            result = future.result()
            if result is not None:
                op_symbol = {
                    'add': '+', 'sub': '-', 'div': '//', 'mod': '%'
                }[op]
                print(f"  ✓ {a} {op_symbol} {b} = {result}")
    
    print("\n✓ All concurrent operations completed!")


def main():
    """Main application loop"""
    print("="*60)
    print("CloudGrpc - Secure Calculator Service")
    print("="*60)
    
    client = CloudGrpcClient()
    
    while True:
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)
        print("1. Login (Existing User)")
        print("2. Enroll (New User)")
        print("3. Exit")
        print("="*60)
        
        choice = input("Select option (1-3): ").strip()
        
        if choice == '3':
            print("\n✓ Thank you for using CloudGrpc!")
            client.close()
            sys.exit(0)
        
        if choice == '1':
            # LOGIN FLOW (Existing User)
            print("\n" + "-"*60)
            print("LOGIN - Existing User")
            print("-"*60)
            
            email = input("Enter your email: ").strip()
            if not email or '@' not in email:
                print("✗ Invalid email address!")
                continue
            
            print(f"\n📧 Sending OTP to {email}...")
            if not client.send_otp(email):
                continue
            
            otp = input("\nEnter the OTP sent to your email: ").strip()
            if not client.verify_otp(email, otp):
                continue
            
            print(f"\n🔐 Logging in...")
            if not client.login(email):
                continue
            
            # Successfully logged in, go to calculator menu
            print(f"\n✓ Welcome back!")
            display_storage_info(client)
            calculator_menu(client)
        
        elif choice == '2':
            # ENROLLMENT FLOW (New User)
            print("\n" + "-"*60)
            print("ENROLLMENT - New User")
            print("-"*60)
            
            email = input("Enter your email: ").strip()
            if not email or '@' not in email:
                print("✗ Invalid email address!")
                continue
            
            full_name = input("Enter your full name: ").strip()
            if not full_name:
                print("✗ Name cannot be empty!")
                continue
            
            print(f"\n📧 Sending OTP to {email}...")
            if not client.send_otp(email):
                continue
            
            otp = input("\nEnter the OTP sent to your email: ").strip()
            if not client.verify_otp(email, otp):
                continue
            
            print(f"\n📝 Enrolling {full_name}...")
            if not client.enroll(email, full_name):
                continue
            
            # Successfully enrolled, go to calculator menu
            print(f"\n✓ Welcome, {full_name}!")
            display_storage_info(client)
            calculator_menu(client)
        
        else:
            print("✗ Invalid choice! Please select 1-3.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✓ Application terminated by user.")
        sys.exit(0)