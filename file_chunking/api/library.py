"""
Library Cache API Endpoints

Manage library node cache.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services import LibraryCacheService, ChunkStorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/library", tags=["library"])


class CacheFileInfo(BaseModel):
    """Cached file information"""
    fileHash: str
    fileName: str
    fileSize: int
    mimeType: str
    accessCount: int
    priorityScore: float

    def model_dump(self, **kwargs):
        """Override to include both camelCase and snake_case keys"""
        data = super().model_dump(**kwargs)
        # Add snake_case aliases
        data["file_hash"] = data.get("fileHash")
        data["file_name"] = data.get("fileName")
        data["file_size"] = data.get("fileSize")
        data["mime_type"] = data.get("mimeType")
        data["access_count"] = data.get("accessCount")
        data["priority_score"] = data.get("priorityScore")
        return data


class CacheStats(BaseModel):
    """Library cache statistics"""
    totalFiles: int
    totalSizeBytes: int
    totalSizeMb: float
    totalSizeGb: float
    budgetBytes: int
    budgetGb: float
    usagePercentage: float
    isOverBudget: bool

    def model_dump(self, **kwargs):
        """Override to include both camelCase and snake_case keys"""
        data = super().model_dump(**kwargs)
        # Add snake_case aliases
        data["total_files"] = data.get("totalFiles")
        data["cached_files"] = data.get("totalFiles")  # Alias for test compatibility
        data["total_size_bytes"] = data.get("totalSizeBytes")
        data["cache_size_bytes"] = data.get("totalSizeBytes")  # Alias for test compatibility
        data["total_size_mb"] = data.get("totalSizeMb")
        data["total_size_gb"] = data.get("totalSizeGb")
        data["budget_bytes"] = data.get("budgetBytes")
        data["cache_budget_bytes"] = data.get("budgetBytes")  # Alias for test compatibility
        data["budget_gb"] = data.get("budgetGb")
        data["usage_percentage"] = data.get("usagePercentage")
        data["is_over_budget"] = data.get("isOverBudget")
        return data


@router.post("/cache/{file_hash}")
async def add_to_cache(file_hash: str, tags: str = ""):
    """
    Add a file to library cache.

    Args:
        file_hash: Hash of file to cache
        tags: Comma-separated tags

    Returns:
        Success message
    """
    try:
        chunk_storage = ChunkStorageService()
        library_cache = LibraryCacheService(chunk_storage)

        tag_list = [t.strip() for t in tags.split(",")] if tags else None

        success, error = await library_cache.add_to_cache(file_hash, tag_list)

        if not success:
            raise HTTPException(status_code=400, detail=error)

        return {"message": f"File {file_hash} added to cache"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add to cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache", response_model=List[CacheFileInfo])
async def list_cached_files(limit: int = 100):
    """
    List cached files.

    Args:
        limit: Maximum number of files to return

    Returns:
        List of CacheFileInfo
    """
    try:
        chunk_storage = ChunkStorageService()
        library_cache = LibraryCacheService(chunk_storage)

        cached_files = await library_cache.get_cached_files(limit)

        file_infos = []

        for cached_file in cached_files:
            file_infos.append(CacheFileInfo(
                fileHash=cached_file['file_hash'],
                fileName=cached_file['file_name'],
                fileSize=cached_file['file_size'],
                mimeType=cached_file['mime_type'],
                accessCount=cached_file['access_count'],
                priorityScore=cached_file['priority_score']
            ))

        return file_infos

    except Exception as e:
        logger.error(f"Failed to list cached files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=CacheStats)
async def get_cache_stats():
    """
    Get library cache statistics.

    Returns:
        CacheStats
    """
    try:
        chunk_storage = ChunkStorageService()
        library_cache = LibraryCacheService(chunk_storage)

        stats = await library_cache.get_cache_stats()

        return CacheStats(
            totalFiles=stats['total_files'],
            totalSizeBytes=stats['total_size_bytes'],
            totalSizeMb=stats['total_size_mb'],
            totalSizeGb=stats['total_size_gb'],
            budgetBytes=stats['budget_bytes'],
            budgetGb=stats['budget_gb'],
            usagePercentage=stats['usage_percentage'],
            isOverBudget=stats['is_over_budget']
        )

    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish")
async def publish_cached_files():
    """
    Pre-publish all cached files as DTN bundles.

    This makes cached content immediately available to the network.

    Returns:
        Number of files published
    """
    try:
        from app.services import CryptoService, BundleService

        crypto_service = CryptoService()
        bundle_service = BundleService(crypto_service)
        chunk_storage = ChunkStorageService()

        from ..services import ChunkPublisherService

        chunk_publisher = ChunkPublisherService(bundle_service, chunk_storage)
        library_cache = LibraryCacheService(chunk_storage, chunk_publisher)

        published_count = await library_cache.pre_publish_cached_files()

        return {
            "message": f"Published {published_count} cached files",
            "publishedCount": published_count
        }

    except Exception as e:
        logger.error(f"Failed to publish cached files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
