"""
Merkle Tree Service

Builds and verifies Merkle trees for efficient chunk verification.
"""

from typing import List, Optional, Tuple
from ..models import MerkleNode
from .hashing_service import HashingService


class MerkleTreeService:
    """
    Service for building and verifying Merkle trees.

    A Merkle tree allows:
    - Efficient verification of individual chunks
    - Proof that a chunk belongs to a file
    - Detection of tampering
    """

    @staticmethod
    def build_tree(chunk_hashes: List[str]) -> MerkleNode:
        """
        Build a Merkle tree from chunk hashes.

        Args:
            chunk_hashes: Ordered list of chunk hashes (format: chunk:sha256:...)

        Returns:
            Root node of Merkle tree

        Raises:
            ValueError: If chunk_hashes is empty
        """
        if not chunk_hashes:
            raise ValueError("Cannot build Merkle tree from empty chunk list")

        # Extract hex hashes
        hex_hashes = [
            HashingService.extract_hex_hash(h) for h in chunk_hashes
        ]

        # Build leaf nodes
        nodes = [
            MerkleNode(hash=h, isLeaf=True)
            for h in hex_hashes
        ]

        # Build tree bottom-up
        while len(nodes) > 1:
            parent_nodes = []

            # Pair up nodes and create parents
            for i in range(0, len(nodes), 2):
                left = nodes[i]

                # If odd number of nodes, duplicate the last one
                if i + 1 < len(nodes):
                    right = nodes[i + 1]
                else:
                    right = nodes[i]

                # Combine hashes to create parent
                parent_hash = HashingService.combine_hashes(left.hash, right.hash)
                parent = MerkleNode(
                    hash=parent_hash,
                    left=left,
                    right=right,
                    isLeaf=False
                )
                parent_nodes.append(parent)

            nodes = parent_nodes

        # Return root node
        return nodes[0]

    @staticmethod
    def get_root_hash(tree: MerkleNode) -> str:
        """
        Get the root hash from a Merkle tree.

        Args:
            tree: Root node of Merkle tree

        Returns:
            Root hash (64-char hex)
        """
        return tree.hash

    @staticmethod
    def generate_proof(tree: MerkleNode, chunk_index: int, total_chunks: int) -> List[Tuple[str, bool]]:
        """
        Generate Merkle proof for a chunk at given index.

        The proof is a list of sibling hashes needed to verify the chunk.

        Args:
            tree: Root node of Merkle tree
            chunk_index: Index of chunk (0-based)
            total_chunks: Total number of chunks in tree

        Returns:
            List of (hash, is_left) tuples representing the proof path

        Raises:
            ValueError: If chunk_index is out of range
        """
        if chunk_index < 0 or chunk_index >= total_chunks:
            raise ValueError(f"Chunk index {chunk_index} out of range [0, {total_chunks})")

        proof = []
        current_index = chunk_index
        current_node = tree
        level_size = total_chunks

        # Traverse from root to leaf, collecting sibling hashes
        while not current_node.isLeaf:
            # Determine which child to follow
            mid = (level_size + 1) // 2

            if current_index < mid:
                # Go left, add right sibling to proof
                if current_node.right:
                    proof.append((current_node.right.hash, False))
                current_node = current_node.left
                level_size = mid
            else:
                # Go right, add left sibling to proof
                if current_node.left:
                    proof.append((current_node.left.hash, True))
                current_node = current_node.right
                current_index -= mid
                level_size = level_size - mid

        return proof

    @staticmethod
    def verify_proof(
        chunk_hash: str,
        chunk_index: int,
        proof: List[Tuple[str, bool]],
        root_hash: str
    ) -> bool:
        """
        Verify a Merkle proof for a chunk.

        Args:
            chunk_hash: Hash of the chunk (chunk:sha256:... or hex)
            chunk_index: Index of chunk in file
            proof: List of (hash, is_left) tuples from generate_proof
            root_hash: Expected root hash

        Returns:
            True if proof is valid, False otherwise
        """
        # Extract hex hash if formatted
        try:
            current_hash = HashingService.extract_hex_hash(chunk_hash)
        except ValueError:
            current_hash = chunk_hash

        # Verify proof by hashing up the tree
        for sibling_hash, is_left in proof:
            if is_left:
                # Sibling is on the left
                current_hash = HashingService.combine_hashes(sibling_hash, current_hash)
            else:
                # Sibling is on the right
                current_hash = HashingService.combine_hashes(current_hash, sibling_hash)

        # Check if we arrived at the root hash
        return current_hash == root_hash

    @staticmethod
    def verify_chunk_in_tree(
        tree: MerkleNode,
        chunk_hash: str,
        chunk_index: int,
        total_chunks: int
    ) -> bool:
        """
        Verify that a chunk with given hash exists at given index in tree.

        Args:
            tree: Root node of Merkle tree
            chunk_hash: Hash of chunk to verify
            chunk_index: Expected index of chunk
            total_chunks: Total number of chunks

        Returns:
            True if chunk is valid, False otherwise
        """
        try:
            # Generate proof for this chunk
            proof = MerkleTreeService.generate_proof(tree, chunk_index, total_chunks)

            # Verify proof
            root_hash = MerkleTreeService.get_root_hash(tree)
            return MerkleTreeService.verify_proof(chunk_hash, chunk_index, proof, root_hash)
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def tree_to_dict(node: Optional[MerkleNode]) -> Optional[dict]:
        """
        Convert Merkle tree to dictionary for serialization.

        Args:
            node: Merkle tree node

        Returns:
            Dictionary representation of tree
        """
        if node is None:
            return None

        return {
            "hash": node.hash,
            "isLeaf": node.isLeaf,
            "left": MerkleTreeService.tree_to_dict(node.left),
            "right": MerkleTreeService.tree_to_dict(node.right)
        }

    @staticmethod
    def dict_to_tree(data: Optional[dict]) -> Optional[MerkleNode]:
        """
        Convert dictionary to Merkle tree.

        Args:
            data: Dictionary representation of tree

        Returns:
            Merkle tree node
        """
        if data is None:
            return None

        return MerkleNode(
            hash=data["hash"],
            isLeaf=data["isLeaf"],
            left=MerkleTreeService.dict_to_tree(data.get("left")),
            right=MerkleTreeService.dict_to_tree(data.get("right"))
        )
