#!/usr/bin/env python3
"""
Multiverse Mesh CLI - Manage your .multiversemesh identity

Commands:
  mesh whoami              - Show your mesh name
  mesh claim <name>        - Claim a new mesh name
  mesh discover            - Find other nodes
  mesh lookup <name>       - Look up a mesh name
  mesh resolve <dtn-uri>   - Resolve DTN URI to HTTP URL
  mesh announce            - Start announcing on the network
"""

import sys
import argparse
from mesh_dns import get_mesh_naming, MultiverseMeshNaming


def cmd_whoami(args):
    """Show current mesh identity"""
    mesh = get_mesh_naming()

    print(f"🌐 Your Multiverse Mesh Identity")
    print(f"=" * 50)
    print(f"Mesh Name:    {mesh.mesh_fqdn}")
    print(f"Node Name:    {mesh.node_name}")
    if mesh.community_name:
        print(f"Community:    {mesh.community_name}")
    print()
    print(f"Services:")
    print(f"  DTN:        dtn://{mesh.mesh_fqdn}/")
    print(f"  Offers:     dtn://{mesh.mesh_fqdn}/offers")
    print(f"  Needs:      dtn://{mesh.mesh_fqdn}/needs")
    print(f"  AI:         dtn://{mesh.mesh_fqdn}/ai/inference")


def cmd_claim(args):
    """Claim a new mesh name"""
    import os

    name = args.name
    community = args.community

    # Validate name
    if not name.replace('-', '').isalnum():
        print("❌ Name must be alphanumeric (hyphens allowed)")
        return 1

    # Save to config
    config_dir = os.path.expanduser("~/.config/multiversemesh")
    os.makedirs(config_dir, exist_ok=True)

    with open(f"{config_dir}/identity", "w") as f:
        f.write(f"MESH_NAME={name}\n")
        if community:
            f.write(f"COMMUNITY_NAME={community}\n")

    # Create mesh naming with new identity
    mesh = MultiverseMeshNaming(node_name=name, community_name=community)

    print(f"✅ Claimed: {mesh.mesh_fqdn}")
    print()
    print(f"Add to your environment:")
    print(f"  export MESH_NAME={name}")
    if community:
        print(f"  export COMMUNITY_NAME={community}")


def cmd_discover(args):
    """Discover other mesh nodes"""
    mesh = get_mesh_naming()

    print(f"🔍 Discovering .multiversemesh nodes...")
    print()

    nodes = mesh.discover(timeout=float(args.timeout))

    if not nodes:
        print("No nodes found. Make sure:")
        print("  • Other nodes are running mesh services")
        print("  • You're on the same local network")
        print("  • Firewall allows mDNS (port 5353 UDP)")
        return

    print(f"Found {len(nodes)} node(s):")
    print()

    for node in nodes:
        print(f"📍 {node['mesh_name']}")
        print(f"   IP:         {node['ip']}")
        print(f"   Node:       {node['node_name']}")
        if node.get('community'):
            print(f"   Community:  {node['community']}")
        print(f"   DTN:        http://{node['ip']}:{node['ports']['dtn']}")
        print(f"   ValueFlows: http://{node['ip']}:{node['ports']['valueflows']}")
        print(f"   AI:         http://{node['ip']}:{node['ports']['ai']}")
        print()


def cmd_lookup(args):
    """Look up a mesh name"""
    mesh = get_mesh_naming()
    name = args.name

    if not name.endswith('.multiversemesh'):
        name = f"{name}.multiversemesh"

    print(f"🔎 Looking up {name}...")
    print()

    node = mesh.resolve(name)

    if not node:
        print(f"❌ Not found")
        print()
        print(f"Try:")
        print(f"  mesh discover  # Scan for nearby nodes")
        return 1

    print(f"✅ Found!")
    print()
    print(f"Name:       {node['mesh_name']}")
    print(f"IP:         {node['ip']}")
    print(f"Node:       {node['node_name']}")
    if node.get('community'):
        print(f"Community:  {node['community']}")
    print()
    print(f"Endpoints:")
    print(f"  DTN API:      http://{node['ip']}:{node['ports']['dtn']}")
    print(f"  ValueFlows:   http://{node['ip']}:{node['ports']['valueflows']}")
    print(f"  AI Inference: http://{node['ip']}:{node['ports']['ai']}")


def cmd_resolve(args):
    """Resolve DTN URI to HTTP URL"""
    mesh = get_mesh_naming()
    uri = args.uri

    print(f"🔗 Resolving {uri}...")
    print()

    http_url = mesh.resolve_dtn_uri(uri)

    if not http_url:
        print(f"❌ Could not resolve")
        print()
        print(f"Make sure:")
        print(f"  • URI format: dtn://name.multiversemesh/path")
        print(f"  • Node is discoverable: mesh discover")
        return 1

    print(f"✅ Resolved:")
    print(f"   {http_url}")
    print()
    print(f"Try:")
    print(f"  curl {http_url}")


def cmd_announce(args):
    """Announce services on the network"""
    mesh = get_mesh_naming()

    dtn_port = args.dtn_port
    vf_port = args.vf_port
    ai_port = args.ai_port

    print(f"📡 Announcing {mesh.mesh_fqdn} on the network...")
    print()

    mesh.announce(
        dtn_port=dtn_port,
        valueflows_port=vf_port,
        ai_port=ai_port,
    )

    print(f"✅ Broadcasting as:")
    print(f"   {mesh.mesh_fqdn}")
    print()
    print(f"Services:")
    print(f"   DTN:        :{dtn_port}")
    print(f"   ValueFlows: :{vf_port}")
    print(f"   AI:         :{ai_port}")
    print()
    print(f"Press Ctrl+C to stop")

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print(f"Shutting down...")
        mesh.shutdown()


def main():
    parser = argparse.ArgumentParser(
        description="Multiverse Mesh - Manage your .multiversemesh identity"
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # whoami
    subparsers.add_parser('whoami', help='Show your mesh identity')

    # claim
    claim_parser = subparsers.add_parser('claim', help='Claim a mesh name')
    claim_parser.add_argument('name', help='Your mesh name (e.g., alice)')
    claim_parser.add_argument('--community', help='Community name (optional)')

    # discover
    discover_parser = subparsers.add_parser('discover', help='Find other nodes')
    discover_parser.add_argument('--timeout', default='5', help='Discovery timeout (seconds)')

    # lookup
    lookup_parser = subparsers.add_parser('lookup', help='Look up a mesh name')
    lookup_parser.add_argument('name', help='Mesh name to look up')

    # resolve
    resolve_parser = subparsers.add_parser('resolve', help='Resolve DTN URI')
    resolve_parser.add_argument('uri', help='DTN URI (e.g., dtn://alice.multiversemesh/offers)')

    # announce
    announce_parser = subparsers.add_parser('announce', help='Announce services')
    announce_parser.add_argument('--dtn-port', type=int, default=8000, help='DTN port')
    announce_parser.add_argument('--vf-port', type=int, default=8001, help='ValueFlows port')
    announce_parser.add_argument('--ai-port', type=int, default=8005, help='AI inference port')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        'whoami': cmd_whoami,
        'claim': cmd_claim,
        'discover': cmd_discover,
        'lookup': cmd_lookup,
        'resolve': cmd_resolve,
        'announce': cmd_announce,
    }

    return commands[args.command](args) or 0


if __name__ == '__main__':
    sys.exit(main())
