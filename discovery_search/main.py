"""
Discovery and Search System - Main Application

Integrates the discovery system with the DTN bundle system.
"""

import sys
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add app to path
app_path = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_path))

# Also add the root directory to path for proper imports
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from .database import init_discovery_db, close_discovery_db
from .api import discovery_router
from .api.discovery import init_discovery_services
from .services import (
    IndexPublisher,
    QueryHandler,
    ResponseBuilder,
    SpeculativeCacheManager,
)
from .bundle_processor import process_inbox_bundles

from app.services import CryptoService, BundleService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
index_publisher: IndexPublisher = None
query_handler: QueryHandler = None
response_builder: ResponseBuilder = None
cache_manager: SpeculativeCacheManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    Handles startup and shutdown of discovery services.
    """
    global index_publisher, query_handler, response_builder, cache_manager

    # Startup
    logger.info("Starting Discovery and Search System...")

    # Initialize database
    await init_discovery_db()
    logger.info("Discovery database initialized")

    # Initialize crypto service
    crypto_service = CryptoService()
    bundle_service = BundleService(crypto_service)
    node_id = crypto_service.get_public_key_fingerprint()
    node_public_key = crypto_service.get_public_key_pem()

    logger.info(f"Node ID: {node_id}")

    # Initialize discovery services
    init_discovery_services(node_id, node_public_key, bundle_service)

    # Get service instances
    from .api.discovery import get_services
    services = get_services()
    index_publisher = services["publisher"]
    query_handler = services["query_handler"]
    response_builder = services["response_builder"]
    cache_manager = services["cache_manager"]

    # Start index publisher
    await index_publisher.start()
    logger.info("Index publisher started")

    # Start background task for processing bundles
    bundle_processor_task = asyncio.create_task(
        _bundle_processor_loop(query_handler, response_builder, cache_manager)
    )

    logger.info("Discovery and Search System started successfully")
    logger.info("=" * 60)
    logger.info("Discovery API available at http://localhost:8001/discovery")
    logger.info("Docs available at http://localhost:8001/docs")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Shutting down Discovery and Search System...")

    # Stop index publisher
    if index_publisher:
        await index_publisher.stop()

    # Cancel bundle processor
    bundle_processor_task.cancel()
    await asyncio.gather(bundle_processor_task, return_exceptions=True)

    # Close database
    await close_discovery_db()

    logger.info("Discovery and Search System shutdown complete")


async def _bundle_processor_loop(
    query_handler: QueryHandler,
    response_builder: ResponseBuilder,
    cache_manager: SpeculativeCacheManager,
):
    """
    Background loop for processing discovery bundles.

    Runs every 30 seconds.
    """
    logger.info("Starting bundle processor loop...")

    while True:
        try:
            await process_inbox_bundles(
                query_handler,
                response_builder,
                cache_manager,
            )
            await asyncio.sleep(30)  # Process every 30 seconds

        except asyncio.CancelledError:
            logger.info("Bundle processor loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in bundle processor loop: {e}", exc_info=True)
            await asyncio.sleep(60)  # Wait longer on error


# Create FastAPI app
app = FastAPI(
    title="Discovery and Search System",
    description="Distributed discovery and search for Solarpunk mesh network",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(discovery_router)


@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "service": "Discovery and Search System",
        "version": "1.0.0",
        "description": "Distributed discovery and search for Solarpunk mesh network",
        "docs": "/docs",
        "endpoints": {
            "discovery": "/discovery",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    global cache_manager, index_publisher

    cache_stats = await cache_manager.get_cache_stats() if cache_manager else {}

    return {
        "status": "healthy",
        "cache": {
            "total_indexes": cache_stats.get("total_indexes", 0),
            "unique_nodes": cache_stats.get("unique_nodes", 0),
            "usage_percent": cache_stats.get("usage_percent", 0),
        },
        "services": {
            "index_publisher": "running" if index_publisher else "stopped",
            "query_handler": "initialized" if query_handler else "not initialized",
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "discovery_search.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
