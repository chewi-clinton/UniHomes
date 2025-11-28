# Cloud Storage Platform - Setup & Usage Guide

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Gmail account (for OTP)

## Installation

### 1. Install Dependencies

```bash
pip install grpcio grpcio-tools sqlalchemy psycopg2-binary python-dotenv
```

### 2. Setup PostgreSQL Database

```bash
# Login to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE cloud_storage;
CREATE USER cloud_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE cloud_storage TO cloud_user;
\q
```

### 3. Configure Environment Variables

Create a `.env` file in your project root:

```properties
# PostgreSQL Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cloud_storage
DB_USER=cloud_user
DB_PASSWORD=your_secure_password

# Gmail OTP Configuration
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password

# Server Configuration
GRPC_SERVER_HOST=localhost
GRPC_SERVER_PORT=50051

# Admin Configuration
ADMIN_KEY=change_this_to_a_secure_random_key

# User Storage Configuration
PER_USER_STORAGE_GB=1
```

### 4. Setup Gmail App Password

1. Go to Google Account settings
2. Enable 2-Factor Authentication
3. Go to Security → App passwords
4. Generate new app password for "Mail"
5. Copy the 16-character password to `GMAIL_APP_PASSWORD` in `.env`

### 5. Generate gRPC Code

```bash
python -m grpc_tools.protoc \
    -I. \
    --python_out=generated \
    --grpc_python_out=generated \
    cloud_storage.proto
```

## Project Structure

```
cloud-storage/
├── server/
│   └── cloud_server.py         # Main gRPC server
├── client/
│   ├── cloud_client.py         # Client library
│   └── cli.py                  # Command-line interface
├── admin/
│   └── admin_monitor.py        # Admin dashboard
├── node/
│   └── storage_node.py         # Storage node
├── auth/
│   └── gmail_otp.py            # OTP manager
├── user/
│   └── user_manager.py         # User management
├── file/
│   └── file_manager.py         # File operations
├── storage/
│   ├── node_manager.py         # Node management
│   └── chunk_distributor.py   # Chunk distribution
├── db/
│   ├── models.py               # Database models
│   └── database.py             # Database connection
├── generated/                  # Generated gRPC code
├── cloud_storage.proto         # Protocol buffer definition
└── .env                        # Environment variables
```

## Usage

### Starting the System

#### 1. Start the Cloud Server

```bash
python -m server.cloud_server
```

Output:

```
======================================================================
CLOUD STORAGE PLATFORM - SERVER (DYNAMIC STORAGE)
======================================================================
[DATABASE] Connecting to: postgresql://cloud_user:***@localhost:5432/cloud_storage
[DATABASE] Tables created successfully
[DATABASE] Database initialized
Current Global Storage: 0 GB (no nodes registered)
Storage will grow as nodes are added!
Server listening on port 50051
Admin Key: change_this_to_a_secure_random_key
======================================================================

[READY] Cloud server is ready to accept connections
```

#### 2. Start Storage Nodes

Open new terminals and start nodes:

```bash
# Terminal 2: Node 1
python -m node.storage_node node1 localhost 9001 2

# Terminal 3: Node 2
python -m node.storage_node node2 localhost 9002 3

# Terminal 4: Node 3
python -m node.storage_node node3 localhost 9003 5
```

Each node will output:

```
[NODE] Storage Node: node1
[NODE] Storage capacity: 2.00 GB
[NODE] Listening on localhost:9001
[NODE] Registered with gateway
[NODE] Status: ONLINE
```

### Using the CLI

#### Interactive Mode

```bash
python -m client.cli
```

This starts an interactive shell:

```
======================================================================
  Cloud Storage CLI - Interactive Mode
======================================================================
Type 'help' for available commands or 'exit' to quit

[not logged in] />
```

#### Command Mode

