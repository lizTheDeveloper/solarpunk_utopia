"""
DTN Bundle System Backend for Solarpunk Mesh Network

This is the core DTN (Delay-Tolerant Networking) bundle transport layer.
All payloads (offers, needs, files, indexes, queries) move as signed bundles
with TTL, priority, audience controls, and hop limits.

Key features:
- Content-addressed bundles with Ed25519 signing
- 6-queue lifecycle management (inbox, outbox, pending, delivered, expired, quarantine)
- TTL enforcement with automatic expiration
- Cache budget management with eviction policy
- Priority-based forwarding (emergency first)
- Audience enforcement (public, local, trusted, private)
- Hop limit tracking to prevent loops

API Endpoints:
- POST /bundles - Create new bundle
- GET /bundles - List bundles in queue
- POST /bundles/receive - Receive bundle from peer
- GET /sync/index - Get bundle index for sync
- POST /sync/push - Receive multiple bundles
- GET /sync/pull - Pull bundles for forwarding

Background Services:
- TTL enforcement (runs every 60 seconds)
- Cache budget enforcement (on-demand)
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, close_db
from .api import bundles_router, sync_router, agents_router
from .api.auth import router as auth_router
from .api.vouch import router as vouch_router
from .services import TTLService, CryptoService, CacheService
from .middleware import CSRFMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
ttl_service: TTLService = None
crypto_service: CryptoService = None
cache_service: CacheService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    Handles startup and shutdown of background services.
    """
    global ttl_service, crypto_service, cache_service

    # Startup
    logger.info("Starting DTN Bundle System...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize crypto service (loads or generates keypair)
    crypto_service = CryptoService()
    fingerprint = crypto_service.get_public_key_fingerprint()
    logger.info(f"Crypto service initialized (fingerprint: {fingerprint})")

    # Initialize cache service (2GB default budget)
    cache_service = CacheService(storage_budget_bytes=2 * 1024 * 1024 * 1024)
    cache_stats = await cache_service.get_cache_stats()
    logger.info(f"Cache service initialized (budget: {cache_stats['budget_bytes']} bytes)")

    # Start TTL enforcement service
    ttl_service = TTLService(check_interval_seconds=60)
    await ttl_service.start()

    logger.info("DTN Bundle System started successfully")
    logger.info("=" * 60)
    logger.info("API available at http://localhost:8000")
    logger.info("Docs available at http://localhost:8000/docs")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Shutting down DTN Bundle System...")

    # Stop TTL service
    if ttl_service:
        await ttl_service.stop()

    # Close database
    await close_db()

    logger.info("DTN Bundle System shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="DTN Bundle System",
    description="Delay-Tolerant Networking bundle transport for Solarpunk mesh network",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (for development - adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSRF Protection middleware (GAP-56)
app.add_middleware(
    CSRFMiddleware,
    exempt_paths={
        "/",
        "/docs",
        "/openapi.json",
        "/health",
        "/node/info",
        "/auth/csrf-token",  # CSRF token endpoint must be exempt
        "/auth/register",  # Registration should be exempt
        "/auth/login",  # Login should be exempt
    }
)

# Register routers
app.include_router(bundles_router)
app.include_router(sync_router)
app.include_router(agents_router)
app.include_router(auth_router)
app.include_router(vouch_router)


@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "service": "DTN Bundle System",
        "version": "1.0.0",
        "description": "Delay-Tolerant Networking bundle transport for Solarpunk mesh network",
        "docs": "/docs",
        "endpoints": {
            "bundles": "/bundles",
            "sync": "/sync",
            "agents": "/agents",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    global cache_service

    # Get cache stats
    cache_stats = await cache_service.get_cache_stats()

    return {
        "status": "healthy",
        "cache": {
            "usage_percentage": cache_stats["usage_percentage"],
            "is_over_budget": cache_stats["is_over_budget"],
            "total_bundles": sum(cache_stats["queue_counts"].values())
        },
        "services": {
            "ttl_enforcement": "running" if ttl_service and ttl_service._running else "stopped",
            "crypto": "initialized" if crypto_service else "not initialized"
        }
    }


@app.get("/node/info")
async def node_info():
    """Get information about this node"""
    global crypto_service

    fingerprint = crypto_service.get_public_key_fingerprint()
    public_key = crypto_service.get_public_key_pem()

    return {
        "node_id": fingerprint,
        "public_key_fingerprint": fingerprint,
        "public_key": public_key,
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
