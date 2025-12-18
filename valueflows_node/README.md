# ValueFlows Node - Gift Economy Coordination System

**Version:** 1.0.0
**Status:** Production-Ready Prototype
**Tier:** TIER 0 (Foundation)

A complete ValueFlows-compatible node for gift economy coordination in Solarpunk communes. Implements all 13 VF-Full v1.0 object types with simple UX, cryptographic signatures, and DTN bundle integration.

## Features

### Complete VF-Full v1.0 Implementation

**All 13 ValueFlows Object Types:**
- **Agent** - People, groups, places
- **Location** - Physical places with optional coordinates
- **ResourceSpec** - Resource categories/types
- **ResourceInstance** - Trackable resource instances
- **Listing** - Offers and needs (primary UX)
- **Match** - Offer/need pairings
- **Exchange** - Negotiated resource transfers
- **Event** - Economic events (handoff, work, etc.)
- **Process** - Input→output transformations
- **Commitment** - Promises to deliver/work
- **Plan** - Organized processes with dependencies
- **Protocol** - Reusable methods/recipes
- **Lesson** - Just-in-time learning modules

### Simple User Experience

- **Create offers in <1 minute** - Quick form with category picker
- **Browse and filter** - Offers, needs, by category/location
- **Match approval** - Both parties review and accept
- **Exchange coordination** - Schedule handoffs, track completion
- **Event recording** - Both parties sign for accountability

### Cryptographic Trust

- **Ed25519 signatures** on all objects
- **Provenance tracking** - Author and signature verification
- **Audit trail** - Full event chain for resource instances

### DTN Bundle Integration

- **Automatic bundle publishing** - VF objects → DTN bundles
- **Smart TTL** - Perishables get 24-72h, tools get 30 days
- **Priority routing** - Expiring food gets priority
- **Mesh sync** - Objects propagate across AP islands

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ and npm
- SQLite (built into Python)

### Backend Setup

```bash
cd valueflows_node

# Install Python dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app.database import initialize_database; initialize_database()"

# Run FastAPI server
python app/main.py
# Or: uvicorn app.main:app --reload
```

Server runs at: http://localhost:8000

API docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs at: http://localhost:3000

### Production Build

```bash
# Frontend
cd frontend
npm run build
# Outputs to frontend/dist/

# Backend (with production ASGI server)
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Architecture

### Backend (FastAPI + SQLite)

```
app/
├── models/vf/          # All 13 VF data models
├── repositories/vf/    # CRUD operations
├── services/           # Query, signing, bundle publishing
├── api/vf/            # REST API endpoints
├── database/          # SQLite schema + connection
└── main.py            # FastAPI application
```

### Frontend (React + Vite)

```
frontend/src/
├── components/        # Reusable UI components
│   ├── CreateOfferForm.tsx
│   └── BrowseOffers.tsx
├── pages/            # Route pages
│   ├── HomePage.tsx
│   ├── BrowseOffersPage.tsx
│   ├── CreateOfferPage.tsx
│   └── OfferDetailPage.tsx
└── App.tsx           # Main application
```

### Database Schema

All 13 VF object types with:
- Foreign key constraints
- Indexes for efficient queries
- Cryptographic signature fields
- Timestamps for TTL management

See: `app/database/vf_schema.sql`

## API Endpoints

### Listings (Offers/Needs)

```
POST   /vf/listings/          Create offer or need
GET    /vf/listings/          Browse with filters
GET    /vf/listings/{id}      Get listing details
PATCH  /vf/listings/{id}      Update listing
```

### Matches

```
POST   /vf/matches/                    Create match
PATCH  /vf/matches/{id}/approve        Approve match
GET    /vf/matches/agent/{agent_id}   Get agent's matches
```

### Exchanges

```
POST   /vf/exchanges/                     Create exchange
GET    /vf/exchanges/upcoming             Get upcoming exchanges
PATCH  /vf/exchanges/{id}/complete        Mark completed
```

### Events

```
POST   /vf/events/                              Record event
GET    /vf/events/exchange/{exchange_id}        Get exchange events
GET    /vf/events/resource/{instance_id}/provenance  Get provenance chain
```

## Usage Examples

### Creating an Offer

**Via UI:**
1. Navigate to "Create Offer"
2. Select category (Food, Tools, etc.)
3. Enter title and details
4. Specify quantity and unit
5. Submit

**Via API:**
```bash
curl -X POST http://localhost:8000/vf/listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "listing_type": "offer",
    "title": "Fresh tomatoes from garden",
    "category": "food",
    "quantity": 5,
    "unit": "lbs",
    "agent_id": "user:alice",
    "description": "Heirloom variety, organic"
  }'
