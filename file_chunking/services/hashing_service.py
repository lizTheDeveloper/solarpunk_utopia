"""
Hashing Service

Provides content addressing with SHA-256.
All files and chunks are content-addressed with immutable hashes.
"""

import hashlib
from typing import BinaryIO


class HashingService:
    """
    Service for generating SHA-256 content hashes.

    Provides:
    - File hashing (complete files)
    - Chunk hashing (individual chunks)
    - Stream hashing (for large files)
    """

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """
        Hash bytes and return hex digest.

        Args:
            data: Raw bytes to hash

        Returns:
            64-character hex string (SHA-256 hash)
        """
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def hash_file_content(data: bytes) -> str:
        """
        Hash file content and return formatted file hash.

        Args:
            data: Complete file content as bytes

        Returns:
            File hash in format: file:sha256:...
        """
        hash_hex = HashingService.hash_bytes(data)
        return f"file:sha256:{hash_hex}"

    @staticmethod
    def hash_chunk_content(data: bytes) -> str:
        """
        Hash chunk content and return formatted chunk hash.

        Args:
            data: Chunk content as bytes

        Returns:
            Chunk hash in format: chunk:sha256:...
        """
        hash_hex = HashingService.hash_bytes(data)
        return f"chunk:sha256:{hash_hex}"

    @staticmethod
    def hash_file_stream(file_stream: BinaryIO, buffer_size: int = 65536) -> str:
        """
        Hash a file stream incrementally (for large files).

        Args:
            file_stream: File-like object opened in binary mode
            buffer_size: Size of read buffer (default 64KB)

        Returns:
            File hash in format: file:sha256:...
        """
        sha256_hash = hashlib.sha256()

        # Read file in chunks to avoid loading entire file into memory
        while True:
            chunk = file_stream.read(buffer_size)
            if not chunk:
                break
            sha256_hash.update(chunk)

        hash_hex = sha256_hash.hexdigest()
        return f"file:sha256:{hash_hex}"

    @staticmethod
    def verify_file_hash(data: bytes, expected_hash: str) -> bool:
        """
        Verify file content matches expected hash.

        Args:
            data: File content as bytes
            expected_hash: Expected hash in format file:sha256:...

        Returns:
            True if hash matches, False otherwise
        """
        actual_hash = HashingService.hash_file_content(data)
        return actual_hash == expected_hash

    @staticmethod
    def verify_chunk_hash(data: bytes, expected_hash: str) -> bool:
        """
        Verify chunk content matches expected hash.

        Args:
            data: Chunk content as bytes
            expected_hash: Expected hash in format chunk:sha256:...

        Returns:
            True if hash matches, False otherwise
        """
        actual_hash = HashingService.hash_chunk_content(data)
        return actual_hash == expected_hash

    @staticmethod
    def extract_hex_hash(formatted_hash: str) -> str:
        """
        Extract hex hash from formatted hash string.

        Args:
            formatted_hash: Hash in format file:sha256:... or chunk:sha256:...

        Returns:
            64-character hex hash

        Raises:
            ValueError: If format is invalid
        """
        if formatted_hash.startswith('file:sha256:'):
            return formatted_hash[12:]
        elif formatted_hash.startswith('chunk:sha256:'):
            return formatted_hash[13:]
        elif formatted_hash.startswith('b:sha256:'):  # Bundle hash format
            return formatted_hash[9:]
        else:
            raise ValueError(f"Invalid hash format: {formatted_hash}")

    @staticmethod
    def combine_hashes(hash1: str, hash2: str) -> str:
        """
        Combine two hashes to create parent hash (for Merkle tree).

        Args:
            hash1: First hash (64-char hex)
            hash2: Second hash (64-char hex)

        Returns:
            Combined hash (64-char hex)
        """
        # Extract hex from formatted hashes if needed
        try:
            hex1 = HashingService.extract_hex_hash(hash1) if ':' in hash1 else hash1
            hex2 = HashingService.extract_hex_hash(hash2) if ':' in hash2 else hash2
        except ValueError:
            # If extraction fails, assume they're already hex
            hex1 = hash1
            hex2 = hash2

        # Concatenate and hash
        combined = hex1 + hex2
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
