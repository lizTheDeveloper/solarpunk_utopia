"""Real encryption utilities using NaCl and AES-256-GCM

This module provides actual cryptographic functions for:
- E2E message encryption (X25519 + XSalsa20-Poly1305)
- Seed phrase encryption (AES-256-GCM + Argon2)
- Secure key deletion
- BIP39 seed phrase to Ed25519 key derivation

Replaces placeholder Base64 "encryption" with real crypto.
"""
import os
import ctypes
import hashlib
from typing import Tuple
from nacl.public import PrivateKey, PublicKey, Box
from nacl.signing import SigningKey
from nacl.utils import random as nacl_random
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from mnemonic import Mnemonic


# ===== Message Encryption (X25519 + XSalsa20-Poly1305) =====

def encrypt_message(plaintext: str, recipient_pubkey: bytes, sender_privkey: bytes) -> bytes:
    """Encrypt message using NaCl box (X25519 + XSalsa20-Poly1305)

    Args:
        plaintext: Message to encrypt
        recipient_pubkey: Recipient's 32-byte X25519 public key
        sender_privkey: Sender's 32-byte X25519 private key

    Returns:
        Encrypted message (nonce + ciphertext)
    """
    sender_key = PrivateKey(sender_privkey)
    recipient_key = PublicKey(recipient_pubkey)
    box = Box(sender_key, recipient_key)

    # Encrypt with random nonce
    nonce = nacl_random(Box.NONCE_SIZE)
    encrypted = box.encrypt(plaintext.encode('utf-8'), nonce)

    return encrypted


def decrypt_message(ciphertext: bytes, sender_pubkey: bytes, recipient_privkey: bytes) -> str:
    """Decrypt message using NaCl box

    Args:
        ciphertext: Encrypted message (nonce + ciphertext)
        sender_pubkey: Sender's 32-byte X25519 public key
        recipient_privkey: Recipient's 32-byte X25519 private key

    Returns:
        Decrypted plaintext

    Raises:
        nacl.exceptions.CryptoError: If decryption fails (wrong keys, tampered ciphertext)
    """
    recipient_key = PrivateKey(recipient_privkey)
    sender_key = PublicKey(sender_pubkey)
    box = Box(recipient_key, sender_key)

    decrypted = box.decrypt(ciphertext)
    return decrypted.decode('utf-8')


# ===== Seed Phrase Encryption (AES-256-GCM + Scrypt) =====

def derive_key_scrypt(password: str, salt: bytes) -> bytes:
    """Derive 256-bit key from password using Scrypt

    Args:
        password: User password
        salt: 16-byte random salt

    Returns:
        32-byte derived key
    """
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,  # CPU/memory cost (16384)
        r=8,      # Block size
        p=1,      # Parallelization
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))


def encrypt_seed_phrase(seed_phrase: str, password: str) -> bytes:
    """Encrypt seed phrase with password-derived key using AES-256-GCM

    Args:
        seed_phrase: BIP39 seed phrase to encrypt
        password: User password

    Returns:
        salt (16 bytes) + nonce (12 bytes) + ciphertext + tag
    """
    # Generate random salt
    salt = os.urandom(16)

    # Derive key from password
    key = derive_key_scrypt(password, salt)

    # Encrypt with AES-256-GCM
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, seed_phrase.encode('utf-8'), None)

    # Return salt + nonce + ciphertext
    return salt + nonce + ciphertext


def decrypt_seed_phrase(encrypted: bytes, password: str) -> str:
    """Decrypt seed phrase with password

    Args:
        encrypted: salt (16) + nonce (12) + ciphertext + tag
        password: User password

    Returns:
        Decrypted seed phrase

    Raises:
        cryptography.exceptions.InvalidTag: If password is wrong or data tampered
    """
    # Extract components
    salt = encrypted[:16]
    nonce = encrypted[16:28]
    ciphertext = encrypted[28:]

    # Derive key
    key = derive_key_scrypt(password, salt)

    # Decrypt
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)

    return plaintext.decode('utf-8')


# ===== Secure Key Deletion =====

def secure_wipe_key(key_bytes: bytearray):
    """Securely wipe key from memory

    Performs multiple overwrites to prevent key recovery from RAM.

    Args:
        key_bytes: Key material as mutable bytearray
    """
    length = len(key_bytes)

    # Overwrite with zeros
    ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(key_bytes)), 0, length)

    # Overwrite with random
    random_bytes = os.urandom(length)
    for i in range(length):
        key_bytes[i] = random_bytes[i]

    # Overwrite with ones
    ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(key_bytes)), 0xFF, length)

    # Final zero
    ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(key_bytes)), 0, length)


# ===== Key Generation =====

def generate_x25519_keypair() -> Tuple[bytes, bytes]:
    """Generate X25519 key pair for message encryption

    Returns:
        (private_key, public_key) tuple of 32-byte keys
    """
    private_key = PrivateKey.generate()
    public_key = private_key.public_key

    return bytes(private_key), bytes(public_key)


# ===== BIP39 Seed Phrase Derivation =====

def derive_ed25519_from_seed_phrase(seed_phrase: str) -> Tuple[bytes, bytes]:
    """Derive Ed25519 signing key pair from BIP39 seed phrase

    Args:
        seed_phrase: 12 or 24 word BIP39 mnemonic phrase

    Returns:
        (private_key, public_key) tuple of 32-byte Ed25519 keys

    Raises:
        ValueError: If seed phrase is invalid
    """
    mnemo = Mnemonic("english")

    # Validate the seed phrase
    if not mnemo.check(seed_phrase):
        raise ValueError("Invalid BIP39 seed phrase")

    # Convert mnemonic to seed (512 bits)
    # Using empty passphrase - could add passphrase support later
    seed = mnemo.to_seed(seed_phrase, passphrase="")

    # Derive Ed25519 key from first 32 bytes of seed
    # This is a simplified derivation - production might use BIP32/BIP44 path
    seed_bytes = seed[:32]

    # Create Ed25519 signing key
    signing_key = SigningKey(seed_bytes)
    verify_key = signing_key.verify_key

    return bytes(signing_key), bytes(verify_key)


def generate_bip39_seed_phrase(word_count: int = 12) -> str:
    """Generate a valid BIP39 seed phrase

    Args:
        word_count: Number of words (12, 15, 18, 21, or 24)

    Returns:
        BIP39 mnemonic phrase

    Raises:
        ValueError: If word_count is invalid
    """
    if word_count not in [12, 15, 18, 21, 24]:
        raise ValueError("word_count must be 12, 15, 18, 21, or 24")

    # Calculate strength in bits: 128, 160, 192, 224, or 256
    strength = (word_count * 11) - (word_count // 3)

    mnemo = Mnemonic("english")
    return mnemo.generate(strength=strength)
