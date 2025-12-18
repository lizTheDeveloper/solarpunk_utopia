"""
Bridge Node API

FastAPI endpoints for bridge node management.
"""

from .bridge_api import router, initialize_services, shutdown_services

__all__ = ["router", "initialize_services", "shutdown_services"]
