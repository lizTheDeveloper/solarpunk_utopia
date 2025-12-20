"""
ValueFlows Node - FastAPI Application

Main entry point for the ValueFlows gift economy coordination system.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import initialize_database
from .api.vf import listings, matches, exchanges, events, agents, resource_specs, commitments, discovery, bakunin_analytics
from .api import communities, leakage_metrics

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database on startup"""
    # Startup
    print("🌱 Initializing ValueFlows Node...")
    initialize_database()
    print("✓ ValueFlows Node ready")

    yield

    # Shutdown
    print("👋 Shutting down ValueFlows Node...")


# Create FastAPI app
app = FastAPI(
    title="ValueFlows Node",
    description="Gift economy coordination system for Solarpunk communes",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (for frontend)
# Get allowed origins from environment variable
allowed_origins_str = os.getenv("ALLOWED_ORIGINS")

if not allowed_origins_str:
    # Development defaults (localhost only)
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    logger.warning("ALLOWED_ORIGINS not set, using development defaults: %s", allowed_origins)
else:
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
    logger.info("CORS configured for origins: %s", allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Explicit list from env or dev defaults
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(communities.router)
app.include_router(listings.router)
app.include_router(matches.router)
app.include_router(commitments.router)
app.include_router(exchanges.router)
app.include_router(events.router)
app.include_router(agents.router)
app.include_router(resource_specs.router)
app.include_router(leakage_metrics.router)
app.include_router(discovery.router)
app.include_router(bakunin_analytics.router)  # GAP-64: Battery Warlord Detection


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ValueFlows Node",
        "version": "1.0.0",
        "status": "running",
        "description": "Gift economy coordination for Solarpunk communes"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/vf/stats")
async def get_stats():
    """Get system statistics"""
    from .database import get_database
    from .repositories.vf.listing_repo import ListingRepository

    try:
        db = get_database()
        db.connect()
        listing_repo = ListingRepository(db.conn)

        stats = {
            "total_listings": listing_repo.count(),
            "active_offers": len(listing_repo.find_offers(status="active", limit=1000)),
            "active_needs": len(listing_repo.find_needs(status="active", limit=1000)),
        }

        db.close()
        return stats
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("valueflows_node.app.main:app", host="0.0.0.0", port=8001, reload=True)
