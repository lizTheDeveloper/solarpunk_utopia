"""Security Status Models - GAP-66

Plain-language security status for users.
Anti crypto-priesthood: explain what's protected and what isn't.
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class SecurityStatus(BaseModel):
    """User's current security status in plain English."""
    user_id: str

    # Messages
    messages_encrypted: bool = Field(
        default=True,
        description="Plain: Messages are encrypted - only recipients can read"
    )
    encryption_algorithm: str = Field(
        default="X25519 + XSalsa20-Poly1305",
        description="Technical: Same as Signal messenger"
    )

    # Identity
    identity_verified: bool = Field(
        default=True,
        description="Plain: Your posts are signed - no one can fake them"
    )
    signature_algorithm: str = Field(
        default="Ed25519",
        description="Technical: Mathematically unforgeable"
    )

    # Backup
    has_backup: bool = Field(
        default=False,
        description="Plain: Not backed up - if you lose phone, you lose access"
    )
    backup_method: Optional[str] = Field(
        default=None,
        description="seed_phrase or none"
    )

    # Security level
    security_level: Literal["basic", "high", "maximum"] = Field(
        default="basic",
        description="Plain: How much security is enabled"
    )

    # Warnings
    warnings: List[str] = Field(
        default_factory=list,
        description="Things user should know"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "alice-pk",
                "messages_encrypted": True,
                "encryption_algorithm": "X25519 + XSalsa20-Poly1305",
                "identity_verified": True,
                "signature_algorithm": "Ed25519",
                "has_backup": False,
                "backup_method": None,
                "security_level": "basic",
                "warnings": [
                    "No backup: If you lose your phone, you lose access"
                ]
            }
        }


class SecurityExplanation(BaseModel):
    """Plain-English explanation of a security feature."""
    feature: str
    simple_explanation: str = Field(description="What a 15-year-old can understand")
    metaphor: Optional[str] = Field(default=None, description="Helpful comparison")
    technical_details: Optional[str] = Field(default=None, description="For those who want details")
    limitations: List[str] = Field(default_factory=list, description="What this DOESN'T protect")


class SecuritySetting(BaseModel):
    """Security setting that user can control."""
    setting_name: str
    current_value: str
    options: List[dict]
    plain_explanation: str
    recommended: Optional[str] = None


class SecurityLevel(BaseModel):
    """Security level configuration."""
    level: Literal["basic", "high", "maximum"]
    features: List[str] = Field(description="What's enabled at this level")
    good_for: str = Field(description="Who should use this level")


# Predefined security levels
SECURITY_LEVELS = {
    "basic": SecurityLevel(
        level="basic",
        features=[
            "Messages encrypted",
            "Identity signed"
        ],
        good_for="Most users"
    ),
    "high": SecurityLevel(
        level="high",
        features=[
            "Messages encrypted",
            "Identity signed",
            "Require PIN for app unlock",
            "Auto-lock after 5 minutes"
        ],
        good_for="Anyone who shares their phone"
    ),
    "maximum": SecurityLevel(
        level="maximum",
        features=[
            "Messages encrypted",
            "Identity signed",
            "Require PIN for app unlock",
            "Duress PIN (opens decoy app)",
            "Panic wipe (5 taps on logo)",
            "Auto-delete old messages"
        ],
        good_for="High-risk situations"
    )
}


# Security explanations (plain English)
SECURITY_EXPLANATIONS = {
    "encryption": SecurityExplanation(
        feature="Message Encryption",
        simple_explanation="When you send a message, it goes in a locked box. Only the recipient has the key. Even we can't read it.",
        metaphor="Like passing a locked box. Only your friend has the key.",
        technical_details="X25519 key exchange with XSalsa20-Poly1305 AEAD. Same encryption as Signal messenger. Provides forward secrecy and authenticated encryption.",
        limitations=[
            "If someone steals your unlocked phone, they have your keys",
            "Metadata (who talks to who, when) is visible to phone carriers"
        ]
    ),
    "signatures": SecurityExplanation(
        feature="Digital Signatures",
        simple_explanation="When you post an offer, it has your digital signature. No one can fake it. No one can change it. If someone tries to edit your offer, the seal breaks.",
        metaphor="Like a wax seal on a letter. If anyone opens it, the seal breaks.",
        technical_details="Ed25519 signatures. Provides existential unforgeability. Mathematicians have proven that without your secret key, creating a valid signature is impossible.",
        limitations=[
            "If you share your password, anyone can impersonate you",
            "If someone gets your seed phrase, they can sign as you"
        ]
    ),
    "mesh_sync": SecurityExplanation(
        feature="Mesh Networking",
        simple_explanation="Messages hop phone-to-phone until they reach you. Like kids passing notes in class. Works even when internet is down.",
        metaphor="Like passing notes in class. Your message hops from person to person.",
        technical_details="DTN (Delay-Tolerant Networking) with store-and-forward bundles. Messages are encrypted end-to-end and signed at each hop.",
        limitations=[
            "Phone carriers can see you're using the app",
            "They can see approximate message sizes and timing"
        ]
    ),
    "web_of_trust": SecurityExplanation(
        feature="Web of Trust",
        simple_explanation="You vouch for people you know in real life. They vouch for people they know. If you're 3+ friend-hops from someone, you probably don't trust them.",
        metaphor="Friend-of-friend verification. Your trust degrades with distance.",
        technical_details="Decentralized Web of Trust with 0.8 attenuation per hop. Trust = previous_trust × 0.8. Prevents Sybil attacks while allowing growth.",
        limitations=[
            "If someone tricks you into vouching, their fake friends get some trust",
            "You need to know people in real life to join"
        ]
    )
}
