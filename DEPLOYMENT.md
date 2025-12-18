# Solarpunk Mesh Network - Deployment Guide

**Complete deployment guide for production use in Solarpunk communes**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Hardware Deployment](#hardware-deployment)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Scaling](#scaling)

---

## Quick Start

Get the system running locally in 5 minutes:

```bash
# 1. Clone and setup
cd /Users/annhoward/src/solarpunk_utopia
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Start all backend services
./run_all_services.sh

# 3. Start frontend (in new terminal)
cd frontend
npm install
npm run dev

# 4. Access the application
# Frontend: http://localhost:3000
# Backend APIs: http://localhost:8000-8004
```

---

## Development Deployment

### Backend Services

**Option 1: All services with one script**
```bash
./run_all_services.sh
```

**Option 2: Individual services (separate terminals)**
```bash
# Terminal 1: DTN Bundle System
source venv/bin/activate
python -m app.main

# Terminal 2: ValueFlows Node
source venv/bin/activate
python -m valueflows_node.main

# Terminal 3: Discovery & Search
source venv/bin/activate
python -m discovery_search.main

# Terminal 4: File Chunking
source venv/bin/activate
python -m file_chunking.main

# Terminal 5: Bridge Management
source venv/bin/activate
python -m mesh_network.bridge_node.main
```

### Frontend Application

```bash
cd frontend
npm install      # First time only
npm run dev      # Development server with hot reload
```

Access at: **http://localhost:3000**

### Stop All Services

```bash
./stop_all_services.sh
```

---

## Production Deployment

### 1. Server Setup

**Requirements:**
- Ubuntu 22.04 LTS (or similar)
- Python 3.12+
- Node.js 18+
- 4GB RAM minimum
- 20GB disk space

**Install dependencies:**
```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip nodejs npm nginx
```

### 2. Application Setup

```bash
# Clone repository
git clone <repository-url>
cd solarpunk_utopia

# Backend setup
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend build
cd frontend
npm install
npm run build
cd ..
```

### 3. Create Systemd Services

Create service files in `/etc/systemd/system/`:

**solarpunk-dtn.service:**
```ini
[Unit]
Description=Solarpunk DTN Bundle System
After=network.target

[Service]
Type=simple
User=solarpunk
WorkingDirectory=/opt/solarpunk_utopia
Environment="PATH=/opt/solarpunk_utopia/venv/bin"
ExecStart=/opt/solarpunk_utopia/venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**solarpunk-valueflows.service:**
```ini
[Unit]
Description=Solarpunk ValueFlows Node
After=network.target solarpunk-dtn.service

[Service]
Type=simple
User=solarpunk
WorkingDirectory=/opt/solarpunk_utopia
Environment="PATH=/opt/solarpunk_utopia/venv/bin"
ExecStart=/opt/solarpunk_utopia/venv/bin/python -m valueflows_node.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create similar services for:
- `solarpunk-discovery.service`
- `solarpunk-chunking.service`
- `solarpunk-bridge.service`

**Enable and start:**
```bash
sudo systemctl enable --now solarpunk-dtn
sudo systemctl enable --now solarpunk-valueflows
sudo systemctl enable --now solarpunk-discovery
sudo systemctl enable --now solarpunk-chunking
sudo systemctl enable --now solarpunk-bridge
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/solarpunk`:

```nginx
server {
    listen 80;
    server_name solarpunk.local;  # Replace with your domain

    # Frontend
    root /opt/solarpunk_utopia/frontend/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxies
    location /api/dtn/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/vf/ {
        proxy_pass http://localhost:8001/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /api/bridge/ {
        proxy_pass http://localhost:8002/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /api/discovery/ {
        proxy_pass http://localhost:8003/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /api/files/ {
        proxy_pass http://localhost:8004/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        client_max_body_size 100M;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/solarpunk /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Firewall Configuration

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 6. SSL/TLS (Production)

Using Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d solarpunk.your-domain.com
```

---

## Docker Deployment

### Build and Run with Docker Compose

**Start all services:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
```

**Stop all services:**
```bash
docker-compose down
```

**Rebuild after changes:**
```bash
docker-compose up -d --build
```

### Access Services

- **Frontend:** http://localhost:80 (nginx)
- **DTN API:** http://localhost:8000
- **ValueFlows API:** http://localhost:8001
- **Bridge API:** http://localhost:8002
- **Discovery API:** http://localhost:8003
- **File Chunking API:** http://localhost:8004

### Data Persistence

Docker volumes automatically created:
- `dtn-data` - DTN bundle database
- `valueflows-data` - ValueFlows database
- `discovery-data` - Discovery indexes
- `chunking-data` - File chunk metadata
- `chunking-storage` - Actual file chunks
- `bridge-data` - Bridge metrics

**Backup volumes:**
```bash
docker run --rm -v solarpunk_utopia_dtn-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/dtn-backup.tar.gz /data
```

---

## Hardware Deployment

### Raspberry Pi as AP Island

**Requirements:**
- Raspberry Pi 4 (4GB+ recommended)
- SD card (32GB+)
- Power supply (solar + battery or wall)
- WiFi dongle (for dual WiFi: one for mesh, one for AP)

**Setup:**
```bash
# 1. Flash Raspberry Pi OS Lite

# 2. Install software
sudo apt update
sudo apt install -y hostapd dnsmasq python3-venv

# 3. Deploy AP configuration
cd /opt/solarpunk_utopia/mesh_network/mode_a/scripts
sudo ./deploy_ap_raspberry_pi.sh ../ap_configs/garden_ap.json

# 4. Install and start DTN service
# (Follow systemd service setup above)

# 5. Configure as AP preset
# Edit deployment preset in openspec/changes/phone-deployment-system/
```

**Monitoring:**
```bash
# Check AP status
sudo systemctl status hostapd
sudo systemctl status dnsmasq

# View connected devices
sudo hostapd_cli all_sta

# Check DTN service
sudo systemctl status solarpunk-dtn
```

### Android Phone as Bridge Node

**Requirements:**
- Android phone with LineageOS (or similar)
- Termux installed
- Python 3.12 via Termux
- Battery >80%

**Setup:**
```bash
# 1. Install Termux from F-Droid

# 2. In Termux:
pkg update && pkg upgrade
pkg install python git

# 3. Clone and setup
git clone <repository-url>
cd solarpunk_utopia
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Start bridge node
python -m mesh_network.bridge_node.main

# 5. Keep running in background
# Use Termux:Boot to auto-start on phone boot
```

**Bridge Configuration:**
- Set deployment preset to "Bridge"
- Increase cache budget (2-8GB)
- Enable aggressive forwarding
- Monitor battery level

---

## Monitoring & Maintenance

### Health Checks

**Service health:**
```bash
# DTN Bundle System
curl http://localhost:8000/health

# ValueFlows Node
curl http://localhost:8001/health

# Bridge Management
curl http://localhost:8002/bridge/health
```

**System stats:**
```bash
# DTN bundle stats
curl http://localhost:8000/bundles/stats/queues

# Bridge effectiveness
curl http://localhost:8002/bridge/metrics

# Discovery indexes
curl http://localhost:8003/discovery/stats

# File chunking cache
curl http://localhost:8004/library/stats
```

### Logs

**Development:**
```bash
tail -f logs/dtn_bundle_system.log
tail -f logs/valueflows_node.log
tail -f logs/bridge_management.log
```

**Production (systemd):**
```bash
sudo journalctl -u solarpunk-dtn -f
sudo journalctl -u solarpunk-valueflows -f
sudo journalctl -u solarpunk-bridge -f
```

### Database Maintenance

**Backup databases:**
```bash
# DTN bundles
cp app/data/bundles.db app/data/bundles.db.backup

# ValueFlows
cp valueflows_node/data/valueflows.db valueflows_node/data/valueflows.db.backup

# Discovery indexes
cp discovery_search/data/discovery.db discovery_search/data/discovery.db.backup
```

**Optimize databases:**
```bash
sqlite3 app/data/bundles.db "VACUUM;"
sqlite3 valueflows_node/data/valueflows.db "VACUUM;"
```

### Updates

**Pull latest changes:**
```bash
cd /opt/solarpunk_utopia
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Rebuild frontend
cd frontend
npm install
npm run build

# Restart services
sudo systemctl restart solarpunk-*
```

---

## Troubleshooting

### Services Won't Start

**Check logs:**
```bash
sudo journalctl -u solarpunk-dtn -n 50
```

**Common issues:**
- Port already in use: `sudo lsof -i :8000`
- Permission denied: Check user/group ownership
- Database locked: Stop all services, remove .db-wal files

### Database Errors

**Reset databases (CAUTION: deletes all data):**
```bash
sudo systemctl stop solarpunk-*
rm -f app/data/*.db*
rm -f valueflows_node/data/*.db*
rm -f discovery_search/data/*.db*
rm -f file_chunking/data/*.db*
sudo systemctl start solarpunk-*
```

### Network Issues

**Bridge not syncing:**
```bash
# Check bridge status
curl http://localhost:8002/bridge/status

# Check network connectivity
curl http://localhost:8002/bridge/network

# Manual sync
curl -X POST http://localhost:8002/bridge/sync/manual
```

**Bundles not propagating:**
```bash
# Check DTN queue stats
curl http://localhost:8000/bundles/stats/queues

# Check sync stats
curl http://localhost:8000/sync/stats

# Verify bundle signatures
curl http://localhost:8000/bundles?queue=quarantine
```

### Frontend Issues

**Build fails:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

**API calls failing:**
- Check backend services are running
- Verify ports in vite.config.ts
- Check CORS headers in nginx config

### Performance Issues

**High CPU:**
```bash
# Check running processes
top -u solarpunk

# Reduce cache budgets in config
# Increase TTL service interval
```

**High memory:**
```bash
# Check memory usage
free -h

# Reduce cache budgets
# Clear expired bundles
curl -X DELETE http://localhost:8000/bundles?queue=expired
```

**Slow queries:**
```bash
# Optimize databases
sqlite3 app/data/bundles.db "ANALYZE;"
sqlite3 valueflows_node/data/valueflows.db "ANALYZE;"
```

---

## Scaling

### Horizontal Scaling

**Multiple AP Islands:**
1. Deploy additional Raspberry Pi APs
2. Use different SSIDs (SolarpunkGarden, SolarpunkKitchen, etc.)
3. Configure unique subnets (10.44.1.0/24, 10.44.2.0/24, etc.)
4. Deploy bridge nodes to walk between islands

**Multiple Bridge Nodes:**
- More bridge nodes = faster propagation
- Aim for 1 bridge per 10-20 citizens
- Configure different routes/schedules
- Monitor effectiveness scores

### Vertical Scaling

**Increase cache budgets:**
- Edit service configurations
- Citizen: 256MB-1GB
- Bridge: 2GB-8GB
- AP: 2GB-8GB
- Library: 10GB-50GB

**Upgrade hardware:**
- Raspberry Pi 4 8GB for APs
- SSD instead of SD card
- Larger battery banks for bridge nodes

### Multi-Commune Federation

**Setup NATS for cross-commune sync:**
```bash
# Install NATS server
docker run -d -p 4222:4222 nats:latest

# Configure DTN to publish to NATS
# See openspec/AGENTS.md for NATS patterns
```

**Cross-commune routing:**
- Each commune runs complete system
- Bridge nodes sync via NATS
- Namespaced streams prevent conflicts
- TTL prevents infinite propagation

---

## Security Considerations

### Authentication

**Current state:** No authentication (suitable for trusted commune)

**Add authentication (future):**
- JWT tokens for API access
- Ed25519 identity for agents
- Capability-based access control

### Encryption

**Current state:**
- Ed25519 signing for bundles
- No encryption (local network only)

**Add encryption (future):**
- TLS for API endpoints
- Encrypted bundle payloads
- Signal protocol for private exchanges

### Privacy

**Current state:** Opt-in agents, no surveillance

**Best practices:**
- Run on isolated network (no internet)
- Trust on first use (TOFU) for new nodes
- Regular security audits
- Community governance of data policies

---

## Backup & Recovery

### Backup Strategy

**Daily backups:**
```bash
#!/bin/bash
# /opt/solarpunk_utopia/scripts/backup.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR=/backup/solarpunk/$DATE

mkdir -p $BACKUP_DIR

# Backup databases
cp app/data/*.db $BACKUP_DIR/
cp valueflows_node/data/*.db $BACKUP_DIR/
cp discovery_search/data/*.db $BACKUP_DIR/
cp file_chunking/data/*.db $BACKUP_DIR/

# Backup file chunks
tar czf $BACKUP_DIR/chunks.tar.gz file_chunking/storage/

# Backup crypto keys
cp app/data/ed25519_* $BACKUP_DIR/

echo "Backup complete: $BACKUP_DIR"
```

**Automate with cron:**
```bash
0 2 * * * /opt/solarpunk_utopia/scripts/backup.sh
```

### Recovery

**Restore from backup:**
```bash
sudo systemctl stop solarpunk-*

# Restore databases
cp /backup/solarpunk/20251217/*.db app/data/
cp /backup/solarpunk/20251217/*.db valueflows_node/data/

# Restore chunks
tar xzf /backup/solarpunk/20251217/chunks.tar.gz -C file_chunking/storage/

# Restore keys
cp /backup/solarpunk/20251217/ed25519_* app/data/

sudo systemctl start solarpunk-*
```

---

## Production Checklist

Before going live:

- [ ] All backend services running and healthy
- [ ] Frontend built and served via nginx
- [ ] SSL/TLS configured (if internet-connected)
- [ ] Firewall rules configured
- [ ] Systemd services enabled for auto-start
- [ ] Backup cron job configured
- [ ] Logs rotating properly
- [ ] Monitoring dashboards set up
- [ ] Hardware tested (APs, bridge nodes)
- [ ] Network topology validated
- [ ] Bundle propagation tested (<10 min)
- [ ] End-to-end tests passing
- [ ] Community training completed
- [ ] Documentation distributed

---

## Support

For issues and questions:
1. Check logs: `sudo journalctl -u solarpunk-* -f`
2. Review troubleshooting section above
3. Test with integration tests: `pytest tests/integration/`
4. Check component READMEs for specific systems

---

**This is production-ready deployment infrastructure for real Solarpunk communities. Deploy it. Use it. Iterate based on real-world needs. 🌱**
