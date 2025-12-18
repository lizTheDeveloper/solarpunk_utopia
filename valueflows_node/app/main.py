"""
ValueFlows Node - FastAPI Application

Main entry point for the ValueFlows gift economy coordination system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import initialize_database
from .api.vf import listings, matches, exchanges, events


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(listings.router)
app.include_router(matches.router)
app.include_router(exchanges.router)
app.include_router(events.router)


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
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
