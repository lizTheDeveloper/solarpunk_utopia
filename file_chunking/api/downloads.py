"""
Downloads API Endpoints

Request files and track download progress.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models import FileDownloadStatus, DownloadStatus
from ..database import DownloadRepository
from ..services import ChunkRequestService, ChunkStorageService, ReassemblyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/downloads", tags=["downloads"])


class DownloadRequest(BaseModel):
    """Request to download a file"""
    fileHash: str
    outputPath: str
    priority: int = 5


class DownloadStatusResponse(BaseModel):
    """Download status response"""
    requestId: str
    fileHash: str
    fileName: Optional[str]
    status: str
    totalChunks: int
    receivedChunks: int
    percentComplete: float
    errorMessage: Optional[str] = None


@router.post("/request", response_model=DownloadStatusResponse)
async def request_file_download(request: DownloadRequest):
    """
    Request a file download.

    This initiates the download process:
    1. Request manifest if needed
    2. Request missing chunks
    3. Track progress

    Args:
        request: DownloadRequest

    Returns:
        DownloadStatusResponse with request ID
    """
    try:
        # Initialize services
        from app.services import CryptoService, BundleService

        crypto_service = CryptoService()
        bundle_service = BundleService(crypto_service)
        chunk_storage = ChunkStorageService()
        chunk_request_service = ChunkRequestService(bundle_service, chunk_storage)

        # Request file
        request_id = await chunk_request_service.request_file(
            request.fileHash,
            request.outputPath,
            request.priority
        )

        # Get download status
        download_status = await chunk_request_service.get_download_status(request_id)

        if not download_status:
            raise HTTPException(status_code=500, detail="Failed to create download request")

        return DownloadStatusResponse(
            requestId=download_status.requestId,
            fileHash=download_status.fileHash,
            fileName=download_status.fileName,
            status=download_status.status.value,
            totalChunks=download_status.progress.totalChunks if download_status.progress else 0,
            receivedChunks=download_status.progress.receivedChunks if download_status.progress else 0,
            percentComplete=download_status.get_progress_percentage(),
            errorMessage=download_status.errorMessage
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to request download: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{request_id}", response_model=DownloadStatusResponse)
async def get_download_status(request_id: str):
    """
    Get download status.

    Args:
        request_id: Download request ID

    Returns:
        DownloadStatusResponse
    """
    try:
        download_status = await DownloadRepository.get(request_id)

        if not download_status:
            raise HTTPException(status_code=404, detail="Download not found")

        return DownloadStatusResponse(
            requestId=download_status.requestId,
            fileHash=download_status.fileHash,
            fileName=download_status.fileName,
            status=download_status.status.value,
            totalChunks=download_status.progress.totalChunks if download_status.progress else 0,
            receivedChunks=download_status.progress.receivedChunks if download_status.progress else 0,
            percentComplete=download_status.get_progress_percentage(),
            errorMessage=download_status.errorMessage
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get download status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[DownloadStatusResponse])
async def list_downloads(active_only: bool = True, limit: int = 100):
    """
    List downloads.

    Args:
        active_only: Only show active downloads
        limit: Maximum number to return

    Returns:
        List of DownloadStatusResponse
    """
    try:
        if active_only:
            downloads = await DownloadRepository.get_active_downloads(limit)
        else:
            # TODO: Implement list all downloads
            downloads = await DownloadRepository.get_active_downloads(limit)

        responses = []

        for download in downloads:
            responses.append(DownloadStatusResponse(
                requestId=download.requestId,
                fileHash=download.fileHash,
                fileName=download.fileName,
                status=download.status.value,
                totalChunks=download.progress.totalChunks if download.progress else 0,
                receivedChunks=download.progress.receivedChunks if download.progress else 0,
                percentComplete=download.get_progress_percentage(),
                errorMessage=download.errorMessage
            ))

        return responses

    except Exception as e:
        logger.error(f"Failed to list downloads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{request_id}/reassemble")
async def reassemble_download(request_id: str):
    """
    Reassemble a completed download.

    Args:
        request_id: Download request ID

    Returns:
        Success message with output path
    """
    try:
        download_status = await DownloadRepository.get(request_id)

        if not download_status:
            raise HTTPException(status_code=404, detail="Download not found")

        if download_status.status != DownloadStatus.REASSEMBLING:
            if download_status.progress and not download_status.progress.is_complete():
                raise HTTPException(status_code=400, detail="Download not complete")

        # Initialize services
        chunk_storage = ChunkStorageService()
        reassembly_service = ReassemblyService(chunk_storage)

        # Reassemble file
        success, error = await reassembly_service.reassemble_file(
            download_status.fileHash,
            download_status.outputPath
        )

        if not success:
            download_status.mark_failed(f"Reassembly failed: {error}")
            await DownloadRepository.update(download_status)
            raise HTTPException(status_code=500, detail=f"Reassembly failed: {error}")

        # Mark download as completed
        download_status.mark_completed(download_status.outputPath)
        await DownloadRepository.update(download_status)

        logger.info(f"Reassembled download {request_id}")

        return {
            "message": "File reassembled successfully",
            "outputPath": download_status.outputPath
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reassemble download: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{request_id}")
async def cancel_download(request_id: str):
    """
    Cancel a download.

    Args:
        request_id: Download request ID

    Returns:
        Success message
    """
    try:
        from app.services import CryptoService, BundleService

        crypto_service = CryptoService()
        bundle_service = BundleService(crypto_service)
        chunk_storage = ChunkStorageService()
        chunk_request_service = ChunkRequestService(bundle_service, chunk_storage)

        success = await chunk_request_service.cancel_download(request_id)

        if not success:
            raise HTTPException(status_code=404, detail="Download not found")

        return {"message": f"Download {request_id} cancelled"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel download: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
