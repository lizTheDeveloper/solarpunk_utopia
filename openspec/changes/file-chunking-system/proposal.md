# Proposal: File Chunking and Retrieval System

**Submitted By:** orchestrator
**Date:** 2025-12-17
**Status:** ✅ IMPLEMENTED - Content-addressed chunking, manifest generation, library cache, download orchestration
**Priority:** TIER 1 (Core Functionality)
**Complexity:** 3 systems (content addressing, chunking, retrieval)

---

## Problem Statement

Protocols, lessons, maps, and knowledge content are too large to include in bundles directly. Files must be split into chunks, distributed via DTN, and reassembled on demand. Library nodes need to cache large files for the community. Users need offline access to permaculture guides, repair manuals, and educational content.

**Current state:** No file distribution mechanism
**Desired state:** Content-addressed file chunking with opportunistic retrieval

---

## Proposed Solution

Implement content addressing (sha256) for all files. Split files into 256KB-1MB chunks. Distribute chunks as DTN bundles with long TTL. Metadata bundles reference file hashes. Library nodes cache popular content. Users request chunks opportunistically and reassemble locally.

---

## Requirements

### Requirement: Files SHALL Be Content-Addressed

All files SHALL have immutable content hash identifiers.

#### Scenario: File is added to system

- GIVEN a user uploads a PDF protocol
- WHEN the file is processed
- THEN the system SHALL:
  - Calculate sha256 hash of file content
  - Assign contentHash as unique identifier
  - Store metadata: filename, size, mimeType, contentHash

### Requirement: Files SHALL Be Chunked

Files larger than 256KB SHALL be split into chunks.

#### Scenario: Large file is chunked

- GIVEN a 5MB permaculture guide PDF
- WHEN preparing for distribution
- THEN the system SHALL:
  - Split into chunks (256KB-1MB each, configurable)
  - Calculate hash for each chunk
  - Create chunk manifest: [chunk0Hash, chunk1Hash, ...]
  - Store manifest separately

### Requirement: Chunks SHALL Be Distributed as Bundles

Chunks SHALL propagate via DTN bundles.

#### Scenario: Chunks are published

- GIVEN a file has been chunked
- WHEN publishing
- THEN each chunk SHALL be bundled:
  - payloadType: "file:chunk"
  - payload: base64-encoded chunk data
  - TTL: 180-365 days (knowledge content)
  - priority: low (not time-sensitive)
- AND manifest SHALL be bundled separately

### Requirement: Files SHALL Be Retrievable on Demand

Users SHALL request files and receive chunks opportunistically.

#### Scenario: User requests protocol PDF

- GIVEN user sees "Hot Composting Protocol" in index
- WHEN they request to download
- THEN the system SHALL:
  - Request manifest bundle (via contentHash)
  - Parse manifest to get chunk hashes
  - Request chunk bundles from network
  - Reassemble chunks as they arrive
  - Verify final file hash matches contentHash
  - Save to local cache

#### Scenario: Library node serves chunks

- GIVEN a library node has cached full file
- WHEN it receives chunk request
- THEN it SHALL respond with chunk bundle
- AND SHALL prioritize serving knowledge/education content

---

## Implementation Tasks

See `tasks.md` for detailed breakdown.

**Key deliverables:**
1. Content hashing utility (sha256)
2. File chunking engine
3. Chunk manifest format
4. Chunk bundler and publisher
5. Chunk request protocol
6. Chunk reassembly engine
7. Library node cache manager
8. UI for downloading files

---

## Success Criteria

- [ ] Files content-addressed (sha256)
- [ ] Files >256KB chunked correctly
- [ ] Chunks distributed as bundles
- [ ] Manifest bundles published
- [ ] Users can request files by hash
- [ ] Chunks reassembled correctly
- [ ] Final hash verified after reassembly
- [ ] Library nodes cache and serve popular files
- [ ] 10MB file retrieved in <30 min (via library node)
- [ ] Partial downloads resume correctly

---

## Dependencies

- DTN Bundle System

---

## Constraints

- Chunk size: 256KB-1MB (configurable)
- Library nodes need large storage (10GB+ for knowledge cache)

---

## Notes

This implements Section 7 "Files: Content Addressing + Chunking" from solarpunk_node_full_spec.md.
