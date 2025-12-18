# Quick Start Guide

Get the Multi-AP Mesh Network up and running in 5 minutes (software validation).

## Prerequisites

- Python 3.12+
- Git (to access this repo)
- Terminal/command line access

## Step 1: Validate Installation

```bash
cd /Users/annhoward/src/solarpunk_utopia/mesh_network

# Run validation script
python validate_installation.py
```

Expected output: All file checks should pass ✅

## Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python validate_installation.py
```

All checks should now pass, including Python modules.

## Step 3: Run Example

```bash
# Run integration examples
python example_integration.py
```

You'll see demonstrations of:
- Mode C operation (store-and-forward)
- Mode A detection
- Bridge node concepts

## Step 4: Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run test suite
pytest bridge_node/tests/ -v

# Run with coverage
pytest bridge_node/tests/ --cov=bridge_node --cov-report=html
```

Expected: All tests pass ✅

## Step 5: Start Bridge API (Optional)

```bash
# Start bridge management API
cd bridge_node
python main.py
```

Then in another terminal:

```bash
# Test API endpoints
curl http://localhost:8002/bridge/health
curl http://localhost:8002/bridge/status
```

## Next Steps

### For Development/Testing

1. **Read the docs:**
   - `README.md` - System overview
   - `docs/deployment_guide.md` - Deployment details
   - `docs/mode_a_requirements.md` - Mode A specifics

2. **Explore the code:**
   - `bridge_node/services/` - Core services
   - `bridge_node/api/` - API endpoints
   - `bridge_node/tests/` - Test suite

3. **Try the example:**
   ```bash
   # Run full bridge node example (runs indefinitely)
   python example_integration.py --bridge
   ```

### For Physical Deployment

1. **Prepare hardware:**
   - 3-4 Raspberry Pi 4 (for APs)
   - 2+ Android phones (for bridge nodes)
   - Power supplies (solar for outdoor, wall for indoor)

2. **Deploy first AP:**
   ```bash
   # Copy config to Pi
   scp ap_configs/garden_ap.json pi@raspberrypi:/tmp/

   # SSH to Pi and run deployment
   ssh pi@raspberrypi
   sudo ./deploy_ap_raspberry_pi.sh /tmp/garden_ap.json
   ```

3. **Deploy DTN node on AP:**
   - Copy `/app/` directory to Raspberry Pi
   - Install Python dependencies
   - Run DTN node on port 8000
   - Configure systemd service for autostart

4. **Configure bridge nodes:**
   - Install Solarpunk app on Android phones
   - Enable bridge role in settings
   - Let bridge nodes walk between islands

5. **Monitor and validate:**
   ```bash
   # Check bridge metrics
   curl http://localhost:8002/bridge/metrics

   # Check sync stats
   curl http://localhost:8002/bridge/sync/stats
   ```

## Common Commands

### Check Bridge Status
```bash
curl http://localhost:8002/bridge/status | jq
```

### Get Metrics
```bash
curl http://localhost:8002/bridge/metrics | jq
```

### Trigger Manual Sync
```bash
curl -X POST http://localhost:8002/bridge/sync/manual
```

### Check Mode
```bash
curl http://localhost:8002/bridge/mode | jq
```

### Export Metrics
```bash
curl "http://localhost:8002/bridge/metrics/export?filepath=/tmp/metrics.json"
```

## Troubleshooting

### Import Error
```
❌ Python module import failed: No module named 'httpx'
```
**Fix:** `pip install -r requirements.txt`

### Port Already in Use
```
ERROR: [Errno 48] Address already in use
```
**Fix:** Change port in `bridge_node/main.py` or stop other service

### Tests Fail
```
pytest bridge_node/tests/ -v
```
**Fix:** Check error messages, ensure dependencies installed

### Can't Find Modules
```
ModuleNotFoundError: No module named 'bridge_node'
```
**Fix:** Run from mesh_network directory, not bridge_node directory

## File Locations

```
mesh_network/
├── README.md                    # Main documentation
├── QUICKSTART.md               # This file
├── IMPLEMENTATION_SUMMARY.md   # Complete implementation details
├── requirements.txt            # Python dependencies
├── validate_installation.py    # Validation script
├── example_integration.py      # Integration examples
│
├── ap_configs/                 # AP configuration templates
│   ├── garden_ap.json
│   ├── kitchen_ap.json
│   ├── workshop_ap.json
│   └── library_ap.json
│
├── bridge_node/                # Bridge node software
│   ├── services/              # Core services
│   ├── api/                   # API endpoints
│   ├── tests/                 # Test suite
│   └── main.py                # Application entry
│
├── mode_a/                     # Mode A (BATMAN-adv)
│   └── scripts/               # Setup scripts
│
└── docs/                       # Documentation
    ├── deployment_guide.md
    └── mode_a_requirements.md
```

## Support

**Questions?**
- Check `README.md` for detailed documentation
- Review `docs/deployment_guide.md` for deployment help
- See `docs/mode_a_requirements.md` for Mode A specifics
- Read `IMPLEMENTATION_SUMMARY.md` for implementation details

**Issues?**
- Run validation: `python validate_installation.py`
- Check logs in bridge node application
- Review test output: `pytest bridge_node/tests/ -v`

## Success Criteria

You're ready for deployment when:

- ✅ Validation script passes all checks
- ✅ Dependencies installed successfully
- ✅ Example runs without errors
- ✅ Tests pass (pytest)
- ✅ API starts and responds to health checks
- ✅ You understand Mode C vs Mode A
- ✅ You've read the deployment guide

## Estimated Time

- **Software validation:** 5 minutes
- **Reading documentation:** 30 minutes
- **Understanding architecture:** 1 hour
- **First AP deployment:** 2 hours
- **Complete 4-island deployment:** 1 day
- **Adding bridge nodes:** 1 hour per device
- **Mode A setup (optional):** 2-4 hours

## What's Next?

1. ✅ Software is complete
2. ⏳ Prepare hardware (Raspberry Pis, phones)
3. ⏳ Deploy first AP island
4. ⏳ Test client connectivity
5. ⏳ Deploy DTN node on AP
6. ⏳ Configure first bridge node
7. ⏳ Test bridge walks between islands
8. ⏳ Scale to full 4-island deployment

**Status:** Software ready, hardware deployment pending.

---

**Quick Links:**
- Main docs: [README.md](README.md)
- Deployment: [docs/deployment_guide.md](docs/deployment_guide.md)
- Mode A: [docs/mode_a_requirements.md](docs/mode_a_requirements.md)
- Implementation: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
