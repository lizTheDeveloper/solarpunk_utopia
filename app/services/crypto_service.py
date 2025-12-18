from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
import base64
from pathlib import Path
from typing import Tuple


class CryptoService:
    """
    Ed25519 signing and verification service for DTN bundles.

    All bundles are cryptographically signed to ensure:
    - Authenticity (bundle created by claimed author)
    - Integrity (bundle hasn't been tampered with)
    """

    def __init__(self, keys_dir: Path = None):
        """Initialize crypto service with key storage directory"""
        if keys_dir is None:
            keys_dir = Path(__file__).parent.parent.parent / "data" / "keys"

        self.keys_dir = keys_dir
        self.keys_dir.mkdir(parents=True, exist_ok=True)

        self.private_key_path = self.keys_dir / "node_private.pem"
        self.public_key_path = self.keys_dir / "node_public.pem"

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

        # Set restrictive permissions (owner-only)
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

    def sign(self, data: str) -> str:
        """
        Sign data with node's private key.

        Args:
            data: String data to sign (typically canonical JSON)

        Returns:
            Base64-encoded signature string
        """
        signature = self.private_key.sign(data.encode('utf-8'))
        return base64.b64encode(signature).decode('utf-8')

    def verify(self, data: str, signature: str, public_key_pem: str) -> bool:
        """
        Verify signature against data using provided public key.

        Args:
            data: String data that was signed
            signature: Base64-encoded signature
            public_key_pem: PEM-encoded public key

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Decode signature
            signature_bytes = base64.b64decode(signature)

            # Load public key from PEM
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8')
            )

            # Verify signature
            public_key.verify(signature_bytes, data.encode('utf-8'))
            return True

        except (InvalidSignature, Exception):
            return False

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
