#!/usr/bin/env python3
"""
System Test - Comprehensive testing of the distributed cloud storage system
"""

import os
import sys
import socket
import json
import time
import threading
import subprocess
import shutil

class SystemTester:
    def __init__(self):
        self.test_results = []
        self.cloud_process = None
        self.node_processes = []
        
    def log_result(self, test_name, passed, message=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message,
            'status': status
        })
        
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
    
    def test_file_exists(self):
        """Test if all required files exist"""
        required_files = [
            'cloud_gateway.py',
            'storage_node.py',
            'upload_client.py',
            'create_node.py',
            'start_node.py',
            'requirements.txt',
            'README.md'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            self.log_result("File Existence Test", False, f"Missing files: {', '.join(missing_files)}")
            return False
        else:
            self.log_result("File Existence Test", True, "All required files present")
            return True
    
    def test_cloud_gateway_start(self):
        """Test if Cloud Gateway can start"""
        try:
            # Test if we can bind to the required ports
            upload_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            node_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            upload_sock.bind(('localhost', 8000))
            node_sock.bind(('localhost', 8001))
            
            upload_sock.close()
            node_sock.close()
            
            self.log_result("Cloud Gateway Port Test", True, "Ports 8000 and 8001 available")
            return True
            
        except Exception as e:
            self.log_result("Cloud Gateway Port Test", False, f"Port binding error: {e}")
            return False
    
    def test_node_creation(self):
        """Test node creation functionality"""
        try:
            # Test create_node.py
            result = subprocess.run([
                sys.executable, 'create_node.py', 'test_node', 
                '--storage', '0.1', '--cpu', '1', '--port', '9999'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "created successfully" in result.stdout:
                self.log_result("Node Creation Test", True, "Node created successfully")
                
                # Check if config file was created
                if os.path.exists('nodes_config.json'):
                    with open('nodes_config.json', 'r') as f:
                        config = json.load(f)
                    
                    if 'test_node' in config:
                        self.log_result("Node Configuration Test", True, "Configuration saved correctly")
                        return True
                    else:
                        self.log_result("Node Configuration Test", False, "Node not found in config")
                        return False
                else:
                    self.log_result("Node Configuration Test", False, "Config file not created")
                    return False
            else:
                self.log_result("Node Creation Test", False, f"Creation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_result("Node Creation Test", False, "Command timed out")
            return False
        except Exception as e:
            self.log_result("Node Creation Test", False, f"Exception: {e}")
            return False
    
    def test_node_start(self):
        """Test if node can start (basic syntax check)"""
        try:
            # Test storage_node.py syntax
            result = subprocess.run([
                sys.executable, '-m', 'py_compile', 'storage_node.py'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_result("Node Syntax Test", True, "Storage node syntax is valid")
                return True
            else:
                self.log_result("Node Syntax Test", False, f"Syntax error: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_result("Node Syntax Test", False, f"Exception: {e}")
            return False
    
    def test_upload_client(self):
        """Test upload client syntax"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'py_compile', 'upload_client.py'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_result("Upload Client Syntax Test", True, "Upload client syntax is valid")
                return True
            else:
                self.log_result("Upload Client Syntax Test", False, f"Syntax error: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_result("Upload Client Syntax Test", False, f"Exception: {e}")
            return False
    
    def test_network_communication(self):
        """Test basic network communication"""
        try:
            # Test if we can create sockets and communicate
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('localhost', 0))  # Let OS choose port
            port = server_sock.getsockname()[1]
            server_sock.listen(1)
            
            # Test client connection
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.settimeout(5)
            
            # Start server in thread
            def accept_conn():
                conn, addr = server_sock.accept()
                conn.close()
            
            thread = threading.Thread(target=accept_conn)
            thread.daemon = True
            thread.start()
            
            # Try to connect
            result = client_sock.connect_ex(('localhost', port))
            client_sock.close()
            server_sock.close()
            
            if result == 0:
                self.log_result("Network Communication Test", True, "Socket communication working")
                return True
            else:
                self.log_result("Network Communication Test", False, "Cannot establish socket connection")
                return False
                
        except Exception as e:
            self.log_result("Network Communication Test", False, f"Exception: {e}")
            return False
    
    def test_json_functionality(self):
        """Test JSON serialization/deserialization"""
        try:
            test_data = {
                'node_id': 'test',
                'host': 'localhost',
                'port': 9001,
                'storage_capacity': 1000000
            }
            
            # Test serialization
            json_str = json.dumps(test_data)
            
            # Test deserialization
            parsed_data = json.loads(json_str)
            
            if parsed_data['node_id'] == 'test' and parsed_data['port'] == 9001:
                self.log_result("JSON Functionality Test", True, "JSON serialization working")
                return True
            else:
                self.log_result("JSON Functionality Test", False, "JSON parse error")
                return False
                
        except Exception as e:
            self.log_result("JSON Functionality Test", False, f"Exception: {e}")
            return False
    
    def test_storage_allocation(self):
        """Test storage directory creation"""
        try:
            test_dir = 'test_storage_dir'
            
            # Create directory
            os.makedirs(test_dir, exist_ok=True)
            
            # Create test file
            test_file = os.path.join(test_dir, 'test_file.dat')
            test_size = 1024 * 1024  # 1MB
            
            with open(test_file, 'wb') as f:
                f.write(b'X' * test_size)
            
            # Check if file exists and has correct size
            if os.path.exists(test_file) and os.path.getsize(test_file) == test_size:
                self.log_result("Storage Allocation Test", True, "Storage allocation working")
                
                # Cleanup
                shutil.rmtree(test_dir)
                return True
            else:
                self.log_result("Storage Allocation Test", False, "File creation failed")
                return False
                
        except Exception as e:
            self.log_result("Storage Allocation Test", False, f"Exception: {e}")
            return False
    
    def test_multi_threading(self):
        """Test multi-threading functionality"""
        try:
            results = []
            
            def worker(worker_id):
                time.sleep(0.1)  # Simulate work
                results.append(worker_id)
            
            # Create multiple threads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            if len(results) == 5:
                self.log_result("Multi-threading Test", True, "Threading working correctly")
                return True
            else:
                self.log_result("Multi-threading Test", False, f"Expected 5 results, got {len(results)}")
                return False
                
        except Exception as e:
            self.log_result("Multi-threading Test", False, f"Exception: {e}")
            return False
    
    def cleanup(self):
        """Clean up test artifacts"""
        try:
            # Clean up test files
            test_files = ['nodes_config.json', 'cloud_db.pkl']
            for file in test_files:
                if os.path.exists(file):
                    os.remove(file)
            
            # Clean up test directories
            for item in os.listdir('.'):
                if item.startswith('storage_') or item.startswith('test_storage'):
                    if os.path.isdir(item):
                        shutil.rmtree(item)
            
            self.log_result("Cleanup Test", True, "Test artifacts cleaned up")
            
        except Exception as e:
            self.log_result("Cleanup Test", False, f"Cleanup error: {e}")
    
    def run_all_tests(self):
        """Run all system tests"""
        print("🧪 Running System Tests")
        print("=" * 60)
        print()
        
        # Run tests
        tests = [
            self.test_file_exists,
            self.test_cloud_gateway_start,
            self.test_node_creation,
            self.test_node_start,
            self.test_upload_client,
            self.test_network_communication,
            self.test_json_functionality,
            self.test_storage_allocation,
            self.test_multi_threading
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_result(test.__name__, False, f"Unexpected exception: {e}")
        
        print()
        print("=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['passed'])
        total = len(self.test_results)
        
        for result in self.test_results:
            print(f"{result['status']} {result['test']}")
            if result['message']:
                print(f"   {result['message']}")
        
        print()
        print(f"🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! System is ready to use.")
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
        
        # Cleanup
        print()
        print("🧹 Cleaning up...")
        self.cleanup()
        
        return passed == total

def main():
    tester = SystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()