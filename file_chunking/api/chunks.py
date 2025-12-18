"""
Chunks API Endpoints

Low-level chunk operations.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from ..models import ChunkMetadata
from ..database import ChunkRepository
from ..services import ChunkStorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chunks", tags=["chunks"])


class ChunkInfo(BaseModel):
    """Chunk information"""
    chunkHash: str
    chunkIndex: int
    chunkSize: int
    fileHash: str
    status: str
    storagePath: str | None


@router.get("/{chunk_hash}", response_model=ChunkInfo)
async def get_chunk_info(chunk_hash: str):
    """
    Get chunk information.

    Args:
        chunk_hash: Hash of chunk

    Returns:
        ChunkInfo
    """
    try:
        chunk = await ChunkRepository.get(chunk_hash)

        if chunk is None:
            raise HTTPException(status_code=404, detail="Chunk not found")

        return ChunkInfo(
            chunkHash=chunk.chunkHash,
            chunkIndex=chunk.chunkIndex,
            chunkSize=chunk.chunkSize,
            fileHash=chunk.fileHash,
            status=chunk.status.value,
            storagePath=chunk.storagePath
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chunk info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chunk_hash}/data")
async def get_chunk_data(chunk_hash: str):
    """
    Get chunk data.

    Args:
        chunk_hash: Hash of chunk

    Returns:
        Raw chunk data as bytes
    """
    try:
        chunk_storage = ChunkStorageService()
        chunk_data = await chunk_storage.retrieve_chunk(chunk_hash)

        if chunk_data is None:
            raise HTTPException(status_code=404, detail="Chunk not found")

        return Response(content=chunk_data, media_type="application/octet-stream")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chunk data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/{file_hash}", response_model=List[ChunkInfo])
async def list_file_chunks(file_hash: str):
    """
    List chunks for a file.

    Args:
        file_hash: Hash of file

    Returns:
        List of ChunkInfo
    """
    try:
        chunks = await ChunkRepository.get_by_file(file_hash)

        chunk_infos = []

        for chunk in chunks:
            chunk_infos.append(ChunkInfo(
                chunkHash=chunk.chunkHash,
                chunkIndex=chunk.chunkIndex,
                chunkSize=chunk.chunkSize,
                fileHash=chunk.fileHash,
                status=chunk.status.value,
                storagePath=chunk.storagePath
            ))

        return chunk_infos

    except Exception as e:
        logger.error(f"Failed to list chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chunk_hash}/verify")
async def verify_chunk(chunk_hash: str):
    """
    Verify chunk integrity.

    Args:
        chunk_hash: Hash of chunk to verify

    Returns:
        Verification result
    """
    try:
        chunk_storage = ChunkStorageService()
        is_valid = await chunk_storage.verify_chunk_integrity(chunk_hash)

        return {
            "chunkHash": chunk_hash,
            "isValid": is_valid
        }

    except Exception as e:
        logger.error(f"Failed to verify chunk: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
