from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from ..models import Bundle, BundleCreate, QueueName
from ..services import BundleService, CryptoService, ForwardingService
from ..database import QueueManager

router = APIRouter(prefix="/bundles", tags=["bundles"])

# Dependency injection
def get_crypto_service() -> CryptoService:
    return CryptoService()

def get_bundle_service(crypto: CryptoService = Depends(get_crypto_service)) -> BundleService:
    return BundleService(crypto)

def get_forwarding_service() -> ForwardingService:
    return ForwardingService()


@router.post("", response_model=Bundle)
async def create_bundle(
    bundle_create: BundleCreate,
    service: BundleService = Depends(get_bundle_service)
):
    """
    Create a new bundle.

    The bundle will be signed with the node's private key and stored in the outbox queue.
    """
    try:
        bundle = await service.create_bundle(bundle_create)
        return bundle
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bundle: {str(e)}")


@router.get("", response_model=List[Bundle])
async def list_bundles(
    queue: QueueName = QueueName.INBOX,
    limit: int = 100,
    offset: int = 0,
    service: BundleService = Depends(get_bundle_service)
):
    """
    List bundles in a queue.

    Query parameters:
    - queue: Which queue to list (inbox, outbox, pending, delivered, expired, quarantine)
    - limit: Maximum number of bundles to return (default: 100)
    - offset: Offset for pagination (default: 0)
    """
    try:
        bundles = await service.list_bundles(queue, limit, offset)
        return bundles
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list bundles: {str(e)}")


@router.get("/{bundle_id}", response_model=Bundle)
async def get_bundle(
    bundle_id: str,
    service: BundleService = Depends(get_bundle_service)
):
    """Get a specific bundle by ID"""
    bundle = await service.get_bundle(bundle_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    return bundle


@router.post("/receive", response_model=dict)
async def receive_bundle(
    bundle: Bundle,
    service: BundleService = Depends(get_bundle_service)
):
    """
    Receive a bundle from a peer.

    The bundle will be validated:
    - Signature verification
    - TTL check
    - Hop limit check
    - Content-addressed ID verification

    Valid bundles go to inbox, invalid ones to quarantine.
    """
    try:
        success, message = await service.receive_bundle(bundle)
        return {
            "success": success,
            "message": message,
            "bundle_id": bundle.bundleId
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to receive bundle: {str(e)}")


@router.post("/{bundle_id}/forward", response_model=dict)
async def forward_bundle(
    bundle_id: str,
    peer_trust_score: float = 0.5,
    peer_is_local: bool = True,
    forwarding_service: ForwardingService = Depends(get_forwarding_service)
):
    """
    Check if a bundle can be forwarded to a peer.

    Query parameters:
    - peer_trust_score: Trust score of peer (0.0-1.0, default: 0.5)
    - peer_is_local: Whether peer is in local community (default: true)

    Returns whether the bundle can be forwarded and why.
    """
    # Get bundle
    bundle = await QueueManager.get_bundle(bundle_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")

    # Check if forwarding is allowed
    can_forward, reason = forwarding_service.can_forward_to_peer(
        bundle,
        peer_trust_score,
        peer_is_local
    )

    return {
        "can_forward": can_forward,
        "reason": reason,
        "bundle_id": bundle_id,
        "priority": bundle.priority.value,
        "audience": bundle.audience.value
    }


@router.post("/{bundle_id}/to-pending", response_model=dict)
async def move_to_pending(
    bundle_id: str,
    forwarding_service: ForwardingService = Depends(get_forwarding_service)
):
    """
    Move a bundle from outbox to pending queue.

    This marks the bundle as ready for opportunistic forwarding.
    """
    success = await forwarding_service.move_to_pending(bundle_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bundle not found in outbox")

    return {
        "success": True,
        "message": "Bundle moved to pending queue",
        "bundle_id": bundle_id
    }


@router.post("/{bundle_id}/mark-delivered", response_model=dict)
async def mark_delivered(
    bundle_id: str,
    forwarding_service: ForwardingService = Depends(get_forwarding_service)
):
    """
    Mark a bundle as delivered.

    This is called when a receipt acknowledgment is received.
    """
    success = await forwarding_service.mark_delivered(bundle_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bundle not found")

    return {
        "success": True,
        "message": "Bundle marked as delivered",
        "bundle_id": bundle_id
    }


@router.get("/stats/queues", response_model=dict)
async def get_queue_stats():
    """Get statistics about all queues"""
    stats = {}
    for queue in QueueName:
        count = await QueueManager.count_queue(queue)
        stats[queue.value] = count

    return {
        "queue_counts": stats
    }


@router.get("/stats/forwarding", response_model=dict)
async def get_forwarding_stats(
    forwarding_service: ForwardingService = Depends(get_forwarding_service)
):
    """Get statistics about forwarding queues"""
    stats = await forwarding_service.get_forwarding_stats()
    return stats