```bash
# Send OTP
python -m client.cli send-otp user@example.com

# Verify OTP
python -m client.cli verify-otp user@example.com 123456

# Enroll new user
python -m client.cli enroll user@example.com "John Doe"

# Login
python -m client.cli login user@example.com

# Upload file
python -m client.cli upload /path/to/file.pdf

# List files
python -m client.cli list

# Download file
python -m client.cli download <file_id> /path/to/output

# Delete file
python -m client.cli delete <file_id>
python -m client.cli delete <file_id> --permanent

# Check storage
python -m client.cli storage
```

### Complete User Workflow

#### 1. Registration & Login

```bash
# Interactive mode
python -m client.cli

# In the CLI:
> send-otp john@example.com
✓ OTP sent successfully. [TEST MODE: OTP is 123456]

> verify-otp john@example.com 123456
✓ OTP verified successfully.

> enroll john@example.com John Doe
✓ Successfully enrolled John Doe. Allocated 1 GB storage.
ℹ Logged in as: john@example.com
ℹ User ID: abc-123-def-456
```

#### 2. File Operations

```bash
# Upload a file
> upload /home/user/document.pdf
ℹ Uploading: document.pdf (2.34 MB)
✓ File uploaded successfully
ℹ File ID: file_xyz123

# List files
> list
======================================================================
  Files in: /
======================================================================

📄 FILES:
Filename                       Size         Type                 Created
----------------------------------------------------------------------
document.pdf                   2.34 MB      application/pdf      2024-01-15 10:30:45
  ID: file_xyz123

# Get file info
> info file_xyz123
======================================================================
  File Information
======================================================================

Filename:      document.pdf
File ID:       file_xyz123
Size:          2.34 MB
MIME Type:     application/pdf
Chunks:        4
Created:       2024-01-15 10:30:45
Modified:      2024-01-15 10:30:45
Shared:        No

# Download file
> download file_xyz123 /home/user/downloads/
✓ File downloaded to /home/user/downloads/document.pdf
```

#### 3. Folder Management

```bash
# Create folder
> mkdir Work Documents
✓ Folder created
ℹ Folder ID: folder_abc123

# Upload to folder would require navigating (future enhancement)
```

#### 4. File Sharing

```bash
# Share file with another user
> share file_xyz123 jane@example.com read
✓ File shared successfully
ℹ Share token: abc123def456

# View files shared with you
> shared
======================================================================
  Shared Files
======================================================================

Filename                       Shared By                      Permission   Date
----------------------------------------------------------------------
report.pdf                     john@example.com               read         2024-01-15 09:15:22
  ID: file_shared123
```

#### 5. Storage Management

```bash
# Check storage quota
> storage
======================================================================
  Storage Information
======================================================================

Allocated:     1.00 GB
Used:          156.78 MB
Available:     891.22 MB
Usage:         15.30%

[███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 15.3%
```

### Admin Monitoring

```bash
# Start admin monitor
python -m admin.admin_monitor

# Or quick status check
python -m admin.admin_monitor --status

# Or real-time monitoring
python -m admin.admin_monitor --monitor
```

Admin dashboard shows:

```
================================================================================
CLOUD STORAGE PLATFORM - SYSTEM STATUS
================================================================================

📊 STORAGE OVERVIEW:
  Total Capacity:     10.00 GB
  Allocated:          3.00 GB
  Actually Used:      156.78 MB
  Available:          7.00 GB

  Allocation: [███████████░░░░░░░░░░░░░░░░░░░░░░░░░░░] 30.0%
  Usage:      [█████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 5.1%

👥 USER STATISTICS:
  Total Users:        3

💾 STORAGE NODES:
  Total Nodes:        3
  Online Nodes:       3
  Offline Nodes:      0
  Node Health:        🟢 HEALTHY (100%)

📁 FILE STATISTICS:
  Total Files:        12
  Total Chunks:       48
  Avg Chunks/File:    4.0

🏥 SYSTEM HEALTH:
  Overall Health:     100.0%
================================================================================
```

## CLI Commands Reference

### Authentication

