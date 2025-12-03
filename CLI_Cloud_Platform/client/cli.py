#!/usr/bin/env python3
"""
CLI - Command Line Interface for Cloud Storage (SIMPLIFIED)
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from client.cloud_client import CloudClient
from dotenv import load_dotenv

load_dotenv()


class CloudCLI:
    def __init__(self):
        server_address = os.getenv('GRPC_SERVER_HOST', 'localhost') + ':' + os.getenv('GRPC_SERVER_PORT', '50051')
        self.client = CloudClient(server_address)
        self.current_folder_id = None
        self.current_folder_path = "/"
    
    def format_bytes(self, bytes_value):
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def print_success(self, message):
        """Print success message"""
        print(f"✓ {message}")
    
    def print_error(self, message):
        """Print error message"""
        print(f"✗ {message}")
    
    def print_info(self, message):
        """Print info message"""
        print(f"ℹ {message}")
    
    # ============================================================================
    # SIMPLIFIED Authentication Commands
    # ============================================================================
    
    def cmd_enroll(self, email, full_name):
        """SIMPLIFIED: Enroll new user with automatic OTP"""
        self.print_header("Enroll New User")
        
        if not email or not full_name:
            self.print_error("Email and full name required")
            print("Usage: enroll <email> <full_name>")
            return False
        
        # Step 1: Send OTP automatically
        print(f"📧 Sending OTP to {email}...")
        success, message = self.client.send_otp(email)
        
        if not success:
            self.print_error(f"Failed to send OTP: {message}")
            return False
        
        self.print_success("OTP sent to your email!")
        
        # Step 2: Ask user to enter OTP
        print("\n" + "-" * 70)
        otp = input("📬 Enter the 6-digit OTP code from your email: ").strip()
        
        if not otp:
            self.print_error("OTP is required")
            return False
        
        # Step 3: Verify OTP
        print("🔐 Verifying OTP...")
        success, message = self.client.verify_otp(email, otp)
        
        if not success:
            self.print_error(f"OTP verification failed: {message}")
            return False
        
        self.print_success("OTP verified!")
        
        # Step 4: Enroll user
        print("📝 Creating your account...")
        success, message = self.client.enroll(email, full_name)
        
        if success:
            self.print_success(message)
            self.print_info(f"Logged in as: {self.client.email}")
            self.print_info(f"User ID: {self.client.user_id}")
            self.print_info("You have 1 GB storage allocated")
        else:
            self.print_error(message)
        
        return success
    
    def cmd_login(self, email):
        """SIMPLIFIED: Login existing user with automatic OTP"""
        self.print_header("Login")
        
        if not email:
            self.print_error("Email required")
            print("Usage: login <email>")
            return False
        
        # Step 1: Send OTP automatically
        print(f"📧 Sending OTP to {email}...")
        success, message = self.client.send_otp(email)
        
        if not success:
            self.print_error(f"Failed to send OTP: {message}")
            return False
        
        self.print_success("OTP sent to your email!")
        
        # Step 2: Ask user to enter OTP
        print("\n" + "-" * 70)
        otp = input("📬 Enter the 6-digit OTP code from your email: ").strip()
        
        if not otp:
            self.print_error("OTP is required")
            return False
        
        # Step 3: Verify OTP
        print("🔐 Verifying OTP...")
        success, message = self.client.verify_otp(email, otp)
        
        if not success:
            self.print_error(f"OTP verification failed: {message}")
            return False
        
        self.print_success("OTP verified!")
        
        # Step 4: Login
        print("🔓 Logging you in...")
        success, message = self.client.login(email)
        
        if success:
            self.print_success(message)
            self.print_info(f"Logged in as: {self.client.email}")
            self.print_info(f"User ID: {self.client.user_id}")
        else:
            self.print_error(message)
        
        return success
    
    def cmd_logout(self):
        """Logout current user"""
        self.print_header("Logout")
        
        if not self.client.is_logged_in():
            self.print_error("Not logged in")
            return False
        
        success, message = self.client.logout()
        
        if success:
            self.print_success(message)
        else:
            self.print_error(message)
        
        return success
    
    # ============================================================================
    # File Commands (Same as before)
    # ============================================================================
    
    def cmd_upload(self, file_path):
        """Upload a file"""
        self.print_header("Upload File")
        
        if not self.client.is_logged_in():
            self.print_error("Not logged in. Please login first.")
            return False
        
        if not file_path:
            self.print_error("File path required")
            print("Usage: upload <file_path>")
            return False
        
        if not os.path.exists(file_path):
            self.print_error(f"File not found: {file_path}")
            return False
        
        file_size = os.path.getsize(file_path)
        self.print_info(f"Uploading: {os.path.basename(file_path)} ({self.format_bytes(file_size)})")
        
        success, message, file_id = self.client.upload_file(file_path, self.current_folder_id)
        
        if success:
            self.print_success(message)
            self.print_info(f"File ID: {file_id}")
        else:
            self.print_error(message)
        
        return success
    
    def cmd_download(self, file_id, output_path=None):
        """Download a file"""
        self.print_header("Download File")
        
        if not self.client.is_logged_in():
            self.print_error("Not logged in. Please login first.")
            return False
        
        if not file_id:
            self.print_error("File ID required")
            print("Usage: download <file_id> [output_path]")
            return False
        
        self.print_info(f"Downloading file: {file_id}")
        
        success, message = self.client.download_file(file_id, output_path)
        
        if success:
            self.print_success(message)
        else:
            self.print_error(message)
        
        return success
    
    def cmd_list(self):
        """List files in current folder"""
        self.print_header(f"Files in: {self.current_folder_path}")
        
        if not self.client.is_logged_in():
            self.print_error("Not logged in. Please login first.")
            return False
        
        success, message, files, folders = self.client.list_files(self.current_folder_id)
        
        if not success:
            self.print_error(message)
            return False
        
        # Print folders
        if folders:
            print("\n📁 FOLDERS:")
            print(f"{'Name':<30} {'Files':<10} {'Created':<20}")
            print("-" * 70)
            for folder in folders:
                created = folder['created_at'][:19].replace('T', ' ')
                print(f"{folder['folder_name']:<30} {folder['file_count']:<10} {created:<20}")
        
        # Print files
        if files:
            print("\n📄 FILES:")
            print(f"{'Filename':<30} {'Size':<12} {'Type':<20}")
            print("-" * 70)
            for file in files:
                size = self.format_bytes(file['file_size'])
                shared = " 🔗" if file['is_shared'] else ""
                print(f"{file['filename']:<30} {size:<12} {file['mime_type']:<20}{shared}")
                print(f"  ID: {file['file_id']}")
        
        if not folders and not files:
            self.print_info("No files or folders found")
        
        return True
    
    def cmd_delete(self, file_id, permanent=True):
        """Delete a file"""
        self.print_header("Delete File")
        
        if not self.client.is_logged_in():
            self.print_error("Not logged in. Please login first.")
            return False
        
        if not file_id:
            self.print_error("File ID required")
            print("Usage: delete <file_id> [--permanent]")
            return False
        
        success, message = self.client.delete_file(file_id, permanent)
        
        if success:
            self.print_success(message)
        else:
            self.print_error(message)
        
        return success
    
    def cmd_storage(self):
        """Show storage information"""
        self.print_header("Storage Information")
        
        if not self.client.is_logged_in():
            self.print_error("Not logged in. Please login first.")
            return False
        
        success, message, storage_info = self.client.get_storage_info()
        
        if not success:
            self.print_error(message)
            return False
        
        allocated = self.format_bytes(storage_info['allocated_bytes'])
        used = self.format_bytes(storage_info['used_bytes'])
        available = self.format_bytes(storage_info['available_bytes'])
        percentage = storage_info['usage_percentage']
        
        print(f"\nAllocated:     {allocated}")
        print(f"Used:          {used}")
        print(f"Available:     {available}")
        print(f"Usage:         {percentage:.2f}%")
        
        # Progress bar
        bar_length = 50
        filled = int(bar_length * percentage / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\n[{bar}] {percentage:.1f}%")
        
        return True
    
    # ============================================================================
    # Interactive Shell
    # ============================================================================
    
    def interactive_shell(self):
        """Run interactive shell"""
        self.print_header("Cloud Storage CLI - Interactive Mode")
        print("Type 'help' for available commands or 'exit' to quit")
        
        while True:
            try:
                prompt = f"\n[{self.client.email or 'not logged in'}] {self.current_folder_path}> "
                command = input(prompt).strip()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                if cmd == 'exit' or cmd == 'quit':
                    print("\nGoodbye!")
                    break
                
                elif cmd == 'help':
                    self.show_help()
                
                elif cmd == 'enroll':
                    email = args[0] if args else None
                    name = ' '.join(args[1:]) if len(args) > 1 else None
                    self.cmd_enroll(email, name)
                
                elif cmd == 'login':
                    self.cmd_login(args[0] if args else None)
                
                elif cmd == 'logout':
                    self.cmd_logout()
                
                elif cmd == 'upload':
                    self.cmd_upload(args[0] if args else None)
                
                elif cmd == 'download':
                    file_id = args[0] if args else None
                    output = args[1] if len(args) > 1 else None
                    self.cmd_download(file_id, output)
                
                elif cmd == 'list' or cmd == 'ls':
                    self.cmd_list()
                
                elif cmd == 'delete' or cmd == 'rm':
                    file_id = args[0] if args else None
                    permanent = '--permanent' in args
                    self.cmd_delete(file_id, permanent)
                
                elif cmd == 'storage':
                    self.cmd_storage()
                
                elif cmd == 'clear':
                    os.system('clear' if os.name != 'nt' else 'cls')
                
                else:
                    self.print_error(f"Unknown command: {cmd}")
                    print("Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\n\nUse 'exit' to quit")
            except EOFError:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                self.print_error(f"Error: {str(e)}")
    
    def show_help(self):
        """Show help message"""
        print("\n" + "=" * 70)
        print("AVAILABLE COMMANDS")
        print("=" * 70)
        
        print("\n📧 AUTHENTICATION (SIMPLIFIED):")
        print("  enroll <email> <name>         Register new account (auto-sends OTP)")
        print("  login <email>                 Login to existing account (auto-sends OTP)")
        print("  logout                        Logout current user")
        
        print("\n📁 FILE OPERATIONS:")
        print("  upload <file_path>            Upload a file")
        print("  download <file_id> [output]   Download a file")
        print("  list (or ls)                  List files")
        print("  delete <file_id>              Delete a file")
        print("  storage                       Show storage information")
        
        print("\n🔧 UTILITY:")
        print("  help                          Show this help message")
        print("  clear                         Clear screen")
        print("  exit (or quit)                Exit the CLI")
        print("=" * 70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cloud Storage CLI')
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('args', nargs='*', help='Command arguments')
    
    args = parser.parse_args()
    
    cli = CloudCLI()
    
    # If no command, run interactive shell
    if not args.command:
        cli.interactive_shell()
        return 0
    
    # Execute single command
    cmd = args.command.lower()
    cmd_args = args.args
    
    try:
        if cmd == 'enroll':
            email = cmd_args[0] if cmd_args else None
            name = ' '.join(cmd_args[1:]) if len(cmd_args) > 1 else None
            success = cli.cmd_enroll(email, name)
        
        elif cmd == 'login':
            success = cli.cmd_login(cmd_args[0] if cmd_args else None)
        
        elif cmd == 'logout':
            success = cli.cmd_logout()
        
        elif cmd == 'upload':
            success = cli.cmd_upload(cmd_args[0] if cmd_args else None)
        
        elif cmd == 'download':
            file_id = cmd_args[0] if cmd_args else None
            output = cmd_args[1] if len(cmd_args) > 1 else None
            success = cli.cmd_download(file_id, output)
        
        elif cmd == 'list' or cmd == 'ls':
            success = cli.cmd_list()
        
        elif cmd == 'delete' or cmd == 'rm':
            success = cli.cmd_delete(cmd_args[0] if cmd_args else None)
        
        elif cmd == 'storage':
            success = cli.cmd_storage()
        
        elif cmd == 'help':
            cli.show_help()
            success = True
        
        else:
            cli.print_error(f"Unknown command: {cmd}")
            print("Use 'help' to see available commands")
            success = False
        
        return 0 if success else 1
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        return 130
    except Exception as e:
        cli.print_error(f"Error: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())