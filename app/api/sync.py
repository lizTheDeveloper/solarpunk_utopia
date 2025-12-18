from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

from ..models import Bundle, Priority, QueueName
from ..services import BundleService, CryptoService, ForwardingService, CacheService
from ..database import QueueManager

router = APIRouter(prefix="/sync", tags=["sync"])


class BundleIndex(BaseModel):
    """Lightweight bundle index for sync negotiation"""
    bundleId: str
    priority: Priority
    createdAt: str
    expiresAt: str
    sizeBytes: int


class SyncRequest(BaseModel):
    """Request for syncing bundles with a peer"""
    peer_id: str
    max_bundles: int = 100
    peer_trust_score: float = 0.5
    peer_is_local: bool = True


class SyncResponse(BaseModel):
    """Response containing bundles to sync"""
    bundles: List[Bundle]
    total_count: int


# Dependency injection
def get_crypto_service() -> CryptoService:
    return CryptoService()

def get_bundle_service(crypto: CryptoService = Depends(get_crypto_service)) -> BundleService:
    return BundleService(crypto)

def get_forwarding_service() -> ForwardingService:
    return ForwardingService()

def get_cache_service() -> CacheService:
    return CacheService()


@router.get("/index", response_model=List[BundleIndex])
async def get_bundle_index(
    queue: QueueName = QueueName.PENDING,
    limit: int = 1000
):
    """
    Get lightweight index of available bundles for sync negotiation.

    This endpoint is used by peers to discover what bundles are available
    without transferring full bundle data.

    Query parameters:
    - queue: Which queue to index (default: pending)
    - limit: Maximum number of bundles to include (default: 1000)
    """
    try:
        bundles = await QueueManager.list_queue(queue, limit=limit)

        # Convert to lightweight index
        index = []
        for bundle in bundles:
            index.append(BundleIndex(
                bundleId=bundle.bundleId,
                priority=bundle.priority,
                createdAt=bundle.createdAt.isoformat(),
                expiresAt=bundle.expiresAt.isoformat(),
                sizeBytes=len(str(bundle.payload))  # Approximate
            ))

        return index

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get index: {str(e)}")


@router.post("/request", response_model=SyncResponse)
async def request_bundles(
    bundle_ids: List[str],
    forwarding_service: ForwardingService = Depends(get_forwarding_service),
    peer_trust_score: float = 0.5,
    peer_is_local: bool = True
):
    """
    Request specific bundles by ID.

    This endpoint is called by a peer after reviewing the bundle index.
    Only bundles that pass audience enforcement will be returned.

    Request body:
    - bundle_ids: List of bundle IDs to request

    Query parameters:
    - peer_trust_score: Trust score of requesting peer
    - peer_is_local: Whether peer is in local community
    """
    try:
        bundles_to_send = []

        for bundle_id in bundle_ids:
            bundle = await QueueManager.get_bundle(bundle_id)
            if not bundle:
                continue

            # Check if we can forward this bundle to the peer
            can_forward, reason = forwarding_service.can_forward_to_peer(
                bundle,
                peer_trust_score,
                peer_is_local
            )

            if can_forward:
                bundles_to_send.append(bundle)

        return SyncResponse(
            bundles=bundles_to_send,
            total_count=len(bundles_to_send)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to request bundles: {str(e)}")


@router.post("/push", response_model=dict)
async def push_bundles(
    bundles: List[Bundle],
    service: BundleService = Depends(get_bundle_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """
    Receive multiple bundles pushed by a peer during sync.

    Each bundle will be validated and added to inbox if valid.
    Invalid bundles go to quarantine.

    This is a batch version of POST /bundles/receive.
    """
    try:
        results = []
        accepted = 0
        rejected = 0

        for bundle in bundles:
            # Check cache budget before accepting
            bundle_size = len(str(bundle.payload))
            can_accept = await cache_service.can_accept_bundle(bundle_size)

            if not can_accept:
                results.append({
                    "bundle_id": bundle.bundleId,
                    "success": False,
                    "reason": "Cache budget exceeded"
                })
                rejected += 1
                continue

            # Receive bundle
            success, message = await service.receive_bundle(bundle)
            results.append({
                "bundle_id": bundle.bundleId,
                "success": success,
                "reason": message
            })

            if success:
                accepted += 1
            else:
                rejected += 1

        return {
            "total_received": len(bundles),
            "accepted": accepted,
            "rejected": rejected,
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to push bundles: {str(e)}")


@router.get("/pull", response_model=SyncResponse)
async def pull_bundles(
    max_bundles: int = 100,
    peer_trust_score: float = 0.5,
    peer_is_local: bool = True,
    forwarding_service: ForwardingService = Depends(get_forwarding_service)
):
    """
    Pull bundles ready for forwarding to a peer.

    This is a convenience endpoint that combines getting the forwarding queue
    and filtering by audience enforcement.

    Query parameters:
    - max_bundles: Maximum number of bundles to return (default: 100)
    - peer_trust_score: Trust score of requesting peer (default: 0.5)
    - peer_is_local: Whether peer is in local community (default: true)

    Returns bundles ordered by priority (emergency first).
    """
    try:
        # Get bundles ready for forwarding
        candidates = await forwarding_service.get_bundles_for_forwarding(max_bundles)

        # Filter by audience enforcement
        bundles_to_send = []
        for bundle in candidates:
            can_forward, reason = forwarding_service.can_forward_to_peer(
                bundle,
                peer_trust_score,
                peer_is_local
            )

            if can_forward:
                bundles_to_send.append(bundle)

        return SyncResponse(
            bundles=bundles_to_send,
            total_count=len(bundles_to_send)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pull bundles: {str(e)}")


@router.get("/stats", response_model=dict)
async def get_sync_stats(
    cache_service: CacheService = Depends(get_cache_service),
    forwarding_service: ForwardingService = Depends(get_forwarding_service)
):
    """
    Get comprehensive sync statistics.

    Includes:
    - Cache usage and budget
    - Queue counts
    - Forwarding queue breakdown by priority
    """
    try:
        cache_stats = await cache_service.get_cache_stats()
        forwarding_stats = await forwarding_service.get_forwarding_stats()

        return {
            "cache": cache_stats,
            "forwarding": forwarding_stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
