"""Exchanges API Endpoints"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid

from ...models.vf.exchange import Exchange
from ...models.requests.vf_objects import ExchangeCreate
from ...database import get_database
from ...repositories.vf.exchange_repo import ExchangeRepository
from ...services.vf_bundle_publisher import VFBundlePublisher

router = APIRouter(prefix="/vf/exchanges", tags=["exchanges"])


@router.get("/", response_model=dict)
async def get_exchanges(status: str = None, agent_id: str = None):
    """Get all exchanges, optionally filtered by status or agent"""
    try:
        db = get_database()
        db.connect()
        exchange_repo = ExchangeRepository(db.conn)

        if agent_id:
            exchanges = exchange_repo.find_by_agent(agent_id) if hasattr(exchange_repo, 'find_by_agent') else []
        else:
            exchanges = exchange_repo.find_all()
            # Filter by status if provided
            if status:
                exchanges = [e for e in exchanges if e.status.value == status]

        db.close()

        return {
            "exchanges": [e.to_dict() for e in exchanges],
            "count": len(exchanges)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/", response_model=dict)
async def create_exchange(exchange_data: ExchangeCreate):
    """
    Create a new exchange (from accepted match).

    GAP-43: Now uses Pydantic validation model.

    Validates:
    - Required fields present (name)
    - Field types correct
    - String lengths reasonable
    """
    try:
        # Convert validated Pydantic model to dict
        data = exchange_data.model_dump()

        data["id"] = f"exchange:{uuid.uuid4()}"
        data["created_at"] = datetime.now().isoformat()

        exchange = Exchange.from_dict(data)

        db = get_database()
        db.connect()
        exchange_repo = ExchangeRepository(db.conn)
        created_exchange = exchange_repo.create(exchange)

        publisher = VFBundlePublisher()
        bundle = publisher.publish_vf_object(created_exchange, "Exchange")

        db.close()

        return {
            "status": "created",
            "exchange": created_exchange.to_dict(),
            "bundle_id": bundle["bundleId"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/upcoming", response_model=dict)
async def get_upcoming_exchanges(agent_id: str = None):
    """Get upcoming exchanges"""
    try:
        db = get_database()
        db.connect()
        exchange_repo = ExchangeRepository(db.conn)
        exchanges = exchange_repo.find_upcoming(agent_id=agent_id)
        db.close()

        return {
            "exchanges": [e.to_dict() for e in exchanges],
            "count": len(exchanges)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{exchange_id}/complete", response_model=dict)
async def complete_exchange(
    exchange_id: str,
    agent_id: str,
    event_id: str
):
    """
    Mark exchange as completed by one party.

    Note: Anti-Reputation Capitalism - we no longer track dollar values.
    The exchange is the celebration. The gift is the point.
    """
    try:
        db = get_database()
        db.connect()
        exchange_repo = ExchangeRepository(db.conn)

        exchange = exchange_repo.find_by_id(exchange_id)
        if not exchange:
            raise HTTPException(status_code=404, detail="Exchange not found")

        # Mark appropriate party as completed
        if exchange.provider_id == agent_id:
            exchange.provider_completed = True
            exchange.provider_event_id = event_id
        elif exchange.receiver_id == agent_id:
            exchange.receiver_completed = True
            exchange.receiver_event_id = event_id
        else:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Update status if both completed
        if exchange.is_completed():
            exchange.status = "completed"

        updated_exchange = exchange_repo.update(exchange)

        publisher = VFBundlePublisher()
        bundle = publisher.publish_vf_object(updated_exchange, "Exchange")

        db.close()

        return {
            "status": "updated",
            "exchange": updated_exchange.to_dict(),
            "fully_completed": updated_exchange.is_completed()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
