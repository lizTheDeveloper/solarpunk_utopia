"""
VF Bundle Publisher

Converts VF objects to/from DTN bundles for mesh network sync.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import json
import hashlib
import base64
import os
import logging

from ..models.vf.resource_spec import ResourceCategory

logger = logging.getLogger(__name__)


class VFBundlePublisher:
    """
    Publishes VF objects as DTN bundles and deserializes received bundles.

    Integrates with DTN Bundle System (see dtn-bundle-system proposal).
    """

    # Default TTL values per object type (hours)
    DEFAULT_TTL = {
        "Listing": {
            "food": 48,         # Perishable food offers
            "tools": 720,       # 30 days
            "skills": 2160,     # 90 days
            "default": 168,     # 7 days
        },
        "Match": 72,           # 3 days
        "Exchange": 168,       # 7 days until scheduled date
        "Event": 8760,         # 1 year (audit trail)
        "Process": 720,        # 30 days
        "Plan": 2160,          # 90 days
        "Protocol": 8760,      # 1 year
        "Lesson": 8760,        # 1 year
        "Agent": 8760,         # 1 year
        "Location": 8760,      # 1 year
        "ResourceSpec": 8760,  # 1 year
        "ResourceInstance": 720,  # 30 days
        "Commitment": 168,     # 7 days
    }

    def __init__(self, dtn_outbox_path: Optional[str] = None):
        """
        Initialize bundle publisher.

        Args:
            dtn_outbox_path: Path to DTN outbox directory. If not provided, reads from DTN_OUTBOX_PATH env var.
        """
        if dtn_outbox_path is None:
            dtn_outbox_path = os.getenv('DTN_OUTBOX_PATH')
        self.dtn_outbox_path = dtn_outbox_path

    def vf_object_to_bundle(self, vf_object, object_type: str) -> dict:
        """
        Convert VF object to DTN bundle format.

        Args:
            vf_object: Any VF object
            object_type: Type name (e.g., "Listing", "Event")

        Returns:
            DTN bundle dictionary
        """
        # Serialize object to dict
        payload = vf_object.to_dict()

        # Determine TTL based on object type and content
        ttl_hours = self._determine_ttl(vf_object, object_type)
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=ttl_hours)

        # Determine priority
        priority = self._determine_priority(vf_object, object_type)

        # Determine audience and tags
        audience, tags = self._determine_audience_and_tags(vf_object, object_type)

        # Generate bundle ID
        bundle_id = self._generate_bundle_id(payload)

        # Create bundle
        bundle = {
            "bundleId": bundle_id,
            "createdAt": created_at.isoformat(),
            "expiresAt": expires_at.isoformat(),
            "priority": priority,
            "audience": audience,
            "topic": self._determine_topic(object_type),
            "tags": tags,
            "payloadType": f"vf:{object_type}",
            "payload": payload,
            "hopLimit": 20,
            "receiptPolicy": "none",
            "signature": vf_object.signature
        }

        return bundle

    def bundle_to_vf_object(self, bundle: dict):
        """
        Deserialize DTN bundle to VF object.

        Args:
            bundle: DTN bundle dictionary

        Returns:
            VF object instance
        """
        payload_type = bundle.get("payloadType", "")
        if not payload_type.startswith("vf:"):
            raise ValueError(f"Not a VF bundle: {payload_type}")

        object_type = payload_type.split(":")[1]
        payload = bundle["payload"]

        # Import and deserialize based on type
        model_class = self._get_model_class(object_type)
        vf_object = model_class.from_dict(payload)

        return vf_object

    def publish_bundle(self, bundle: dict) -> bool:
        """
        Publish bundle to DTN outbox.

        Args:
            bundle: DTN bundle dictionary

        Returns:
            True if published successfully
        """
        if not self.dtn_outbox_path:
            logger.debug(f"[VF Bundle] Would publish: {bundle['bundleId']} (no outbox configured)")
            return False

        try:
            # Ensure outbox directory exists
            os.makedirs(self.dtn_outbox_path, exist_ok=True)

            # Generate filename from bundle ID (remove problematic characters)
            bundle_id_safe = bundle['bundleId'].replace(':', '_').replace('/', '_')
            filename = f"{bundle_id_safe}.json"
            filepath = os.path.join(self.dtn_outbox_path, filename)

            # Write bundle to outbox directory
            with open(filepath, 'w') as f:
                json.dump(bundle, f, indent=2)

            logger.info(f"[VF Bundle] Published: {bundle['bundleId']} type={bundle['payloadType']} -> {filepath}")
            return True

        except Exception as e:
            logger.error(f"[VF Bundle] Failed to publish {bundle['bundleId']}: {e}")
            return False

    def publish_vf_object(self, vf_object, object_type: str) -> dict:
        """
        Convert VF object to bundle and publish.

        Args:
            vf_object: VF object to publish
            object_type: Type name

        Returns:
            Published bundle
        """
        bundle = self.vf_object_to_bundle(vf_object, object_type)
        self.publish_bundle(bundle)
        return bundle

    def _determine_ttl(self, vf_object, object_type: str) -> int:
        """Determine TTL in hours based on object type and content"""
        if object_type == "Listing":
            # Check category for food (perishable)
            if hasattr(vf_object, 'resource_spec_id'):
                # In production, look up resource spec category
                # For now, use default
                return self.DEFAULT_TTL["Listing"]["default"]
            return self.DEFAULT_TTL["Listing"]["default"]

        return self.DEFAULT_TTL.get(object_type, 168)  # 7 days default

    def _determine_priority(self, vf_object, object_type: str) -> str:
        """Determine bundle priority"""
        # Emergency/perishable food gets high priority
        if object_type == "Listing":
            if hasattr(vf_object, 'available_until'):
                if vf_object.available_until:
                    # Handle both timezone-aware and timezone-naive datetimes
                    now = datetime.now(timezone.utc) if vf_object.available_until.tzinfo else datetime.now()
                    hours_left = (vf_object.available_until - now).total_seconds() / 3600
                    if hours_left < 24:
                        return "perishable"

        return "normal"

    def _determine_audience_and_tags(self, vf_object, object_type: str) -> tuple:
        """Determine audience and tags"""
        audience = "local"  # Default: local commune only
        tags = []

        if object_type == "Listing":
            tags.append(vf_object.listing_type.value)  # "offer" or "need"
            # Add category tag if we can determine it
            tags.append("mutual-aid")

        elif object_type in ["Event", "Exchange"]:
            tags.append("coordination")

        return audience, tags

    def _determine_topic(self, object_type: str) -> str:
        """Determine bundle topic"""
        if object_type in ["Listing", "Match", "Exchange"]:
            return "mutual-aid"
        elif object_type in ["Event", "Process", "Plan"]:
            return "production"
        elif object_type in ["Protocol", "Lesson"]:
            return "knowledge"
        else:
            return "vf-sync"

    def _generate_bundle_id(self, payload: dict) -> str:
        """Generate deterministic bundle ID from payload"""
        payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        hash_obj = hashlib.sha256(payload_json.encode('utf-8'))
        hash_b64 = base64.b64encode(hash_obj.digest()).decode('utf-8')
        return f"b:sha256:{hash_b64}"

    def _get_model_class(self, object_type: str):
        """Get model class by type name"""
        from ..models import vf

        class_map = {
            "Agent": vf.Agent,
            "Location": vf.Location,
            "ResourceSpec": vf.ResourceSpec,
            "ResourceInstance": vf.ResourceInstance,
            "Listing": vf.Listing,
            "Match": vf.Match,
            "Exchange": vf.Exchange,
            "Event": vf.Event,
            "Process": vf.Process,
            "Commitment": vf.Commitment,
            "Plan": vf.Plan,
            "Protocol": vf.Protocol,
            "Lesson": vf.Lesson,
        }

        return class_map.get(object_type)
