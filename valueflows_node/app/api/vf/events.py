"""Events API Endpoints"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid

from ...models.vf.event import Event
from ...database import get_database
from ...repositories.vf.event_repo import EventRepository
from ...services.vf_bundle_publisher import VFBundlePublisher

router = APIRouter(prefix="/vf/events", tags=["events"])


@router.post("/", response_model=dict)
async def record_event(event_data: dict):
    """Record an economic event"""
    try:
        if "id" not in event_data:
            event_data["id"] = f"event:{uuid.uuid4()}"
        if "occurred_at" not in event_data:
            event_data["occurred_at"] = datetime.now().isoformat()
        event_data["created_at"] = datetime.now().isoformat()

        event = Event.from_dict(event_data)

        db = get_database()
        db.connect()
        event_repo = EventRepository(db.conn)
        created_event = event_repo.create(event)

        publisher = VFBundlePublisher()
        bundle = publisher.publish_vf_object(created_event, "Event")

        db.close()

        return {
            "status": "recorded",
            "event": created_event.to_dict(),
            "bundle_id": bundle["bundleId"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exchange/{exchange_id}", response_model=dict)
async def get_exchange_events(exchange_id: str):
    """Get all events for an exchange"""
    try:
        db = get_database()
        db.connect()
        event_repo = EventRepository(db.conn)
        events = event_repo.find_by_exchange(exchange_id)
        db.close()

        return {
            "events": [e.to_dict() for e in events],
            "count": len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/resource/{instance_id}/provenance", response_model=dict)
async def get_resource_provenance(instance_id: str):
    """Get provenance chain for a resource instance"""
    try:
        db = get_database()
        db.connect()
        event_repo = EventRepository(db.conn)
        events = event_repo.find_by_resource_instance(instance_id)
        db.close()

        return {
            "resource_instance_id": instance_id,
            "events": [e.to_dict() for e in events],
            "event_count": len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
