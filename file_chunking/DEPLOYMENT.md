# File Chunking System - Deployment Guide

Complete guide for deploying the File Chunking System in production environments.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the System](#running-the-system)
5. [Integration with DTN](#integration-with-dtn)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Scaling and Performance](#scaling-and-performance)
8. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+), macOS 11+
- **Python**: 3.12 or higher
- **RAM**: 512MB (2GB recommended)
- **Storage**: 1GB for system + cache budget (10GB-100GB recommended)
- **CPU**: 1 core (2+ cores recommended)

### Recommended Requirements for Library Nodes

- **RAM**: 4GB+
- **Storage**: 100GB+ SSD for chunk storage
- **CPU**: 4+ cores for concurrent operations
- **Network**: Stable connectivity for DTN bundle exchange

## Installation

### 1. Install Python Dependencies

```bash
cd /Users/annhoward/src/solarpunk_utopia/file_chunking

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install fastapi uvicorn aiosqlite pydantic python-multipart
```

### 2. Initialize Database

```bash
# Database will be created automatically on first run
# Location: file_chunking/data/file_chunking.db

# Or initialize manually:
python -c "import asyncio; from file_chunking.database import init_db; asyncio.run(init_db())"
```

### 3. Create Required Directories

```bash
mkdir -p data/chunks
mkdir -p data/downloads
```

### 4. Verify Installation

```bash
# Run health check
python -m file_chunking.main &
sleep 2
curl http://localhost:8001/health
```

## Configuration

### Environment Variables

Create a `.env` file in the `file_chunking/` directory:

```bash
# Server Configuration
FILE_CHUNKING_HOST=0.0.0.0
FILE_CHUNKING_PORT=8001

# Chunk Configuration
CHUNK_SIZE=524288  # 512KB in bytes
MIN_CHUNK_SIZE=262144  # 256KB
MAX_CHUNK_SIZE=1048576  # 1MB

# Storage Configuration
CHUNK_STORAGE_PATH=./data/chunks
DOWNLOADS_PATH=./data/downloads

# Library Cache Configuration (for library nodes)
LIBRARY_CACHE_BUDGET=107374182400  # 100GB in bytes
LIBRARY_CACHE_ENABLED=true

# Database Configuration
DATABASE_PATH=./data/file_chunking.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/file_chunking.log
```

### Configuration for Different Node Types

#### Regular Node (User Node)

```bash
# Minimal cache, focus on personal files
LIBRARY_CACHE_BUDGET=10737418240  # 10GB
LIBRARY_CACHE_ENABLED=false
```

#### Library Node (Community Server)

```bash
# Large cache, serve popular content
LIBRARY_CACHE_BUDGET=107374182400  # 100GB
LIBRARY_CACHE_ENABLED=true

# Pre-publish cached files on startup
AUTO_PUBLISH_CACHE=true
```

#### Offline Node (Occasional Connectivity)

```bash
# Larger chunk size for efficiency
CHUNK_SIZE=1048576  # 1MB

# Conservative cache
LIBRARY_CACHE_BUDGET=5368709120  # 5GB
```

## Running the System

### Development Mode

```bash
cd /Users/annhoward/src/solarpunk_utopia/file_chunking

# Run with auto-reload
python -m file_chunking.main
```

### Production Mode (Systemd Service)

Create systemd service file: `/etc/systemd/system/file-chunking.service`

```ini
[Unit]
Description=File Chunking System
After=network.target

[Service]
Type=simple
User=solarpunk
Group=solarpunk
WorkingDirectory=/home/solarpunk/solarpunk_utopia/file_chunking
Environment="PATH=/home/solarpunk/solarpunk_utopia/file_chunking/venv/bin"
ExecStart=/home/solarpunk/solarpunk_utopia/file_chunking/venv/bin/python -m file_chunking.main
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable file-chunking
sudo systemctl start file-chunking
sudo systemctl status file-chunking
```

### Production Mode (Docker)

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY file_chunking/ ./file_chunking/

# Create data directories
RUN mkdir -p data/chunks data/downloads

# Expose port
EXPOSE 8001

# Run application
CMD ["python", "-m", "file_chunking.main"]
```

Build and run:

```bash
docker build -t file-chunking:latest .
docker run -d \
  --name file-chunking \
  -p 8001:8001 \
  -v /data/chunks:/app/data/chunks \
  -v /data/db:/app/data \
  file-chunking:latest
```

## Integration with DTN

### 1. Start DTN Bundle System

```bash
# In separate terminal
cd /Users/annhoward/src/solarpunk_utopia/app
python main.py
```

The DTN system runs on port 8000 by default.

### 2. Verify Integration

Both systems should be running:
- DTN Bundle System: http://localhost:8000
- File Chunking System: http://localhost:8001

### 3. Test Bundle Publishing

```bash
# Upload a file with automatic publishing
curl -X POST "http://localhost:8001/files/upload" \
  -F "file=@test.pdf" \
  -F "publish=true"

# Check DTN bundles
curl "http://localhost:8000/bundles?queue=outbox"
```

### 4. Register Bundle Receiver (Optional)

For automatic handling of incoming chunk bundles, integrate the bundle receiver:

```python
# In app/main.py, add during startup:
from file_chunking.services.bundle_receiver_service import register_with_dtn_system

@app.on_event("startup")
async def startup():
    # ... existing startup code ...

    # Register file chunking receiver
    await register_with_dtn_system()
```

## Monitoring and Maintenance

### Health Monitoring

```bash
# Check system health
curl http://localhost:8001/health

# Expected response:
{
  "status": "healthy",
  "storage": {
    "total_chunks": 150,
    "total_size_mb": 75.5
  },
  "cache": {
    "total_files": 10,
    "total_size_gb": 2.3,
    "usage_percentage": 23.0
  }
}
```

### Storage Monitoring

```bash
# Get storage statistics
curl http://localhost:8001/library/stats

# Monitor chunk storage directory
du -sh data/chunks
```

### Log Monitoring

```bash
# View logs (systemd)
sudo journalctl -u file-chunking -f

# View logs (Docker)
docker logs -f file-chunking

# View application logs
tail -f logs/file_chunking.log
```

### Database Maintenance

```bash
# Backup database
cp data/file_chunking.db data/file_chunking.db.backup

# Vacuum database (optimize)
sqlite3 data/file_chunking.db "VACUUM;"

# Check database integrity
sqlite3 data/file_chunking.db "PRAGMA integrity_check;"
```

### Cache Cleanup

```bash
# Clear cache (via API)
# TODO: Implement cache clear endpoint

# Manual cleanup (stop service first)
sudo systemctl stop file-chunking
rm -rf data/chunks/*
sqlite3 data/file_chunking.db "DELETE FROM chunks; DELETE FROM file_manifests;"
sudo systemctl start file-chunking
```

## Scaling and Performance

### Performance Tuning

#### 1. Optimize Chunk Size

```python
# For high-bandwidth networks
CHUNK_SIZE = 1048576  # 1MB chunks

# For low-bandwidth/intermittent networks
CHUNK_SIZE = 262144  # 256KB chunks

# For balanced performance
CHUNK_SIZE = 524288  # 512KB chunks (default)
```

#### 2. Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_chunks_file_status
ON chunks(file_hash, status);

CREATE INDEX IF NOT EXISTS idx_manifests_tags
ON file_manifests(tags);

-- Optimize database
PRAGMA optimize;
```

#### 3. Storage Optimization

```bash
# Use SSD for chunk storage
# Mount SSD at /data/chunks

# Enable filesystem caching
sudo sysctl -w vm.swappiness=10
sudo sysctl -w vm.vfs_cache_pressure=50
```

### Horizontal Scaling

#### Load Balancing Multiple Instances

```nginx
# nginx.conf
upstream file_chunking {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;

    location / {
        proxy_pass http://file_chunking;
        proxy_set_header Host $host;
    }
}
```

#### Shared Storage for Chunks

```bash
# Use NFS or distributed filesystem
mount -t nfs storage-server:/chunks /data/chunks

# Or use object storage (S3-compatible)
# Configure in chunk_storage_service.py
```

## Troubleshooting

### Common Issues

#### Issue: "Database locked" errors

**Cause**: Multiple processes accessing SQLite database

**Solution**: Use connection pooling or switch to PostgreSQL for production

```python
# In database/schema.py, increase timeout
_db = await aiosqlite.connect(str(DB_PATH), timeout=30.0)
```

---

#### Issue: High memory usage during large file uploads

**Cause**: Loading entire file into memory

**Solution**: Implement streaming uploads

```python
# Use streaming for files > 10MB
# Already implemented in ChunkingService.chunk_file()
```

---

#### Issue: Slow reassembly for large files

**Cause**: Sequential chunk retrieval

**Solution**: Implement parallel chunk retrieval (future enhancement)

---

#### Issue: Cache eviction too aggressive

**Cause**: Cache budget too small or priority scoring incorrect

**Solution**: Increase cache budget or adjust priority calculation

```python
# In library_cache_service.py
cache_budget_bytes = 200 * 1024 * 1024 * 1024  # 200GB
```

### Debug Mode

Enable detailed logging:

```python
# In main.py
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Performance Profiling

```bash
# Install profiling tools
pip install py-spy

# Profile running service
py-spy record -o profile.svg -- python -m file_chunking.main

# View profile
open profile.svg
```

## Security Considerations

### 1. Authentication

Implement authentication for production:

```python
# Add to API endpoints
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.post("/files/upload")
async def upload_file(
    token: str = Depends(security),
    # ... other params
):
    # Verify token
    if not verify_token(token):
        raise HTTPException(status_code=401)
```

### 2. Rate Limiting

```python
# Install slowapi
pip install slowapi

# Add to main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/files/upload")
@limiter.limit("10/minute")
async def upload_file(...):
    pass
```

### 3. File Validation

Already implemented:
- Hash verification for all chunks
- File size limits (configurable)
- MIME type validation

### 4. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 8001/tcp  # File chunking API
sudo ufw enable
```

## Backup and Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR=/backups/file-chunking
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
sqlite3 data/file_chunking.db ".backup $BACKUP_DIR/db_$DATE.db"

# Backup critical chunks (manifests)
# TODO: Implement selective backup

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

### Recovery Procedure

```bash
# Stop service
sudo systemctl stop file-chunking

# Restore database
cp /backups/file-chunking/db_20251217.db data/file_chunking.db

# Verify integrity
sqlite3 data/file_chunking.db "PRAGMA integrity_check;"

# Start service
sudo systemctl start file-chunking
```

---

**Version**: 1.0.0
**Last Updated**: 2025-12-17

For additional support, see README.md or contact the Solarpunk community.