| Command                    | Description         | Example                              |
| -------------------------- | ------------------- | ------------------------------------ |
| `send-otp <email>`         | Send OTP to email   | `send-otp user@example.com`          |
| `verify-otp <email> <otp>` | Verify OTP          | `verify-otp user@example.com 123456` |
| `enroll <email> <name>`    | Register new user   | `enroll user@example.com "John Doe"` |
| `login <email>`            | Login existing user | `login user@example.com`             |
| `logout`                   | Logout current user | `logout`                             |

### File Operations

| Command                   | Description        | Example                          |
| ------------------------- | ------------------ | -------------------------------- |
| `upload <path>`           | Upload file        | `upload /path/file.pdf`          |
| `download <id> [path]`    | Download file      | `download file_123 ~/downloads/` |
| `list` (or `ls`)          | List files         | `list`                           |
| `delete <id>`             | Move to trash      | `delete file_123`                |
| `delete <id> --permanent` | Permanently delete | `delete file_123 --permanent`    |
| `info <id>`               | Show file info     | `info file_123`                  |
| `mkdir <name>`            | Create folder      | `mkdir Documents`                |

### Sharing

| Command                     | Description       | Example                                |
| --------------------------- | ----------------- | -------------------------------------- |
| `share <id> <email> [perm]` | Share file        | `share file_123 user@example.com read` |
| `shared`                    | List shared files | `shared`                               |

### Storage

| Command   | Description       | Example   |
| --------- | ----------------- | --------- |
| `storage` | Show storage info | `storage` |

### Utility

| Command            | Description  |
| ------------------ | ------------ |
| `help`             | Show help    |
| `clear`            | Clear screen |
| `exit` (or `quit`) | Exit CLI     |

## Dynamic Storage Scaling

The system automatically adjusts total storage as nodes are added/removed:

```bash
# Start with 2GB
python -m node.storage_node node1 localhost 9001 2
# → Global storage: 2GB

# Add 3GB
python -m node.storage_node node2 localhost 9002 3
# → Global storage: 5GB

# Add 5GB
python -m node.storage_node node3 localhost 9003 5
# → Global storage: 10GB
```

Check current capacity:

```bash
python -m admin.admin_monitor --status
```

## Troubleshooting

### Database Connection Error

**Error:** `could not connect to server`

**Solution:**

1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify database exists: `psql -U cloud_user -d cloud_storage`
3. Check `.env` credentials match PostgreSQL setup

### OTP Not Sending

**Error:** `Email service unavailable`

**Solution:**

1. Verify Gmail credentials in `.env`
2. Check Gmail App Password is correct (16 characters, no spaces)
3. System falls back to TEST MODE showing OTP in console

### Storage Quota Exceeded

**Error:** `Storage quota exceeded`

**Solution:**

- User has used their 1GB allocation
- Delete old files or increase quota in database:

```sql
UPDATE users
SET storage_allocated = 2147483648
WHERE email = 'user@example.com';
-- 2GB = 2,147,483,648 bytes
```

### Node Not Registering

**Error:** Node starts but server doesn't show it

**Solution:**

1. Check server is running on port 50051
2. Verify node can reach server
3. Check server logs for registration errors

## Production Deployment

### Security Checklist

- [ ] Change `ADMIN_KEY` to strong random value
- [ ] Use strong PostgreSQL passwords
- [ ] Enable SSL for gRPC (production)
- [ ] Set up firewall rules
- [ ] Use environment-specific `.env` files
- [ ] Enable database backups
- [ ] Implement rate limiting
- [ ] Add logging and monitoring

### Multi-Machine Deployment

```bash
# Server (192.168.1.10)
python -m server.cloud_server

# Node 1 (192.168.1.20)
python -m node.storage_node node1 192.168.1.20 9001 100

# Node 2 (192.168.1.21)
python -m node.storage_node node2 192.168.1.21 9001 100

# Client (anywhere)
# Update .env:
GRPC_SERVER_HOST=192.168.1.10
GRPC_SERVER_PORT=50051
```

## Support

For issues or questions:

1. Check server logs
2. Review admin monitor output
3. Verify all services are running
4. Check database connectivity

Enjoy your cloud storage platform! 🚀
