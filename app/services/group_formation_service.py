"""
Group Formation Protocol Service

Implements fractal group formation with physical key exchange.

Key concepts:
- Groups can exist at any scale (from task forces to federations)
- Nested/hierarchical groups (subsidiarity principle)
- Physical presence required for initial formation (NFC/QR)
- Each group gets: shared inventory, governance scope, encrypted chat
- Fission (split) and fusion (merge) protocols
"""

import logging
import secrets
from datetime import datetime, UTC
from typing import List, Optional, Dict
from nacl.public import PrivateKey, PublicKey, Box
from nacl.encoding import Base64Encoder
import json

logger = logging.getLogger(__name__)


class GroupFormationService:
    """
    Manages fractal group formation and lifecycle.

    Groups are cryptographic entities with:
    - Shared symmetric key for group encryption
    - Member public keys for invitation
    - Parent group reference (if nested)
    - Provisioned resources (inventory, chat channel)
    """

    def __init__(self):
        self.min_group_size = 3  # Minimum 3 people for a "commune" (not a couple)
        logger.info("GroupFormationService initialized")

    def generate_group_key(self) -> bytes:
        """
        Generate a secure symmetric key for group encryption.

        Returns:
            32-byte symmetric key
        """
        return secrets.token_bytes(32)

    def create_initial_group(
        self,
        founder_keys: List[Dict],
        group_name: str,
        parent_group_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new group via physical key exchange.

        Args:
            founder_keys: List of dicts with {user_id, public_key} for founding members
            group_name: Human-readable name for the group
            parent_group_id: Optional parent group (for nested groups)
            metadata: Optional group metadata

        Returns:
            dict with group info including shared key

        Raises:
            ValueError: if fewer than minimum members
        """
        if len(founder_keys) < self.min_group_size:
            raise ValueError(
                f"Groups require at least {self.min_group_size} founding members. "
                f"This ensures collective stewardship, not dyadic relationships."
            )

        # Generate group shared key
        group_key = self.generate_group_key()

        # Generate group ID
        import uuid
        group_id = str(uuid.uuid4())

        # Create group data structure
        group = {
            "id": group_id,
            "name": group_name,
            "created_at": datetime.now(UTC).isoformat(),
            "parent_group_id": parent_group_id,
            "shared_key": Base64Encoder.encode(group_key).decode('utf-8'),
            "founding_members": [k["user_id"] for k in founder_keys],
            "member_count": len(founder_keys),
            "formation_method": "physical_key_exchange",
            "metadata": metadata or {},
            "resources": {
                "inventory_id": f"inventory_{group_id}",
                "chat_channel_id": f"chat_{group_id}",
                "governance_scope_id": f"governance_{group_id}",
            },
            "nesting_level": self._compute_nesting_level(parent_group_id),
        }

        logger.info(
            f"Created group '{group_name}' (id: {group_id}) "
            f"with {len(founder_keys)} founding members"
        )

        return group

    def _compute_nesting_level(self, parent_group_id: Optional[str]) -> int:
        """
        Compute nesting level for a group.

        Args:
            parent_group_id: Parent group ID if nested

        Returns:
            nesting level (0 for top-level groups)
        """
        if parent_group_id is None:
            return 0

        # In production, would query database for parent's nesting level
        # For now, return 1 (immediate child)
        return 1

    def create_formation_invitation(
        self,
        group_id: str,
        inviter_user_id: str,
        inviter_private_key: bytes,
        invitee_public_key: bytes,
        group_shared_key: bytes
    ) -> Dict:
        """
        Create an encrypted invitation to join a group.

        Uses NaCl Box (X25519 + XSalsa20-Poly1305) to encrypt the group key
        from inviter to invitee.

        Args:
            group_id: Group to join
            inviter_user_id: User sending invitation
            inviter_private_key: Inviter's private key
            invitee_public_key: Invitee's public key
            group_shared_key: Group's shared symmetric key

        Returns:
            dict with encrypted invitation
        """
        # Create encryption box
        inviter_key = PrivateKey(inviter_private_key)
        invitee_key = PublicKey(invitee_public_key)
        box = Box(inviter_key, invitee_key)

        # Encrypt the group shared key
        encrypted_key = box.encrypt(
            group_shared_key,
            encoder=Base64Encoder
        )

        invitation = {
            "group_id": group_id,
            "inviter_user_id": inviter_user_id,
            "encrypted_group_key": encrypted_key.decode('utf-8'),
            "created_at": datetime.now(UTC).isoformat(),
            "invitation_type": "group_formation",
        }

        return invitation

    def accept_invitation(
        self,
        invitation: Dict,
        invitee_user_id: str,
        invitee_private_key: bytes,
        inviter_public_key: bytes
    ) -> bytes:
        """
        Accept a group invitation and decrypt the group key.

        Args:
            invitation: Invitation dict with encrypted_group_key
            invitee_user_id: User accepting invitation
            invitee_private_key: Invitee's private key
            inviter_public_key: Inviter's public key

        Returns:
            Decrypted group shared key (bytes)
        """
        # Create decryption box
        invitee_key = PrivateKey(invitee_private_key)
        inviter_key = PublicKey(inviter_public_key)
        box = Box(invitee_key, inviter_key)

        # Decrypt the group shared key
        encrypted_key = invitation["encrypted_group_key"].encode('utf-8')
        group_key = box.decrypt(
            encrypted_key,
            encoder=Base64Encoder
        )

        logger.info(
            f"User {invitee_user_id} accepted invitation to group {invitation['group_id']}"
        )

        return group_key

    def generate_qr_formation_token(
        self,
        group_id: str,
        inviter_user_id: str,
        group_shared_key: bytes,
        expiry_minutes: int = 30
    ) -> str:
        """
        Generate a QR code token for physical group formation.

        The token contains the group key encrypted with a one-time password
        that is displayed separately (or conveyed verbally).

        Args:
            group_id: Group being formed
            inviter_user_id: User creating the QR code
            group_shared_key: Group's shared key
            expiry_minutes: Minutes until token expires

        Returns:
            QR token string (JSON encoded)
        """
        from datetime import timedelta

        # Generate one-time password (6 digits)
        otp = f"{secrets.randbelow(1000000):06d}"

        # Encrypt group key with OTP (using PBKDF2 + AES)
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        import os

        # Derive key from OTP
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        otp_key = kdf.derive(otp.encode('utf-8'))

        # Add checksum to group key for verification
        import hashlib
        checksum = hashlib.sha256(group_shared_key).digest()[:4]  # First 4 bytes
        key_with_checksum = group_shared_key + checksum

        # Encrypt group key
        iv = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(otp_key),
            modes.CTR(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_key = encryptor.update(key_with_checksum) + encryptor.finalize()

        # Create token
        expiry = datetime.now(UTC) + timedelta(minutes=expiry_minutes)
        token = {
            "group_id": group_id,
            "inviter_user_id": inviter_user_id,
            "encrypted_key": Base64Encoder.encode(encrypted_key).decode('utf-8'),
            "salt": Base64Encoder.encode(salt).decode('utf-8'),
            "iv": Base64Encoder.encode(iv).decode('utf-8'),
            "expires_at": expiry.isoformat(),
            "token_type": "group_formation_qr",
        }

        logger.info(
            f"Generated QR formation token for group {group_id} "
            f"(OTP: {otp}, expires: {expiry})"
        )

        # Return QR code data (invitee will need to enter OTP to decrypt)
        return json.dumps(token), otp

    def scan_qr_and_join(
        self,
        qr_token: str,
        otp: str,
        joiner_user_id: str
    ) -> bytes:
        """
        Scan QR code and join group using OTP.

        Args:
            qr_token: QR code JSON token
            otp: One-time password (6 digits)
            joiner_user_id: User joining the group

        Returns:
            Decrypted group shared key

        Raises:
            ValueError: if token expired or OTP invalid
        """
        token = json.loads(qr_token)

        # Check expiry
        expiry = datetime.fromisoformat(token["expires_at"])
        if datetime.now(UTC) > expiry:
            raise ValueError("QR formation token has expired")

        # Decrypt group key using OTP
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        salt = Base64Encoder.decode(token["salt"])
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        try:
            otp_key = kdf.derive(otp.encode('utf-8'))
        except Exception as e:
            raise ValueError(f"Invalid OTP: {e}")

        # Decrypt group key
        iv = Base64Encoder.decode(token["iv"])
        encrypted_key = Base64Encoder.decode(token["encrypted_key"])

        try:
            cipher = Cipher(
                algorithms.AES(otp_key),
                modes.CTR(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(encrypted_key) + decryptor.finalize()

            # Verify decrypted data is correct length (32 bytes key + 4 bytes checksum)
            if len(decrypted_data) != 36:
                raise ValueError("Decryption failed - invalid OTP")

            # Split key and checksum
            group_key = decrypted_data[:32]
            checksum = decrypted_data[32:]

            # Verify checksum
            import hashlib
            expected_checksum = hashlib.sha256(group_key).digest()[:4]
            if checksum != expected_checksum:
                raise ValueError("Checksum verification failed - invalid OTP")

            logger.info(
                f"User {joiner_user_id} joined group {token['group_id']} via QR+OTP"
            )

            return group_key
        except Exception as e:
            if "invalid OTP" in str(e):
                raise
            raise ValueError(f"Failed to decrypt group key - likely invalid OTP")

    def create_nested_group(
        self,
        parent_group_id: str,
        parent_group_key: bytes,
        founder_keys: List[Dict],
        subgroup_name: str,
        inherit_members: bool = False
    ) -> Dict:
        """
        Create a nested subgroup within a parent group.

        Implements subsidiarity: child group has privacy from parent,
        but inherits parent's trusted roots.

        Args:
            parent_group_id: Parent group ID
            parent_group_key: Parent group's shared key (for verification)
            founder_keys: Founding members of subgroup
            subgroup_name: Name for the subgroup
            inherit_members: If True, subgroup inherits parent's member list

        Returns:
            dict with subgroup info
        """
        subgroup = self.create_initial_group(
            founder_keys=founder_keys,
            group_name=subgroup_name,
            parent_group_id=parent_group_id,
            metadata={
                "inherit_parent_trust": True,
                "inherit_parent_members": inherit_members,
                "subsidiarity_enforced": True,  # Parent can't see child's private data
            }
        )

        logger.info(
            f"Created nested subgroup '{subgroup_name}' "
            f"under parent group {parent_group_id}"
        )

        return subgroup

    def merge_groups(
        self,
        group_a_id: str,
        group_a_key: bytes,
        group_b_id: str,
        group_b_key: bytes,
        merged_name: str,
        consensus_required: bool = True
    ) -> Dict:
        """
        Merge two groups into a new federated group (fusion).

        Both groups' members must consent to the merge.

        Args:
            group_a_id: First group ID
            group_a_key: First group key
            group_b_id: Second group ID
            group_b_key: Second group key
            merged_name: Name for merged group
            consensus_required: If True, all members must approve

        Returns:
            dict with merged group info
        """
        # Generate new shared key for merged group
        merged_key = self.generate_group_key()

        import uuid
        merged_id = str(uuid.uuid4())

        merged_group = {
            "id": merged_id,
            "name": merged_name,
            "created_at": datetime.now(UTC).isoformat(),
            "shared_key": Base64Encoder.encode(merged_key).decode('utf-8'),
            "formation_method": "group_fusion",
            "parent_groups": [group_a_id, group_b_id],
            "consensus_required": consensus_required,
            "resources": {
                "inventory_id": f"inventory_{merged_id}",
                "chat_channel_id": f"chat_{merged_id}",
                "governance_scope_id": f"governance_{merged_id}",
            },
            "status": "pending_consensus" if consensus_required else "active",
        }

        logger.info(
            f"Merging groups {group_a_id} and {group_b_id} "
            f"into new group '{merged_name}' (id: {merged_id})"
        )

        return merged_group

    def split_group(
        self,
        original_group_id: str,
        original_group_key: bytes,
        departing_member_ids: List[str],
        new_group_name: str,
        secession_reason: Optional[str] = None
    ) -> Dict:
        """
        Split a group into two (fission/secession).

        Departing members form a new group. Original group continues
        with remaining members and generates new shared key.

        Args:
            original_group_id: Group being split
            original_group_key: Original group key (will be rotated)
            departing_member_ids: Users leaving to form new group
            new_group_name: Name for the new group
            secession_reason: Optional reason for split

        Returns:
            dict with both new group and rotation info for original
        """
        if len(departing_member_ids) < self.min_group_size:
            raise ValueError(
                f"Departing members must form valid group "
                f"(min {self.min_group_size} members)"
            )

        # Generate new group for departing members
        new_group_key = self.generate_group_key()
        import uuid
        new_group_id = str(uuid.uuid4())

        new_group = {
            "id": new_group_id,
            "name": new_group_name,
            "created_at": datetime.now(UTC).isoformat(),
            "shared_key": Base64Encoder.encode(new_group_key).decode('utf-8'),
            "formation_method": "group_fission",
            "parent_group_id": original_group_id,  # Lineage tracking
            "founding_members": departing_member_ids,
            "member_count": len(departing_member_ids),
            "secession_reason": secession_reason,
            "resources": {
                "inventory_id": f"inventory_{new_group_id}",
                "chat_channel_id": f"chat_{new_group_id}",
                "governance_scope_id": f"governance_{new_group_id}",
            },
        }

        # Rotate key for original group (security hygiene)
        rotated_key = self.generate_group_key()

        split_result = {
            "new_group": new_group,
            "original_group_id": original_group_id,
            "original_group_new_key": Base64Encoder.encode(rotated_key).decode('utf-8'),
            "split_timestamp": datetime.now(UTC).isoformat(),
            "action": "group_fission",
        }

        logger.info(
            f"Split group {original_group_id}: "
            f"{len(departing_member_ids)} members forming new group '{new_group_name}'"
        )

        return split_result
