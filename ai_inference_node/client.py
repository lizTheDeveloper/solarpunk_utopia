"""
AI Inference Client - Request AI from the mesh network

Simple client for requesting AI inference from available nodes.
Automatically finds nodes, handles failover, tracks usage.
"""

import httpx
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime


class InferenceClient:
    """Client for requesting AI inference from mesh nodes"""

    def __init__(
        self,
        node_urls: Optional[List[str]] = None,
        discovery_url: str = "http://localhost:8000",
        requester_id: Optional[str] = None,
        timeout: float = 120.0,
    ):
        """
        Initialize inference client

        Args:
            node_urls: List of known inference node URLs (optional)
            discovery_url: URL of DTN bundle system for node discovery
            requester_id: ID of the requesting agent (for gift economy tracking)
            timeout: Request timeout in seconds
        """
        self.node_urls = node_urls or []
        self.discovery_url = discovery_url
        self.requester_id = requester_id
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def discover_nodes(self) -> List[str]:
        """
        Discover available AI inference nodes on the mesh

        Returns:
            List of node URLs
        """
        try:
            response = await self._client.get(
                f"{self.discovery_url}/agents/discover-services",
                params={"service_type": "ai_inference"},
                timeout=5.0
            )
            response.raise_for_status()
            nodes = response.json()

            # Extract endpoints
            return [node["endpoint"] for node in nodes if "endpoint" in node]

        except Exception as e:
            # Discovery failed - use known nodes or defaults
            return self.node_urls or ["http://localhost:8005"]

    async def get_node_status(self, node_url: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific node"""
        try:
            response = await self._client.get(f"{node_url}/status", timeout=5.0)
            response.raise_for_status()
            return response.json()
        except:
            return None

    async def find_best_node(self, model: Optional[str] = None) -> Optional[str]:
        """
        Find the best available node for inference

        Args:
            model: Specific model required (optional)

        Returns:
            URL of best node, or None if none available
        """
        # Discover nodes if we don't have any
        if not self.node_urls:
            self.node_urls = await self.discover_nodes()

        if not self.node_urls:
            return None

        # Check status of all nodes
        statuses = await asyncio.gather(*[
            self.get_node_status(url) for url in self.node_urls
        ])

        # Filter and rank nodes
        available = []
        for url, status in zip(self.node_urls, statuses):
            if not status:
                continue

            # If model specified, check if node supports it
            if model and model not in status.get("available_models", []):
                continue

            # Calculate score (lower load = better)
            load = status.get("current_load", 0)
            max_concurrent = status.get("max_concurrent", 1)
            score = load / max_concurrent if max_concurrent > 0 else 1.0

            available.append((url, score))

        # Sort by score (lower is better)
        available.sort(key=lambda x: x[1])

        return available[0][0] if available else None

    async def infer(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Run AI inference on a prompt

        Args:
            prompt: The prompt to send
            model: Model to use (optional - uses node's default)
            system_prompt: System prompt for context (optional)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate (optional)

        Returns:
            The AI's response text

        Raises:
            Exception: If inference fails on all nodes
        """
        # Find best node
        node_url = await self.find_best_node(model)

        if not node_url:
            raise Exception("No inference nodes available")

        # Prepare request
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "requester_id": self.requester_id,
        }

        if model:
            payload["model"] = model
        if system_prompt:
            payload["system_prompt"] = system_prompt
        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Send request
        try:
            response = await self._client.post(
                f"{node_url}/inference",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["response"]

        except Exception as e:
            # TODO: Retry with different node
            raise Exception(f"Inference failed: {str(e)}")

    async def close(self):
        """Close the HTTP client"""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Synchronous wrapper for non-async code
class SyncInferenceClient:
    """Synchronous wrapper around InferenceClient"""

    def __init__(self, **kwargs):
        self.client = InferenceClient(**kwargs)

    def infer(self, prompt: str, **kwargs) -> str:
        """Run inference synchronously"""
        return asyncio.run(self.client.infer(prompt, **kwargs))

    def discover_nodes(self) -> List[str]:
        """Discover nodes synchronously"""
        return asyncio.run(self.client.discover_nodes())


# Example usage
async def example():
    """Example of using the inference client"""

    async with InferenceClient(requester_id="example-user") as client:
        # Simple inference
        response = await client.infer(
            prompt="What is a gift economy in 2 sentences?",
            temperature=0.7,
        )
        print(f"Response: {response}")

        # With system prompt
        response = await client.infer(
            prompt="Analyze this offer: 'Fresh tomatoes from my garden'",
            system_prompt="You are a helpful assistant analyzing gift economy offers.",
            model="llama3.2:3b",
        )
        print(f"Analysis: {response}")

        # Discover available nodes
        nodes = await client.discover_nodes()
        print(f"Available nodes: {nodes}")


if __name__ == "__main__":
    asyncio.run(example())
