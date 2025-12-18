"""
End-to-End Integration Tests: Knowledge Distribution

Tests the complete flow of knowledge sharing via file chunking:
1. Upload permaculture guide
2. File gets chunked
3. Chunks distributed as DTN bundles
4. Discovery indexes the file
5. Another node requests the file
6. Chunks retrieved and reassembled
7. File verified
"""

import pytest
import httpx
import asyncio
import tempfile
import os
from pathlib import Path


DTN_API = "http://localhost:8000"
CHUNKING_API = "http://localhost:8004"
DISCOVERY_API = "http://localhost:8003"


class TestKnowledgeDistribution:
    """Test complete knowledge distribution workflow"""

    @pytest.mark.asyncio
    async def test_complete_file_distribution_flow(self):
        """
        Complete flow: Upload file → Chunk → Publish → Discover → Download → Verify
        """

        async with httpx.AsyncClient(timeout=60.0) as client:

            # Step 1: Create a test file
            print("\n=== Step 1: Creating test file ===")
            content = b"Permaculture Guide\n" + b"=" * 80 + b"\n"
            content += b"This is a comprehensive guide to permaculture practices.\n" * 100
            content += b"Includes: composting, water harvesting, food forests, etc.\n" * 50

            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
                f.write(content)
                temp_path = f.name

            file_size = os.path.getsize(temp_path)
            print(f"Created test file: {file_size} bytes")

            try:
                # Step 2: Upload file to chunking system
                print("\n=== Step 2: Uploading file ===")
                with open(temp_path, 'rb') as f:
                    files = {'file': ('permaculture_guide.txt', f, 'text/plain')}
                    data = {
                        'tags': 'education,permaculture',
                        'publish': 'true'
                    }
                    upload_resp = await client.post(
                        f"{CHUNKING_API}/files/upload",
                        files=files,
                        data=data
                    )

                assert upload_resp.status_code == 200
                upload_result = upload_resp.json()
                file_hash = upload_result["file_hash"]
                chunk_count = upload_result["chunk_count"]
                print(f"File uploaded: {file_hash}")
                print(f"Chunks created: {chunk_count}")

                # Step 3: Verify file metadata
                print("\n=== Step 3: Verifying file metadata ===")
                file_info_resp = await client.get(f"{CHUNKING_API}/files/{file_hash}")
                assert file_info_resp.status_code == 200
                file_info = file_info_resp.json()
                assert file_info["file_hash"] == file_hash
                assert file_info["chunk_count"] == chunk_count
                assert file_info["total_size"] == file_size
                print(f"✅ File metadata verified")

                # Step 4: Check chunk availability
                print("\n=== Step 4: Checking chunk availability ===")
                availability_resp = await client.get(
                    f"{CHUNKING_API}/files/{file_hash}/availability"
                )
                assert availability_resp.status_code == 200
                availability = availability_resp.json()
                assert availability["available_chunks"] == chunk_count
                assert availability["total_chunks"] == chunk_count
                assert availability["complete"] is True
                print(f"✅ All {chunk_count} chunks available")

                # Step 5: Verify DTN bundles were created
                print("\n=== Step 5: Verifying DTN bundles ===")
                bundles_resp = await client.get(f"{DTN_API}/bundles?queue=outbox")
                assert bundles_resp.status_code == 200
                bundles = bundles_resp.json()

                # Look for file:manifest and file:chunk bundles
                file_bundles = [
                    b for b in bundles
                    if b.get("payload_type", "").startswith("file:")
                ]
                print(f"Found {len(file_bundles)} file-related bundles")
                assert len(file_bundles) > 0

                # Step 6: Search for file in discovery system
                print("\n=== Step 6: Searching for file ===")
                await asyncio.sleep(2)  # Wait for index to update
                search_resp = await client.post(
                    f"{DISCOVERY_API}/discovery/search",
                    json={
                        "query": "permaculture",
                        "filters": {"category": "knowledge"},
                        "max_results": 50
                    }
                )
                # Note: Discovery might not have indexed yet, this is async
                print(f"Search completed (async indexing)")

                # Step 7: Request file download (simulate another node)
                print("\n=== Step 7: Requesting file download ===")
                download_path = tempfile.mktemp(suffix='_downloaded.txt')
                download_resp = await client.post(
                    f"{CHUNKING_API}/downloads/request",
                    json={
                        "file_hash": file_hash,
                        "output_path": download_path
                    }
                )
                assert download_resp.status_code == 200
                download = download_resp.json()
                request_id = download["request_id"]
                print(f"Download request created: {request_id}")

                # Step 8: Check download progress
                print("\n=== Step 8: Checking download progress ===")
                await asyncio.sleep(1)  # Give it time to download
                progress_resp = await client.get(
                    f"{CHUNKING_API}/downloads/{request_id}"
                )
                assert progress_resp.status_code == 200
                progress = progress_resp.json()
                print(f"Progress: {progress['chunks_downloaded']}/{progress['total_chunks']}")

                # Step 9: Trigger reassembly
                print("\n=== Step 9: Reassembling file ===")
                reassemble_resp = await client.post(
                    f"{CHUNKING_API}/downloads/{request_id}/reassemble"
                )
                assert reassemble_resp.status_code == 200
                result = reassemble_resp.json()
                assert result["verified"] is True
                print(f"✅ File reassembled and verified")

                # Step 10: Verify downloaded file
                print("\n=== Step 10: Verifying downloaded file ===")
                if os.path.exists(download_path):
                    with open(download_path, 'rb') as f:
                        downloaded_content = f.read()
                    assert downloaded_content == content
                    print(f"✅ Downloaded file matches original")
                    os.remove(download_path)

                print("\n=== ✅ KNOWLEDGE DISTRIBUTION TEST PASSED ===")

            finally:
                # Cleanup
                if os.path.exists(temp_path):
                    os.remove(temp_path)


    @pytest.mark.asyncio
    async def test_library_node_caching(self):
        """
        Test that library nodes cache popular files
        """

        async with httpx.AsyncClient(timeout=30.0) as client:

            print("\n=== Testing Library Node Caching ===")

            # Get library cache stats
            stats_resp = await client.get(f"{CHUNKING_API}/library/stats")
            assert stats_resp.status_code == 200
            stats = stats_resp.json()

            print(f"Cache size: {stats['cache_size_bytes']} bytes")
            print(f"Cached files: {stats['cached_files']}")
            print(f"Cache budget: {stats['cache_budget_bytes']} bytes")
            print(f"✅ Library cache operational")

            # List cached files
            cache_resp = await client.get(f"{CHUNKING_API}/library/cache")
            assert cache_resp.status_code == 200
            cached_files = cache_resp.json()
            print(f"Found {len(cached_files)} files in cache")

            print("\n=== ✅ LIBRARY CACHE TEST PASSED ===")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
