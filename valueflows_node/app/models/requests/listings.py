"""
Pydantic Validation Models for Listings API

GAP-43: Input Validation
Replaces raw dict parameters with validated Pydantic models.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class ListingType(str, Enum):
    """Type of listing - must match existing enum"""
    OFFER = "offer"
    NEED = "need"


class ListingStatus(str, Enum):
    """Listing status"""
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ListingCreate(BaseModel):
    """
    Request model for creating a new listing.

    Validates:
    - Required fields present
    - Field types correct
    - String lengths reasonable
    - Numeric ranges valid
    - Enum values correct
    """

    # Required fields
    listing_type: ListingType
    resource_spec_id: str = Field(..., min_length=1, max_length=200)
    agent_id: str = Field(..., min_length=1, max_length=200)

    # Quantity and unit
    quantity: float = Field(default=1.0, gt=0, le=1000000)
    unit: str = Field(default="items", max_length=50)

    # Optional location
    location_id: Optional[str] = Field(None, max_length=200)

    # Optional time constraints
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None

    # Optional descriptive fields
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=500)

    # Status (defaults to active)
    status: ListingStatus = ListingStatus.ACTIVE

    # Optional resource instance reference
    resource_instance_id: Optional[str] = Field(None, max_length=200)

    @field_validator('resource_spec_id')
    @classmethod
    def validate_resource_spec_id(cls, v: str) -> str:
        """Validate resource spec ID format"""
        if not v or len(v.strip()) == 0:
            raise ValueError("resource_spec_id cannot be empty")
        # TODO (GAP-43 Phase 3): Add database validation
        # if not await resource_spec_exists(v):
        #     raise ValueError(f"Resource specification {v} not found")
        return v.strip()

    @field_validator('agent_id')
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        """Validate agent ID format"""
        if not v or len(v.strip()) == 0:
            raise ValueError("agent_id cannot be empty")
        # TODO (GAP-43 Phase 3): Add database validation
        # if not await agent_exists(v):
        #     raise ValueError(f"Agent {v} not found")
        return v.strip()

    @field_validator('available_until')
    @classmethod
    def validate_available_until_after_from(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Ensure available_until is after available_from"""
        if v and 'available_from' in info.data and info.data['available_from']:
            if v <= info.data['available_from']:
                raise ValueError("available_until must be after available_from")
        return v

    @field_validator('image_url')
    @classmethod
    def validate_image_url(cls, v: Optional[str]) -> Optional[str]:
        """Basic URL validation"""
        if v and not v.startswith(('http://', 'https://', 'ipfs://')):
            raise ValueError("image_url must be a valid URL")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "listing_type": "offer",
                "resource_spec_id": "resource_spec:tomatoes",
                "agent_id": "agent:alice",
                "quantity": 5.0,
                "unit": "lbs",
                "title": "Fresh heirloom tomatoes",
                "description": "From my garden, ready to pick",
                "location_id": "location:community_garden",
                "available_from": "2025-12-20T10:00:00",
                "available_until": "2025-12-22T18:00:00"
            }
        }


class ListingUpdate(BaseModel):
    """
    Request model for updating an existing listing.

    All fields optional - only provided fields are updated.
    """

    quantity: Optional[float] = Field(None, gt=0, le=1000000)
    unit: Optional[str] = Field(None, max_length=50)
    location_id: Optional[str] = Field(None, max_length=200)
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=500)
    status: Optional[ListingStatus] = None

    @field_validator('image_url')
    @classmethod
    def validate_image_url(cls, v: Optional[str]) -> Optional[str]:
        """Basic URL validation"""
        if v and not v.startswith(('http://', 'https://', 'ipfs://')):
            raise ValueError("image_url must be a valid URL")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "status": "fulfilled",
                "description": "All gone! Thanks everyone!"
            }
        }


class ListingQuery(BaseModel):
    """
    Query parameters for browsing listings.

    Validates search/filter parameters.
    """

    listing_type: Optional[ListingType] = None
    category: Optional[str] = Field(None, max_length=50)
    location_id: Optional[str] = Field(None, max_length=200)
    status: ListingStatus = Field(default=ListingStatus.ACTIVE)
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

    @field_validator('category')
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Validate category format (prevent injection)"""
        if v:
            # Remove potentially dangerous characters
            forbidden = ['<', '>', '&', '"', "'", '\\', '/']
            if any(char in v for char in forbidden):
                raise ValueError("Invalid characters in category")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "listing_type": "offer",
                "category": "food",
                "status": "active",
                "limit": 50
            }
        }
