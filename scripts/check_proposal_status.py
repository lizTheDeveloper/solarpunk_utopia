#!/usr/bin/env python3
import os
import re
from pathlib import Path

changes_dir = Path("/Users/annhoward/src/solarpunk_utopia/openspec/changes")

proposals = []
for proposal_path in sorted(changes_dir.glob("*/proposal.md")):
    with open(proposal_path) as f:
        content = f.read()

    # Extract status
    status_match = re.search(r'\*\*Status:\*\*\s*(.+)', content)
    status = status_match.group(1).strip() if status_match else "Unknown"

    # Extract priority
    priority_match = re.search(r'\*\*Priority:\*\*\s*(.+)', content)
    priority = priority_match.group(1).strip() if priority_match else "Unknown"

    dirname = proposal_path.parent.name
    proposals.append((dirname, status, priority))

# Group by status
print("=" * 80)
print("DRAFT PROPOSALS (Not Yet Implemented)")
print("=" * 80)
for name, status, priority in proposals:
    if "Draft" in status:
        print(f"{name:45} | {priority}")

print("\n" + "=" * 80)
print("IMPLEMENTED/IN-PROGRESS PROPOSALS")
print("=" * 80)
for name, status, priority in proposals:
    if "Draft" not in status:
        print(f"{name:45} | {status:20} | {priority}")
