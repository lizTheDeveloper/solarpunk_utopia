"""
Download Repository

Database access layer for download status tracking.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from ..models import FileDownloadStatus, DownloadStatus, DownloadProgress
from .schema import get_db

logger = logging.getLogger(__name__)


class DownloadRepository:
    """
    Repository for download status operations.

    Handles CRUD operations for file download tracking.
    """

    @staticmethod
    async def create(download: FileDownloadStatus) -> None:
        """
        Create a new download record.

        Args:
            download: FileDownloadStatus to store
        """
        db = await get_db()

        await db.execute("""
            INSERT INTO downloads (
                request_id, file_hash, file_name, file_size,
                status, manifest_received, total_chunks, received_chunks,
                bytes_received, percent_complete, started_at,
                completed_at, error_message, output_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            download.requestId,
            download.fileHash,
            download.fileName,
            download.fileSize,
            download.status.value,
            1 if download.manifestReceived else 0,
            download.progress.totalChunks if download.progress else 0,
            download.progress.receivedChunks if download.progress else 0,
            download.progress.bytesReceived if download.progress else 0,
            download.progress.percentComplete if download.progress else 0.0,
            download.startedAt.isoformat(),
            download.completedAt.isoformat() if download.completedAt else None,
            download.errorMessage,
            download.outputPath
        ))

        await db.commit()
        logger.debug(f"Created download record: {download.requestId}")

    @staticmethod
    async def get(request_id: str) -> Optional[FileDownloadStatus]:
        """
        Get download by request ID.

        Args:
            request_id: Unique download request ID

        Returns:
            FileDownloadStatus or None if not found
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT * FROM downloads WHERE request_id = ?
        """, (request_id,))

        row = await cursor.fetchone()

        if row is None:
            return None

        return await DownloadRepository._row_to_download(row)

    @staticmethod
    async def get_by_file(file_hash: str) -> List[FileDownloadStatus]:
        """
        Get all downloads for a file.

        Args:
            file_hash: Hash of file

        Returns:
            List of FileDownloadStatus
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT * FROM downloads
            WHERE file_hash = ?
            ORDER BY started_at DESC
        """, (file_hash,))

        rows = await cursor.fetchall()

        return [await DownloadRepository._row_to_download(row) for row in rows]

    @staticmethod
    async def get_active_downloads(limit: int = 100) -> List[FileDownloadStatus]:
        """
        Get all active (in-progress) downloads.

        Args:
            limit: Maximum number of downloads to return

        Returns:
            List of FileDownloadStatus
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT * FROM downloads
            WHERE status NOT IN (?, ?)
            ORDER BY started_at DESC
            LIMIT ?
        """, (DownloadStatus.COMPLETED.value, DownloadStatus.FAILED.value, limit))

        rows = await cursor.fetchall()

        return [await DownloadRepository._row_to_download(row) for row in rows]

    @staticmethod
    async def update(download: FileDownloadStatus) -> None:
        """
        Update download status.

        Args:
            download: Updated FileDownloadStatus
        """
        db = await get_db()

        await db.execute("""
            UPDATE downloads SET
                file_name = ?,
                file_size = ?,
                status = ?,
                manifest_received = ?,
                total_chunks = ?,
                received_chunks = ?,
                bytes_received = ?,
                percent_complete = ?,
                completed_at = ?,
                error_message = ?,
                output_path = ?
            WHERE request_id = ?
        """, (
            download.fileName,
            download.fileSize,
            download.status.value,
            1 if download.manifestReceived else 0,
            download.progress.totalChunks if download.progress else 0,
            download.progress.receivedChunks if download.progress else 0,
            download.progress.bytesReceived if download.progress else 0,
            download.progress.percentComplete if download.progress else 0.0,
            download.completedAt.isoformat() if download.completedAt else None,
            download.errorMessage,
            download.outputPath,
            download.requestId
        ))

        await db.commit()
        logger.debug(f"Updated download: {download.requestId}")

    @staticmethod
    async def delete(request_id: str) -> None:
        """
        Delete download record.

        Args:
            request_id: Request ID of download to delete
        """
        db = await get_db()

        await db.execute("""
            DELETE FROM downloads WHERE request_id = ?
        """, (request_id,))

        await db.commit()
        logger.debug(f"Deleted download: {request_id}")

    @staticmethod
    async def exists(request_id: str) -> bool:
        """
        Check if download exists.

        Args:
            request_id: Request ID to check

        Returns:
            True if exists, False otherwise
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT COUNT(*) FROM downloads WHERE request_id = ?
        """, (request_id,))

        row = await cursor.fetchone()
        return row[0] > 0

    @staticmethod
    async def _row_to_download(row) -> FileDownloadStatus:
        """Convert database row to FileDownloadStatus"""
        # Create progress object if we have chunk data
        progress = None
        if row['total_chunks'] > 0:
            # We need to reconstruct missing chunks list
            # This is a simplified version - in production, you might want to store this separately
            received = row['received_chunks']
            total = row['total_chunks']
            missing = list(range(received, total))

            progress = DownloadProgress(
                totalChunks=total,
                receivedChunks=received,
                missingChunks=missing,
                bytesReceived=row['bytes_received'],
                totalBytes=row['file_size'] or 0,
                percentComplete=row['percent_complete']
            )

        return FileDownloadStatus(
            requestId=row['request_id'],
            fileHash=row['file_hash'],
            fileName=row['file_name'],
            fileSize=row['file_size'],
            status=DownloadStatus(row['status']),
            manifestReceived=bool(row['manifest_received']),
            progress=progress,
            startedAt=datetime.fromisoformat(row['started_at']),
            completedAt=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            errorMessage=row['error_message'],
            outputPath=row['output_path']
        )
