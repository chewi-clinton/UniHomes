#!/usr/bin/env python3
"""
CLI - Command Line Interface for Cloud Storage
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
    # Authentication Commands
    # ============================================================================
    
    def cmd_send_otp(self, email):
        """Send OTP to email"""
        self.print_header("Send OTP")
        
        if not email:
            self.print_error("Email required")
            print("Usage: cli.py send-otp <email>")
            return False
        
        success, message = self.client.send_otp(email)
        
        if success:
            self.print_success(message)
        else:
            self.print_error(message)
        
        return success
    
    def cmd_verify_otp(self, email, otp):
        """Verify OTP"""
        self.print_header("Verify OTP")
        
        if not email or not otp:
            self.print_error("Email and OTP required")
            print("Usage: cli.py verify-otp <email> <otp>")
            return False
        
        success, message = self.client.verify_otp(email, otp)
        
        if success:
            self.print_success(message)
        else:
            self.print_error(message)
        
        return success
    
    def cmd_enroll(self, email, full_name):
        """Enroll new user"""
        self.print_header("Enroll New User")
        
        if not email or not full_name:
            self.print_error("Email and full name required")
            print("Usage: cli.py enroll <email> <full_name>")
            return False
        
        success, message = self.client.enroll(email, full_name)
        
        if success:
            self.print_success(message)
            self.print_info(f"Logged in as: {self.client.email}")
            self.print_info(f"User ID: {self.client.user_id}")
        else:
            self.print_error(message)
        
        return success
    
    def cmd_login(self, email):
        """Login existing user"""
        self.print_header("Login")
        
        if not email:
            self.print_error("Email required")
            print("Usage: cli.py login <email>")
            return False
        
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
    # File Commands
    # ============================================================================
    
    def cmd_upload(self, file_path):
        """Upload a file"""
        self.print_header("Upload File")
        
        if not self.client.is_logged_in():
            self.print_error("Not logged in. Please login first.")
            return False
        
        if not file_path:
            self.print_error("File path required")
            print("Usage: cli.py upload <file_path>")
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
            print("Usage: cli.py download <file_id> [output_path]")
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
            print(f"{'Filename':<30} {'Size':<12} {'Type':<20} {'Created':<20}")
            print("-" * 70)
            for file in files:
                size = self.format_bytes(file['file_size'])
                created = file['created_at'][:19].replace('T', ' ')
                shared = " 🔗" if file['is_shared'] else ""
                print(f"{file['filename']:<30} {size:<12} {file['mime_type']:<20} {created:<20}{shared}")
                print(f"  ID: {file['file_id']}")
        
        if not folders and not files:
            self.print_info("No files or folders found")
        
        return True
    
    def cmd_delete(self, file_id, permanent=False):
        """Delete a file"""
        self.print_header("Delete File")
        
        if not self.client.is_logged_in():
            self.print_error("Not logged in. Please login first.")
            return False
        
        if not file_id:
            self.print_error("File ID required")
            print("Usage: cli.py delete <file_id> [--permanent]")
            return False
        
        action = "permanently deleting" if permanent else "moving to trash"
        self.print_info(f"Action: {action} file {file_id}")
        
        success, message = self.client.delete_file(file_id, permanent)
        
        if success:
            self.print_success(message)
        else:
            self.print_error(message)
        
        return success
    
    def cmd_info(self, file_id):
        """Get file information"""
        self.print_header("File Information")
        
        if not self.client.is_logged_in():
            self.print_error("Not logged in. Please login first.")
            return False
        
        if not file_id:
            self.print_error("File ID required")
            print("Usage: cli.py info <file_id>")
            return False
        
        success, message, file_info = self.client.get_file_metadata(file_id)
        
        if not success:
            self.print_error(message)
            return False
        
        print(f"\nFilename:      {file_info['filename']}")
        print(f"File ID:       {file_info['file_id']}")
        print(f"Size:          {self.format_bytes(file_info['file_size'])}")
        print(f"MIME Type:     {file_info['mime_type']}")
        print(f"Chunks:        {file_info['chunk_count']}")
        print(f"Created:       {file_info['created_at'][:19].replace('T', ' ')}")
        print(f"Modified:      {file_info['modified_at'][:19].replace('T', ' ')}")
        print(f"Shared:        {'Yes' if file_info['is_shared'] else 'No'}")
        
        return True
    
    def cmd_mkdir(self, folder_name):
        """Create a folder"""
        self.print_header("Create Folder")
        
        if not self.client.is_logged_in():
            self.print_error("Not logged in. Please login first.")
            return False
        
        if not folder_name:
            self.print_error("Folder name required")
            print("Usage: cli.py mkdir <folder_name>")
            return False
        
        success, message, folder_id = self.client.create_folder(folder_name, self.current_folder_id)
        
        if success:
            self.print_success(message)
            self.print_info(f"Folder ID: {folder_id}")
        else:
            self.print_error(message)
        
        return success
    
    def cmd_share(self, file_id, share_with_email, permission='read'):
        """Share a file"""
        self.print_header("Share File")
        
        if not self.client.is_logged_in():
            self.print_error("Not logged in. Please login first.")
            return False
        
        if not file_id or not share_with_email:
            self.print_error("File ID and email required")
            print("Usage: cli.py share <file_id> <email> [permission]")
            return False
        
        success, message, share_token = self.client.share_file(file_id, share_with_email, permission)
        
        if success:
            self.print_success(message)
            self.print_info(f"Share token: {share_token}")
        else:
            self.print_error(message)
        
        return success
    
    def cmd_shared(self):
        """List files shared with current user"""
        self.print_header("Shared Files")
        
        if not self.client.is_logged_in():
            self.print_error("Not logged in. Please login first.")
            return False
        
        success, message, shared_files = self.client.get_shared_files()
        
        if not success:
            self.print_error(message)
            return False
        
        if not shared_files:
            self.print_info("No files shared with you")
            return True
        
        print(f"\n{'Filename':<30} {'Shared By':<30} {'Permission':<12} {'Date':<20}")
        print("-" * 70)
        
        for file in shared_files:
            shared_at = file['shared_at'][:19].replace('T', ' ')
            print(f"{file['filename']:<30} {file['shared_by_email']:<30} {file['permission']:<12} {shared_at:<20}")
            print(f"  ID: {file['file_id']}")
        
        return True
    
    # ============================================================================
    # Storage Commands
    # ============================================================================
    
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
                
                elif cmd == 'send-otp':
                    self.cmd_send_otp(args[0] if args else None)
                
                elif cmd == 'verify-otp':
                    self.cmd_verify_otp(args[0] if args else None, args[1] if len(args) > 1 else None)
                
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
                
                elif cmd == 'info':
                    self.cmd_info(args[0] if args else None)
                
                elif cmd == 'mkdir':
                    self.cmd_mkdir(' '.join(args) if args else None)
                
                elif cmd == 'share':
                    file_id = args[0] if args else None
                    email = args[1] if len(args) > 1 else None
                    permission = args[2] if len(args) > 2 else 'read'
                    self.cmd_share(file_id, email, permission)
                
                elif cmd == 'shared':
                    self.cmd_shared()
                
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
        
        print("\n📧 AUTHENTICATION:")
        print("  send-otp <email>              Send OTP to email")
        print("  verify-otp <email> <otp>      Verify OTP code")
        print("  enroll <email> <name>         Enroll new user")
        print("  login <email>                 Login existing user")
        print("  logout                        Logout current user")
        
        print("\n📁 FILE OPERATIONS:")
        print("  upload <file_path>            Upload a file")
        print("  download <file_id> [output]   Download a file")
        print("  list (or ls)                  List files")
        print("  delete <file_id> [--permanent] Delete a file")
        print("  info <file_id>                Get file information")
        print("  mkdir <folder_name>           Create a folder")
        
        print("\n🔗 SHARING:")
        print("  share <file_id> <email> [perm] Share a file (perm: read/write)")
        print("  shared                         List files shared with you")
        
        print("\n💾 STORAGE:")
        print("  storage                        Show storage information")
        
        print("\n🔧 UTILITY:")
        print("  help                           Show this help message")
        print("  clear                          Clear screen")
        print("  exit (or quit)                 Exit the CLI")
        print("=" * 70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cloud Storage CLI')
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('--permanent', action='store_true', help='Permanent delete flag')
    
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
        if cmd == 'send-otp':
            success = cli.cmd_send_otp(cmd_args[0] if cmd_args else None)
        
        elif cmd == 'verify-otp':
            success = cli.cmd_verify_otp(
                cmd_args[0] if cmd_args else None,
                cmd_args[1] if len(cmd_args) > 1 else None
            )
        
        elif cmd == 'enroll':
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
            success = cli.cmd_delete(cmd_args[0] if cmd_args else None, args.permanent)
        
        elif cmd == 'info':
            success = cli.cmd_info(cmd_args[0] if cmd_args else None)
        
        elif cmd == 'mkdir':
            success = cli.cmd_mkdir(' '.join(cmd_args) if cmd_args else None)
        
        elif cmd == 'share':
            file_id = cmd_args[0] if cmd_args else None
            email = cmd_args[1] if len(cmd_args) > 1 else None
            permission = cmd_args[2] if len(cmd_args) > 2 else 'read'
            success = cli.cmd_share(file_id, email, permission)
        
        elif cmd == 'shared':
            success = cli.cmd_shared()
        
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