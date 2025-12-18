# DTN Bundle System - Quick Start Guide

Get the DTN Bundle System up and running in 5 minutes.

## Prerequisites

- Python 3.12 (recommended) or 3.10+
- Git (to clone the repository)

## Installation

```bash
# 1. Navigate to project directory
cd /Users/annhoward/src/solarpunk_utopia

# 2. Create virtual environment
python3.12 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

## Start the Server

```bash
# Start the server (from project root)
python -m app.main
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
DTN Bundle System started successfully
API available at http://localhost:8000
Docs available at http://localhost:8000/docs
```

The server is now running! 🎉

## Quick Test

Open a new terminal and try:

```bash
# Health check
curl http://localhost:8000/health | python3 -m json.tool

# Create a bundle
curl -X POST http://localhost:8000/bundles \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"message": "Hello from DTN!"},
    "payloadType": "test:Message",
    "priority": "normal",
    "audience": "public",
    "topic": "coordination",
    "tags": ["test"]
  }' | python3 -m json.tool

# List bundles
curl http://localhost:8000/bundles?queue=outbox | python3 -m json.tool
```

## Run Tests

```bash
# Unit tests
python test_dtn_system.py

# API integration tests
chmod +x test_api.sh
./test_api.sh
```

## Explore the API

Visit http://localhost:8000/docs for interactive API documentation.

## Common Tasks

### Create Different Bundle Types

**Emergency Bundle:**
```bash
curl -X POST http://localhost:8000/bundles \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"message": "Emergency: Fire in garden"},
    "payloadType": "alert:Emergency",
    "priority": "emergency",
    "audience": "public",
    "topic": "coordination",
    "tags": ["emergency", "fire"]
  }'
```
TTL: 12 hours

**Perishable Food Offer:**
```bash
curl -X POST http://localhost:8000/bundles \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"type": "offer", "content": "Fresh tomatoes available"},
    "payloadType": "vf:Listing",
    "priority": "perishable",
    "audience": "local",
    "topic": "mutual-aid",
    "tags": ["food", "perishable", "tomatoes"]
  }'
```
TTL: 48 hours

**Knowledge Article:**
```bash
curl -X POST http://localhost:8000/bundles \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"title": "Composting Guide", "content": "How to make compost..."},
    "payloadType": "protocol:Guide",
    "priority": "normal",
    "audience": "public",
    "topic": "knowledge",
    "tags": ["composting", "permaculture"]
  }'
```
TTL: 270 days

### Get Statistics

**Queue Statistics:**
```bash
curl http://localhost:8000/bundles/stats/queues | python3 -m json.tool
```

**Cache Statistics:**
```bash
curl http://localhost:8000/sync/stats | python3 -m json.tool
```

**Node Info:**
```bash
curl http://localhost:8000/node/info | python3 -m json.tool
```

### Simulate Peer Sync

**Get Index:**
```bash
curl "http://localhost:8000/sync/index?queue=pending&limit=100" | python3 -m json.tool
```

**Pull Bundles:**
```bash
curl "http://localhost:8000/sync/pull?max_bundles=10&peer_trust_score=0.8&peer_is_local=true" | python3 -m json.tool
```

## Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

## Project Structure

```
app/
├── main.py           - FastAPI application entry point
├── models/           - Data models (Bundle, Priority, Queue)
├── database/         - SQLite database and queue management
├── services/         - Business logic (crypto, TTL, cache, forwarding)
└── api/              - HTTP endpoints (bundles, sync)

data/
├── dtn_bundles.db    - SQLite database (created on first run)
└── keys/             - Ed25519 keypair (generated on first run)
    ├── node_private.pem
    └── node_public.pem
```

## Configuration

Edit `app/main.py` to configure:

- **Cache budget**: Default 2GB
  ```python
  cache_service = CacheService(storage_budget_bytes=2 * 1024 * 1024 * 1024)
  ```

- **TTL check interval**: Default 60 seconds
  ```python
  ttl_service = TTLService(check_interval_seconds=60)
  ```

- **Server host/port**: Default 0.0.0.0:8000
  ```python
  uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
  ```

## Troubleshooting

**ImportError: No module named 'pydantic'**
- Make sure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**Address already in use**
- Another process is using port 8000
- Change the port in `app/main.py` or stop the other process

**Database locked**
- Stop all running instances of the server
- Delete `data/dtn_bundles.db` to start fresh (will lose all bundles)

## Next Steps

1. **Read the full README**: `DTN_BUNDLE_SYSTEM_README.md`
2. **Explore the API**: http://localhost:8000/docs
3. **Run the tests**: `python test_dtn_system.py`
4. **Build on top**: Implement ValueFlows, agents, or Android integration

## Support

- Full documentation: `DTN_BUNDLE_SYSTEM_README.md`
- Implementation summary: `DTN_BUNDLE_SYSTEM_SUMMARY.md`
- Spec: `solarpunk_node_full_spec.md` (Section 4)
- Proposal: `openspec/changes/dtn-bundle-system/proposal.md`

---

Happy bundling! 📦
