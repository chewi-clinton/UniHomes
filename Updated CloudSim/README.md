# Distributed Cloud Storage System

A Python-based distributed cloud storage system that simulates how files are stored across multiple nodes in a cloud infrastructure. This project demonstrates core concepts of distributed systems including node registration, heartbeat monitoring, chunk-based file distribution, and fault tolerance.

## 🌟 Features

- **Cloud Gateway**: Central coordinator that manages nodes and file uploads
- **Storage Nodes**: Independent storage servers that store file chunks
- **File Chunking**: Automatic splitting of files into chunks distributed across nodes
- **Heartbeat Monitoring**: Real-time health checking of storage nodes
- **Persistent Storage**: Database persistence for files, chunks, and node metadata
- **Real-time Dashboard**: Live status displays for gateway and nodes
- **Automated Demo**: Quick demonstration script to see the system in action
- **Comprehensive Testing**: Built-in system tests for all components

## 📋 Prerequisites

- Python 3.7 or higher
- No external dependencies required (uses Python standard library only)

## 🚀 Quick Start

### 1. Setup

First, run the setup script to prepare the system:

```bash
python setup.py
```

This will:

- Make all Python scripts executable
- Clean up any existing storage directories
- Reset the database

### 2. Start the Cloud Gateway

Open a terminal and start the gateway:

```bash
python cloud_gateway.py
```

The gateway will start listening on:

- Port 8000: File uploads
- Port 8001: Node registration and heartbeats

### 3. Create and Start Storage Nodes

In separate terminals, create and start nodes:

```bash
# Terminal 2: Create and start Node 1
python create_node.py node1 --storage 1 --cpu 2
python start_node.py node1

# Terminal 3: Create and start Node 2
python create_node.py node2 --storage 2 --cpu 4
python start_node.py node2
```

### 4. Upload Files

In another terminal, upload a file:

```bash
python upload_client.py yourfile.txt
```

## 🎮 Automated Demo

For a quick demonstration, use the demo script:

```bash
python demo.py
```

This will:

1. Create a test file
2. Start the Cloud Gateway
3. Create and start two storage nodes
4. Upload the test file automatically
5. Open everything in separate terminals

## 📁 Project Structure

```
distributed-cloud-storage/
├── cloud_gateway.py      # Main gateway server
├── storage_node.py       # Storage node implementation
├── upload_client.py      # File upload client
├── download_client.py    # File download client (basic)
├── create_node.py        # Node creation utility
├── start_node.py         # Node startup utility
├── demo.py               # Automated demo script
├── setup.py              # Setup and cleanup script
├── system_test.py        # Comprehensive system tests
├── README.md             # This file
├── requirements.txt      # Python dependencies (none needed)
├── cloud_db.pkl          # Database file (created at runtime)
├── nodes_config.json     # Node configurations (created at runtime)
└── storage_*/            # Node storage directories (created at runtime)
```

## 🔧 Components

### Cloud Gateway

The central coordinator that:

- Manages node registration and health monitoring
- Handles file upload requests
- Distributes file chunks across nodes
- Maintains metadata about files and chunks
- Provides real-time system statistics

**Key Features:**

- Thread-safe operations with locks
- Persistent database (cloud_db.pkl)
- Automatic node failure detection
- Real-time status dashboard

### Storage Node

Independent storage servers that:

- Register with the Cloud Gateway
- Send periodic heartbeats
- Store file chunks on disk
- Handle chunk storage and retrieval requests
- Monitor their own statistics

**Key Features:**

- Autonomous operation
- Real disk space allocation
- Automatic reconnection on network failures
- Real-time performance metrics

### Upload Client

Simple client for uploading files:

- Connects to Cloud Gateway
- Reads and transmits file data
- Receives confirmation and file ID
- Reports upload status

### Download Client

Basic client for downloading files:

- Queries file metadata
- Retrieves chunks from nodes
- Reconstructs original file
- _(Note: Basic implementation included)_

## 💻 Usage Examples

### Creating Nodes with Custom Configuration

```bash
# Node with 5GB storage and 4 CPU cores
python create_node.py bignode --storage 5 --cpu 4

# Node on specific port
python create_node.py node3 --port 9010

# Node on remote host
python create_node.py remote1 --host 192.168.1.100 --port 9001
```

### List All Nodes

```bash
python create_node.py --list
```

### Upload Various File Types

```bash
python upload_client.py document.pdf
python upload_client.py image.jpg
python upload_client.py video.mp4
```

### Upload to Remote Gateway

