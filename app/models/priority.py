from enum import Enum


class Priority(str, Enum):
    """Bundle priority levels"""
    EMERGENCY = "emergency"
    PERISHABLE = "perishable"
    NORMAL = "normal"
    LOW = "low"


class Audience(str, Enum):
    """Bundle audience/visibility levels"""
    PUBLIC = "public"  # Anyone may carry
    LOCAL = "local"  # Only within community boundary
    TRUSTED = "trusted"  # Only nodes meeting trust threshold
    PRIVATE = "private"  # Encrypted direct delivery only


class ReceiptPolicy(str, Enum):
    """Receipt acknowledgment policy"""
    NONE = "none"
    REQUESTED = "requested"
    REQUIRED = "required"


class Topic(str, Enum):
    """Bundle topic categories"""
    MUTUAL_AID = "mutual-aid"
    KNOWLEDGE = "knowledge"
    COORDINATION = "coordination"
    INVENTORY = "inventory"
    EDUCATION = "education"
    TRUST = "trust"  # Trust revocations, burn notices, vouches
