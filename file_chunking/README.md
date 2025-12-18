# File Chunking System (TIER 1)

Complete production system for content-addressed file chunking with DTN integration for Solarpunk mesh networks.

## Overview

The File Chunking System enables efficient distribution of large files (protocols, lessons, educational content, media) across delay-tolerant networks. Files are split into content-addressed chunks, distributed as DTN bundles, and reassembled on demand.

### Key Features

- **Content-Addressed Storage**: SHA-256 hashing for immutable file and chunk identification
- **Intelligent Chunking**: Configurable chunk sizes (256KB-1MB) for optimal network distribution
- **Merkle Tree Verification**: Efficient integrity checking for individual chunks and complete files
- **DTN Integration**: Seamless integration with Delay-Tolerant Networking bundle system
- **Opportunistic Retrieval**: Request missing chunks as needed, resume interrupted downloads
- **Library Node Caching**: Automatic caching of popular content for community access
- **Deduplication**: Identical chunks stored only once, reducing storage requirements

## Architecture

### System 1: Content-Addressed Storage (1.0 systems)

**Components:**
- SHA-256 content addressing for files and chunks
- SQLite database for metadata storage
- Filesystem-based chunk storage with sharding
- Automatic deduplication

**Implementation:**
- `HashingService`: SHA-256 hashing utilities
- `ChunkStorageService`: Filesystem storage with metadata tracking
- Database schema: `file_manifests`, `chunks` tables

### System 2: Chunking Engine (1.2 systems)

**Components:**
- File splitting into configurable chunks (256KB-1MB)
- Manifest generation with chunk references
- Merkle tree construction for verification
- Support for files up to 100MB+ (tested with multi-GB files)

**Implementation:**
- `ChunkingService`: File splitting and manifest generation
- `MerkleTreeService`: Merkle tree construction and verification
- `FileManifest`: Comprehensive file metadata with chunk references

### System 3: Opportunistic Retrieval (0.8 systems)

**Components:**
- Request missing chunks via DTN bundles
- Download progress tracking
- Automatic reassembly with verification
- Resume partial downloads
- Library nodes serve popular chunks

**Implementation:**
- `ChunkRequestService`: Orchestrate file downloads and chunk requests
- `ChunkPublisherService`: Serve chunks as DTN bundles
- `ReassemblyService`: Rebuild files from chunks with verification
- `LibraryCacheService`: Manage library node caching

## Installation

### Prerequisites

- Python 3.12+
- SQLite 3
- FastAPI and dependencies (see requirements)

### Setup

```bash
cd /Users/annhoward/src/solarpunk_utopia/file_chunking

# Install dependencies
pip install fastapi uvicorn aiosqlite pydantic

# Initialize database (automatic on first run)
python -m file_chunking.main
```

## Usage

### Start the Server

```bash
python -m file_chunking.main
```

The API will be available at `http://localhost:8001` with interactive docs at `http://localhost:8001/docs`.

### Upload and Chunk a File

```bash
curl -X POST "http://localhost:8001/files/upload" \
  -F "file=@permaculture_guide.pdf" \
  -F "tags=permaculture,education,protocol" \
  -F "description=Complete permaculture guide for community gardens" \
  -F "publish=true"
```

Response:
```json
{
  "fileHash": "file:sha256:abc123...",
  "fileName": "permaculture_guide.pdf",
  "fileSize": 5242880,
  "chunkCount": 11,
  "manifestBundleId": "b:sha256:def456...",
  "chunkBundleIds": ["b:sha256:...", "b:sha256:..."]
}
```

### Request a File Download

```bash
curl -X POST "http://localhost:8001/downloads/request" \
  -H "Content-Type: application/json" \
  -d '{
    "fileHash": "file:sha256:abc123...",
    "outputPath": "/downloads/permaculture_guide.pdf",
    "priority": 8
  }'
```

Response:
```json
{
  "requestId": "req:xyz789...",
  "fileHash": "file:sha256:abc123...",
  "fileName": "permaculture_guide.pdf",
  "status": "requesting_chunks",
  "totalChunks": 11,
  "receivedChunks": 0,
  "percentComplete": 0.0
}
```

### Check Download Progress

```bash
curl "http://localhost:8001/downloads/req:xyz789..."
```

Response:
```json
{
  "requestId": "req:xyz789...",
  "fileHash": "file:sha256:abc123...",
  "fileName": "permaculture_guide.pdf",
  "status": "downloading",
  "totalChunks": 11,
  "receivedChunks": 7,
  "percentComplete": 63.6
}
```

### Check File Availability

```bash
curl "http://localhost:8001/files/file:sha256:abc123.../availability"
```

Response:
```json
{
  "fileHash": "file:sha256:abc123...",
  "isAvailable": true,
  "hasManifest": true,
  "totalChunks": 11,
  "storedChunks": 11,
  "missingChunks": 0,
  "percentComplete": 100.0
}
```

### Library Node Operations

#### Add File to Cache

```bash
curl -X POST "http://localhost:8001/library/cache/file:sha256:abc123..." \
  -d "tags=education,popular"
```

#### List Cached Files

```bash
curl "http://localhost:8001/library/cache?limit=50"
```

#### Pre-Publish Cached Content

```bash
curl -X POST "http://localhost:8001/library/publish"
```

This publishes all cached files as DTN bundles, making them immediately available to the network.

## API Endpoints

### Files

- `POST /files/upload` - Upload and chunk a file
- `GET /files` - List files
- `GET /files/{file_hash}` - Get file information
- `GET /files/{file_hash}/availability` - Check file availability
- `DELETE /files/{file_hash}` - Delete file and chunks

### Downloads

