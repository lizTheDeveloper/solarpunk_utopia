"""
Multiverse Mesh DNS - .multiversemesh namespace

Provides mDNS/DNS-SD service discovery and human-readable names
for nodes on the solarpunk mesh network.

Features:
- Announce your node as {name}.multiversemesh
- Discover other nodes by name
- Automatic service discovery (DTN, ValueFlows, AI inference)
- DTN URI resolution: dtn://alice.multiversemesh/offers
"""

import os
import socket
import asyncio
import json
from typing import Optional, Dict, List, Set
from datetime import datetime
from pathlib import Path

try:
    from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser, ServiceListener
    from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False
    print("⚠️  zeroconf not installed - mDNS discovery disabled")
    print("   Install: pip install zeroconf")

import structlog

logger = structlog.get_logger()


class MultiverseMeshNaming:
    """
    Multiverse Mesh Naming Service

    Manages .multiversemesh namespace for the mesh network:
    - Announces this node via mDNS
    - Discovers other .multiversemesh nodes
    - Resolves names to IPs
    - Handles DTN URI mapping
    """

    def __init__(
        self,
        node_name: Optional[str] = None,
        community_name: Optional[str] = None,
        data_dir: str = "./data/mesh_naming",
    ):
        """
        Initialize mesh naming service

        Args:
            node_name: Your mesh name (e.g., "alice")
            community_name: Optional community subdomain
            data_dir: Directory for name registry cache
        """
        self.node_name = node_name or self._generate_node_name()
        self.community_name = community_name
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Full mesh name
        if community_name:
            self.mesh_fqdn = f"{self.node_name}.{community_name}.multiversemesh"
        else:
            self.mesh_fqdn = f"{self.node_name}.multiversemesh"

        # Name registry (cached from network)
        self.registry_file = self.data_dir / "name_registry.json"
        self.name_registry: Dict[str, Dict] = self._load_registry()

        # mDNS service
        self.zeroconf: Optional[Zeroconf] = None
        self.service_info: Optional[ServiceInfo] = None
        self.discovered_nodes: Dict[str, Dict] = {}

        logger.info(
            "mesh_naming_initialized",
            mesh_name=self.mesh_fqdn,
            node_name=self.node_name,
            community=self.community_name,
        )

    def _generate_node_name(self) -> str:
        """Generate a friendly node name"""
        # Try hostname first
        hostname = socket.gethostname().split('.')[0].lower()

        # Clean it up (alphanumeric + hyphens only)
        clean_name = ''.join(c if c.isalnum() or c == '-' else '-' for c in hostname)

        # If too generic, add random suffix
        if clean_name in ('localhost', 'android', 'termux', 'phone'):
            import random
            adjectives = ['happy', 'brave', 'kind', 'bright', 'swift', 'wise', 'cool', 'wild']
            nouns = ['fox', 'hawk', 'wolf', 'bear', 'deer', 'owl', 'bee', 'tree']
            clean_name = f"{random.choice(adjectives)}-{random.choice(nouns)}"

        return clean_name

    def _load_registry(self) -> Dict[str, Dict]:
        """Load name registry from disk"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_registry(self):
        """Save name registry to disk"""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.name_registry, f, indent=2)
        except Exception as e:
            logger.error("registry_save_failed", error=str(e))

    def announce(
        self,
        dtn_port: int = 8000,
        valueflows_port: int = 8001,
        ai_port: int = 8005,
    ):
        """
        Announce this node on the mesh via mDNS

        Advertises services:
        - _dtn._tcp.local - DTN bundle system
        - _valueflows._tcp.local - ValueFlows API
        - _ai-inference._tcp.local - AI inference
        """
        if not ZEROCONF_AVAILABLE:
            logger.warning("mdns_unavailable", message="zeroconf not installed")
            return

        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            ip_bytes = socket.inet_aton(local_ip)

            # Create service info
            service_type = "_multiversemesh._tcp.local."
            service_name = f"{self.mesh_fqdn}.{service_type}"

            properties = {
                'mesh_name': self.mesh_fqdn.encode('utf-8'),
                'node_name': self.node_name.encode('utf-8'),
                'dtn_port': str(dtn_port).encode('utf-8'),
                'vf_port': str(valueflows_port).encode('utf-8'),
                'ai_port': str(ai_port).encode('utf-8'),
            }

            if self.community_name:
                properties['community'] = self.community_name.encode('utf-8')

            self.service_info = ServiceInfo(
                service_type,
                service_name,
                addresses=[ip_bytes],
                port=dtn_port,
                properties=properties,
                server=f"{self.mesh_fqdn}.local.",
            )

            # Register service
            self.zeroconf = Zeroconf()
            self.zeroconf.register_service(self.service_info)

            logger.info(
                "mdns_announced",
                mesh_name=self.mesh_fqdn,
                ip=local_ip,
                services=f"dtn:{dtn_port}, vf:{valueflows_port}, ai:{ai_port}",
            )

        except Exception as e:
            logger.error("mdns_announce_failed", error=str(e))

    def discover(self, timeout: float = 5.0) -> List[Dict]:
        """
        Discover other .multiversemesh nodes on the network

        Returns:
            List of discovered nodes with their info
        """
        if not ZEROCONF_AVAILABLE:
            return []

        discovered = []

        class MeshListener(ServiceListener):
            def __init__(self, nodes_list):
                self.nodes = nodes_list

            def add_service(self, zc, type_, name):
                info = zc.get_service_info(type_, name)
                if info:
                    props = {
                        k.decode('utf-8'): v.decode('utf-8')
                        for k, v in info.properties.items()
                    }

                    node_info = {
                        'mesh_name': props.get('mesh_name', ''),
                        'node_name': props.get('node_name', ''),
                        'community': props.get('community'),
                        'ip': socket.inet_ntoa(info.addresses[0]),
                        'ports': {
                            'dtn': int(props.get('dtn_port', 8000)),
                            'valueflows': int(props.get('vf_port', 8001)),
                            'ai': int(props.get('ai_port', 8005)),
                        },
                        'discovered_at': datetime.utcnow().isoformat(),
                    }

                    self.nodes.append(node_info)
                    logger.info("node_discovered", **node_info)

            def remove_service(self, zc, type_, name):
                pass

            def update_service(self, zc, type_, name):
                pass

        try:
            zeroconf = Zeroconf()
            listener = MeshListener(discovered)
            browser = ServiceBrowser(zeroconf, "_multiversemesh._tcp.local.", listener)

            # Wait for discoveries
            import time
            time.sleep(timeout)

            browser.cancel()
            zeroconf.close()

            # Update registry
            for node in discovered:
                mesh_name = node['mesh_name']
                self.name_registry[mesh_name] = node

            self._save_registry()

        except Exception as e:
            logger.error("discovery_failed", error=str(e))

        return discovered

    def resolve(self, mesh_name: str) -> Optional[Dict]:
        """
        Resolve a .multiversemesh name to connection info

        Args:
            mesh_name: Full mesh name (e.g., "alice.multiversemesh")

        Returns:
            Node info dict with IP and ports, or None if not found
        """
        # Normalize name
        if not mesh_name.endswith('.multiversemesh'):
            mesh_name = f"{mesh_name}.multiversemesh"

        # Check registry (cached)
        if mesh_name in self.name_registry:
            node = self.name_registry[mesh_name]

            # Check if cache is fresh (< 5 minutes old)
            discovered_at = datetime.fromisoformat(node['discovered_at'])
            age_seconds = (datetime.utcnow() - discovered_at).total_seconds()

            if age_seconds < 300:  # 5 minutes
                return node

        # Not in cache or stale - try live discovery
        discovered = self.discover(timeout=2.0)

        for node in discovered:
            if node['mesh_name'] == mesh_name:
                return node

        return None

    def resolve_dtn_uri(self, dtn_uri: str) -> Optional[str]:
        """
        Resolve DTN URI to HTTP endpoint

        Args:
            dtn_uri: DTN URI like "dtn://alice.multiversemesh/offers"

        Returns:
            HTTP URL like "http://192.168.1.10:8001/vf/offers"
        """
        if not dtn_uri.startswith('dtn://'):
            return None

        # Parse URI: dtn://alice.multiversemesh/path
        parts = dtn_uri[6:].split('/', 1)
        mesh_name = parts[0]
        path = parts[1] if len(parts) > 1 else ''

        # Resolve name
        node = self.resolve(mesh_name)
        if not node:
            return None

        # Map path to appropriate service
        if path.startswith('vf/') or path.startswith('offers') or path.startswith('needs'):
            port = node['ports']['valueflows']
            if not path.startswith('vf/'):
                path = f"vf/{path}"
        elif path.startswith('bundles') or path.startswith('sync'):
            port = node['ports']['dtn']
        elif path.startswith('ai') or path.startswith('inference'):
            port = node['ports']['ai']
        else:
            port = node['ports']['dtn']  # Default to DTN

        return f"http://{node['ip']}:{port}/{path}"

    def list_nodes(self) -> List[Dict]:
        """List all known nodes from registry"""
        return list(self.name_registry.values())

    def shutdown(self):
        """Clean shutdown - unregister mDNS services"""
        if self.zeroconf and self.service_info:
            try:
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
                logger.info("mdns_unregistered", mesh_name=self.mesh_fqdn)
            except:
                pass


# Singleton instance
_mesh_naming: Optional[MultiverseMeshNaming] = None


def get_mesh_naming(
    node_name: Optional[str] = None,
    community_name: Optional[str] = None,
) -> MultiverseMeshNaming:
    """Get or create the mesh naming singleton"""
    global _mesh_naming

    if _mesh_naming is None:
        # Load from config
        node_name = node_name or os.getenv('MESH_NAME')
        community_name = community_name or os.getenv('COMMUNITY_NAME')

        _mesh_naming = MultiverseMeshNaming(
            node_name=node_name,
            community_name=community_name,
        )

    return _mesh_naming