```bash
python upload_client.py file.txt remote_host 8000
```

## 🧪 Testing

Run comprehensive system tests:

```bash
python system_test.py
```

This will test:

- File existence and syntax
- Port availability
- Node creation and configuration
- Network communication
- JSON serialization
- Storage allocation
- Multi-threading
- And more...

## 📊 System Architecture

```
┌─────────────────┐
│  Upload Client  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│     Cloud Gateway           │
│  - File Management          │
│  - Chunk Distribution       │
│  - Node Health Monitoring   │
└──┬───────────────────────┬──┘
   │                       │
   ▼                       ▼
┌──────────────┐    ┌──────────────┐
│ Storage Node │    │ Storage Node │
│   (Node 1)   │    │   (Node 2)   │
│              │    │              │
│ - Chunk A    │    │ - Chunk B    │
│ - Chunk C    │    │ - Chunk D    │
└──────────────┘    └──────────────┘
```

## 🔄 File Upload Process

1. **Client** uploads file to **Gateway**
2. **Gateway** splits file into chunks (default: 3 chunks)
3. **Gateway** selects available nodes using round-robin
4. **Gateway** sends chunks to selected nodes
5. **Nodes** store chunks on disk and send ACK
6. **Gateway** saves metadata to database
7. **Client** receives file ID and confirmation

## 💓 Heartbeat System

- Nodes send heartbeats every 30 seconds
- Gateway marks nodes offline after 60 seconds without heartbeat
- Nodes automatically attempt reconnection if registration fails
- Dashboard shows real-time node status

## 📝 Configuration

### Node Configuration (nodes_config.json)

```json
{
  "node1": {
    "node_id": "node1",
    "host": "localhost",
    "port": 9001,
    "storage_capacity_gb": 1,
    "cpu_cores": 2,
    "bandwidth": "1Gbps",
    "storage_dir": "storage_node1",
    "status": "created"
  }
}
```

### Gateway Database (cloud_db.pkl)

Stores:

- Node registry and status
- File metadata
- Chunk locations
- Upload history

## 🛠️ Advanced Usage

### Multiple Gateway Instances

```python
# Start gateway on different ports
gateway = CloudGateway(host='localhost', upload_port=8002, node_port=8003)
gateway.start()
```

### Custom Storage Allocation

```python
# 10GB storage node
node = StorageNode('bignode', storage_capacity=10*1024*1024*1024)
node.start()
```

### Programmatic File Upload

```python
from upload_client import UploadClient

client = UploadClient('localhost', 8000)
client.upload_file('myfile.txt')
```

## ⚠️ Limitations

- No authentication/authorization
- No encryption for data in transit or at rest
- Basic error recovery
- No data replication/redundancy
- No chunk reassembly for downloads (basic implementation)
- Single gateway (no gateway clustering)

## 🔜 Future Enhancements

- [ ] Data replication across multiple nodes
- [ ] Chunk-level checksums and validation
- [ ] Complete download client with chunk reassembly
- [ ] Gateway clustering for high availability
- [ ] Web-based management interface
- [ ] User authentication and access control
- [ ] Encryption for data security
- [ ] Load balancing algorithms
- [ ] Automatic chunk migration
- [ ] RESTful API interface

## 🐛 Troubleshooting

### Ports Already in Use

```bash
# Check what's using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process or use different ports
```

### Nodes Not Registering

- Ensure Cloud Gateway is running first
- Check firewall settings
- Verify ports are not blocked
- Check terminal output for error messages

### Database Corruption

```bash
# Reset the system
python setup.py
```

### Storage Allocation Fails

- Check available disk space
- Reduce node storage capacity
- Verify write permissions in directory

## 📄 License

This project is for educational purposes. Feel free to modify and distribute.

## 👥 Contributing

This is an educational project demonstrating distributed systems concepts. Contributions, improvements, and bug fixes are welcome!

## 📞 Support

For issues or questions:

- Check the troubleshooting section
- Review terminal output for error messages
- Run system tests: `python system_test.py`

## 🎓 Educational Value

This project demonstrates:

- Distributed system architecture
- Client-server communication
- Socket programming in Python
- Multi-threading and concurrency
- Data serialization (JSON)
- Persistent storage
- Health monitoring and fault detection
- File chunking and distribution

Perfect for learning about cloud storage systems, distributed computing, and network programming!

---

**Note**: This is a simulation/educational project. For production systems, consider using established solutions like Ceph, GlusterFS, or cloud providers (AWS S3, Google Cloud Storage, etc.).
