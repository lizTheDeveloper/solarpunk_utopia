"""
ValueFlows Node - FastAPI Application

Main entry point for the ValueFlows gift economy coordination system.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .logging_config import configure_logging, get_logger
from .database import initialize_database
from .api.vf import listings, matches, exchanges, events, agents, resource_specs, commitments, discovery, bakunin_analytics
from .api import communities, abundance_osmosis
from .middleware import CorrelationIdMiddleware

# Configure structured logging
configure_logging(log_level=settings.log_level, json_logs=settings.json_logs)
logger = get_logger(__name__)


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
# Use config-managed allowed origins
allowed_origins = settings.allowed_origins
logger.info("CORS configured for origins: %s", allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Explicit list from env or dev defaults
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Correlation ID middleware (GAP-53: Request Tracing)
# Must be added before other middleware to ensure correlation IDs are available
app.add_middleware(CorrelationIdMiddleware)

# Include API routers
app.include_router(communities.router)
app.include_router(listings.router)
app.include_router(matches.router)
app.include_router(commitments.router)
app.include_router(exchanges.router)
app.include_router(events.router)
app.include_router(agents.router)
app.include_router(resource_specs.router)
app.include_router(discovery.router)
app.include_router(bakunin_analytics.router)  # GAP-64: Battery Warlord Detection
app.include_router(abundance_osmosis.router)  # GAP-63: Abundance Osmosis


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
    """
    Health check endpoint (GAP-51).
    Returns 503 if any dependency is unhealthy, 200 otherwise.
    """
    from .services import HealthCheckService, HealthStatus
    from fastapi import Response
    import json

    health_result = await HealthCheckService.health_check()

    # Return 503 if unhealthy
    status_code = 200 if health_result["status"] == HealthStatus.HEALTHY else 503

    return Response(
        content=json.dumps(health_result),
        status_code=status_code,
        media_type="application/json"
    )


@app.get("/ready")
async def readiness():
    """
    Kubernetes readiness probe endpoint (GAP-51).
    Returns 503 if service is not ready to accept traffic.
    """
    from .services import HealthCheckService
    from fastapi import Response
    import json

    ready_result = await HealthCheckService.readiness_check()
    status_code = 200 if ready_result["ready"] else 503

    return Response(
        content=json.dumps(ready_result),
        status_code=status_code,
        media_type="application/json"
    )


@app.get("/live")
async def liveness():
    """
    Kubernetes liveness probe endpoint (GAP-51).
    Returns 200 if service is alive and responsive.
    """
    from .services import HealthCheckService

    return await HealthCheckService.liveness_check()


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