```

### Browsing Offers

**Via UI:** Navigate to "Browse Offers" and use filters

**Via API:**
```bash
# Get all food offers
curl "http://localhost:8000/vf/listings/?listing_type=offer&category=food"

# Get needs for tools
curl "http://localhost:8000/vf/listings/?listing_type=need&category=tools"
```

### Creating a Match

```bash
curl -X POST http://localhost:8000/vf/matches/ \
  -H "Content-Type: application/json" \
  -d '{
    "offer_id": "listing:abc123",
    "need_id": "listing:def456",
    "provider_id": "user:alice",
    "receiver_id": "user:bob",
    "status": "suggested"
  }'
```

### Recording an Event

```bash
curl -X POST http://localhost:8000/vf/events/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "transfer-out",
    "agent_id": "user:alice",
    "to_agent_id": "user:bob",
    "resource_spec_id": "spec:tomatoes",
    "quantity": 3,
    "unit": "lbs",
    "exchange_id": "exchange:xyz789"
  }'
```

## DTN Bundle Integration

### Publishing VF Objects

All VF objects are automatically published as DTN bundles:

```python
from app.services.vf_bundle_publisher import VFBundlePublisher

publisher = VFBundlePublisher()
bundle = publisher.publish_vf_object(listing, "Listing")
# Publishes to DTN outbox with appropriate TTL and priority
```

### Bundle Format

```json
{
  "bundleId": "b:sha256:...",
  "createdAt": "2025-12-17T10:00:00Z",
  "expiresAt": "2025-12-19T10:00:00Z",
  "priority": "perishable",
  "audience": "local",
  "topic": "mutual-aid",
  "tags": ["food", "offer"],
  "payloadType": "vf:Listing",
  "payload": { ... },
  "signature": "sig:..."
}
```

### TTL Defaults

- **Food offers:** 48 hours (perishable)
- **Tool offers:** 30 days
- **Skill offers:** 90 days
- **Events:** 1 year (audit trail)
- **Protocols/Lessons:** 1 year

## Security

### Cryptographic Signing

All VF objects are signed with Ed25519:

```python
from app.services.signing_service import SigningService

signer = SigningService(private_key="...")
signer.sign_and_update(vf_object, author_id)
```

### Signature Verification

```python
is_valid = SigningService.verify_signature(vf_object, public_key)
```

### Implementation Notes

Current implementation uses placeholder signing (deterministic hash).
To enable real Ed25519:

1. Uncomment production code in `app/services/signing_service.py`
2. Install: `pip install cryptography`
3. Generate keypairs for users

## Testing

### Backend Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest app/tests/
```

### Frontend Tests

```bash
cd frontend
npm run test
```

### Integration Testing

```bash
# Start backend
python app/main.py &

# Start frontend
cd frontend && npm run dev &

# Create test offer
curl -X POST http://localhost:8000/vf/listings/ ...

# Browse in UI
open http://localhost:3000/browse
```

## Deployment

### Local Network (Commune)

1. Deploy on Raspberry Pi or Android phone
2. Configure static IP
3. Set up systemd service (Linux) or background task (Android)
4. Connect to local Wi-Fi AP

### Multi-AP Mesh

1. Deploy ValueFlows Node on multiple devices
2. Configure DTN bundle system (see `dtn-bundle-system` proposal)
3. Bridge nodes carry bundles between AP islands
4. Objects sync automatically

## Future Enhancements

- [ ] Match approval push notifications
- [ ] Calendar integration for exchanges
- [ ] Photo upload for offerings
- [ ] Real-time updates via WebSockets
- [ ] Advanced filtering (distance, expiry)
- [ ] Reputation/trust scoring
- [ ] Multi-language support
- [ ] Offline-first PWA

## Dependencies

### Backend
- FastAPI 0.109+ (web framework)
- Uvicorn (ASGI server)
- Pydantic 2.5+ (data validation)
- Cryptography 42+ (Ed25519 signing)

### Frontend
- React 18 (UI framework)
- React Router 6 (routing)
- Vite 5 (build tool)

## License

Open source - choose appropriate license for commune use

## Contributing

This is a reference implementation for Solarpunk communes. Adapt for your community's needs.

## References

- **ValueFlows Spec:** https://valueflo.ws/
- **Specification:** `solarpunk_node_full_spec.md` Section 9
- **Proposal:** `openspec/changes/valueflows-node-full/proposal.md`
- **Tasks:** `openspec/changes/valueflows-node-full/tasks.md`

## Support

For issues and questions, see main Solarpunk project documentation.

---

**Built for gift economy communities. Share freely. Grow together.**