- `POST /downloads/request` - Request file download
- `GET /downloads/{request_id}` - Get download status
- `GET /downloads` - List active downloads
- `POST /downloads/{request_id}/reassemble` - Manually trigger reassembly
- `DELETE /downloads/{request_id}` - Cancel download

### Chunks

- `GET /chunks/{chunk_hash}` - Get chunk information
- `GET /chunks/{chunk_hash}/data` - Get chunk data
- `GET /chunks/file/{file_hash}` - List chunks for a file
- `GET /chunks/{chunk_hash}/verify` - Verify chunk integrity

### Library Cache

- `POST /library/cache/{file_hash}` - Add file to cache
- `GET /library/cache` - List cached files
- `GET /library/stats` - Get cache statistics
- `POST /library/publish` - Pre-publish cached files

## DTN Integration

### Bundle Types

The system uses the following DTN bundle payload types:

1. **file:manifest** - File manifest with chunk references
   - Priority: LOW
   - TTL: 270 days (knowledge content)
   - Contains: File metadata, chunk hashes, Merkle root

2. **file:chunk** - Individual chunk data
   - Priority: LOW (normal distribution) or NORMAL (request response)
   - TTL: 270 days (pre-published) or 30 days (on-demand)
   - Contains: Base64-encoded chunk data, metadata

3. **file:chunk_request** - Request for a specific chunk
   - Priority: NORMAL
   - TTL: 7 days
   - Contains: Chunk hash, request ID

4. **file:manifest_request** - Request for a file manifest
   - Priority: NORMAL
   - TTL: 7 days
   - Contains: File hash, request ID

### Bundle Flow

#### Upload Flow

1. User uploads file via API
2. System chunks file, generates manifest
3. Chunks stored locally with metadata
4. Manifest published as DTN bundle (payloadType: "file:manifest")
5. (Optional) Chunks published as DTN bundles (payloadType: "file:chunk")

#### Download Flow

1. User requests file by hash
2. System checks for manifest locally
3. If no manifest: publishes manifest request bundle
4. When manifest received: identifies missing chunks
5. Publishes chunk request bundles for each missing chunk
6. As chunks arrive: stores, verifies, updates progress
7. When complete: reassembles file, verifies final hash
8. Saves to output path

#### Library Node Flow

1. Popular files added to cache
2. Cache manager maintains access counts
3. Pre-publish cached files to network
4. Serve chunk requests from cache
5. Evict low-priority files when over budget

## Configuration

### Chunk Size

Default: 512KB (configurable between 256KB-1MB)

```python
from file_chunking.services import ChunkingService

# Custom chunk size
chunking_service = ChunkingService(chunk_size=768 * 1024)  # 768KB
```

### Library Cache Budget

Default: 10GB

```python
from file_chunking.services import LibraryCacheService, ChunkStorageService

chunk_storage = ChunkStorageService()
library_cache = LibraryCacheService(
    chunk_storage=chunk_storage,
    cache_budget_bytes=20 * 1024 * 1024 * 1024  # 20GB
)
```

## Performance Characteristics

### Benchmarks (Target Performance)

- **10MB file retrieval**: < 30 minutes via library node (specification requirement)
- **Chunking throughput**: ~50MB/s (depends on disk I/O)
- **Reassembly throughput**: ~100MB/s (memory-bound)
- **Deduplication**: O(1) lookup via content hash
- **Merkle verification**: O(log n) per chunk

### Storage Efficiency

- **Deduplication**: Identical chunks stored once
- **Sharded storage**: First 2 hex chars of hash used for directory sharding
- **Metadata overhead**: ~200 bytes per chunk in SQLite
- **Typical chunk count**: 20 chunks per 10MB file (512KB chunks)

## Testing

### Run Tests

```bash
# Run all tests
pytest file_chunking/tests/

# Run specific test file
pytest file_chunking/tests/test_chunking.py -v

# Run with coverage
pytest file_chunking/tests/ --cov=file_chunking --cov-report=html
```

### Test Coverage

- Chunking: File splitting, manifest generation, Merkle trees
- Storage: Chunk storage, retrieval, deduplication, verification
- Reassembly: File reconstruction, partial downloads, verification
- DTN Integration: Bundle publishing, request handling

## Production Deployment

### Recommendations

1. **Storage**: Use SSD for chunk storage (faster I/O)
2. **Database**: Regular SQLite backups of metadata
3. **Cache**: Configure library cache budget based on available storage
4. **Monitoring**: Track chunk storage stats, cache usage, download success rates
5. **Security**: Run behind reverse proxy, implement authentication if needed

### Library Node Configuration

For community library nodes:

```python
# Large cache for popular content
cache_budget = 100 * 1024 * 1024 * 1024  # 100GB

# Pre-publish cached files on startup
library_cache.pre_publish_cached_files()

# Prioritize educational and protocol content
# (automatically via tag-based priority scoring)
```

## Troubleshooting

### Common Issues

**Issue**: Download stuck at "requesting_chunks"

**Solution**: Check network connectivity, verify library nodes are online and serving chunks.

---

**Issue**: Reassembly fails with "hash mismatch"

**Solution**: Chunks may be corrupted. Delete partial download and retry. Check chunk verification.

---

**Issue**: Out of storage space

**Solution**: Check cache budget, evict low-priority files, increase storage capacity.

## Contributing

This is production software for real Solarpunk communities. Contributions should:

- Maintain backward compatibility
- Include comprehensive tests
- Follow security best practices
- Document changes clearly

## License

Open source for community benefit.

## Support

For issues, questions, or contributions, see the main Solarpunk Utopia project documentation.

---

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2025-12-17
