"""
Cryptographic Signing Service

Signs and verifies VF objects using Ed25519.
"""

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from typing import Optional, Tuple
from pathlib import Path
import base64


class SigningService:
    """
    Service for signing and verifying VF objects.

    Uses Ed25519 for cryptographic signatures to ensure:
    - Authenticity (object created by claimed author)
    - Integrity (object hasn't been tampered with)
    """

    def __init__(self, keys_dir: Optional[Path] = None):
        """
        Initialize signing service with key storage directory.

        Args:
            keys_dir: Directory to store keypair (defaults to app/data/keys)
        """
        if keys_dir is None:
            keys_dir = Path(__file__).parent.parent / "data" / "keys"

        self.keys_dir = keys_dir
        self.keys_dir.mkdir(parents=True, exist_ok=True)

        self.private_key_path = self.keys_dir / "vf_node_private.pem"
        self.public_key_path = self.keys_dir / "vf_node_public.pem"

        # Load or generate keypair
        self.private_key, self.public_key = self._load_or_generate_keypair()

    def _load_or_generate_keypair(self) -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
        """Load existing keypair or generate new one"""
        if self.private_key_path.exists() and self.public_key_path.exists():
            return self._load_keypair()
        else:
            return self._generate_keypair()

    def _generate_keypair(self) -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
        """Generate new Ed25519 keypair and save to disk"""
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Save private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        self.private_key_path.write_bytes(private_pem)

        # Save public key
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.public_key_path.write_bytes(public_pem)

        # Set restrictive permissions (owner-only for private key)
        self.private_key_path.chmod(0o600)
        self.public_key_path.chmod(0o644)

        return private_key, public_key

    def _load_keypair(self) -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
        """Load keypair from disk"""
        private_pem = self.private_key_path.read_bytes()
        private_key = serialization.load_pem_private_key(
            private_pem,
            password=None
        )

        public_pem = self.public_key_path.read_bytes()
        public_key = serialization.load_pem_public_key(public_pem)

        return private_key, public_key

    def sign_object(self, vf_object) -> str:
        """
        Sign a VF object.

        Args:
            vf_object: Any VF object with canonical_json() method

        Returns:
            Base64-encoded signature
        """
        # Get canonical JSON (excludes signature field)
        canonical_json = vf_object.canonical_json()

        # Sign with Ed25519
        signature_bytes = self.private_key.sign(canonical_json.encode('utf-8'))
        return base64.b64encode(signature_bytes).decode('utf-8')

    @staticmethod
    def verify_signature(vf_object, public_key_pem: str) -> bool:
        """
        Verify signature on a VF object.

        Args:
            vf_object: VF object with signature
            public_key_pem: Ed25519 public key (PEM format)

        Returns:
            True if signature is valid
        """
        if not vf_object.signature:
            return False

        try:
            # Load public key from PEM
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8')
            )

            # Get canonical JSON
            canonical_json = vf_object.canonical_json()

            # Decode signature
            signature_bytes = base64.b64decode(vf_object.signature)

            # Verify signature
            public_key.verify(signature_bytes, canonical_json.encode('utf-8'))
            return True

        except (InvalidSignature, Exception):
            return False

    def sign_and_update(self, vf_object, author_id: Optional[str] = None):
        """
        Sign object and update author/signature fields.

        Args:
            vf_object: VF object to sign
            author_id: Public key fingerprint of author (defaults to this node's fingerprint)

        Returns:
            Updated object
        """
        if author_id is None:
            author_id = self.get_public_key_fingerprint()

        vf_object.author = author_id
        vf_object.signature = self.sign_object(vf_object)
        return vf_object

    def get_public_key_pem(self) -> str:
        """Get node's public key as PEM string"""
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return public_pem.decode('utf-8')

    def get_public_key_fingerprint(self) -> str:
        """Get a short fingerprint of the public key for display"""
        pem = self.get_public_key_pem()
        import hashlib
        fingerprint = hashlib.sha256(pem.encode('utf-8')).hexdigest()[:16]
        return fingerprint

    @staticmethod
    def generate_keypair() -> dict:
        """
        Generate a new Ed25519 keypair (for testing or external use).

        Returns:
            Dict with 'private_key' and 'public_key' (PEM encoded)
        """
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return {
            'private_key': private_pem.decode('utf-8'),
            'public_key': public_pem.decode('utf-8')
        }
