"""API routes for Minio service."""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response
from starlette import status
from .service import MinioService, minio_service
from .schemas import (
    MinioBucketCreate,
    MinioObjectResponse,
    MinioListResponse,
    MinioPresignedUrlResponse,
    MinioBucketResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_minio_service() -> MinioService:
    """Dependency for MinioService."""
    return minio_service


@router.post(
    "/buckets",
    response_model=MinioBucketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create bucket",
    description="Create a new bucket in Minio storage.",
)
async def create_bucket(
    bucket_data: MinioBucketCreate,
    service: Annotated[MinioService, Depends(get_minio_service)],
) -> MinioBucketResponse:
    """Create a new bucket."""
    try:
        return await service.create_bucket(bucket_data.bucket_name)
    except Exception as e:
        logger.error("Failed to create bucket", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bucket: {str(e)}"
        )


@router.post(
    "/upload",
    response_model=MinioObjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file",
    description="Upload a file to Minio storage. By default, a unique UUID name is generated and original filename is preserved in metadata.",
)
async def upload_file(
    service: Annotated[MinioService, Depends(get_minio_service)],
    bucket_name: str = Form(..., description="Bucket name"),
    object_name: str | None = Form(
        None,
        description="Optional object name/path. If provided, be aware it may cause file overwrites. If not provided, a unique UUID name is generated."
    ),
    preserve_filename: bool = Form(
        True,
        description="If True, original filename is preserved in metadata (recommended)"
    ),
    file: UploadFile = File(..., description="File to upload"),
) -> MinioObjectResponse:
    """Upload file to Minio.
    
    - By default, a unique UUID-based name is generated, preventing overwrites.
    - By default, the original filename is stored in metadata (preserve_filename=True).
    - If you explicitly provide object_name, files with the same name will overwrite each other.
    """
    try:
        # Warn if object_name is explicitly provided
        if object_name is not None:
            logger.warning(
                "Custom object_name provided - risk of file overwrite",
                extra={"bucket": bucket_name, "object_name": object_name}
            )
        
        file_data = await file.read()
        content_type = file.content_type or None
        original_filename = file.filename
        
        return await service.upload_file(
            bucket_name=bucket_name,
            object_name=object_name,
            file_data=file_data,
            content_type=content_type,
            original_filename=original_filename,
            preserve_filename=preserve_filename,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Failed to upload file",
            extra={"bucket": bucket_name, "object": object_name, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get(
    "/download/{bucket_name}/{object_name:path}",
    summary="Download file",
    description="Download a file from Minio storage.",
)
async def download_file(
    bucket_name: str,
    object_name: str,
    service: Annotated[MinioService, Depends(get_minio_service)],
) -> Response:
    """Download file from Minio."""
    try:
        file_data = await service.download_file(bucket_name, object_name)
        return Response(content=file_data, media_type="application/octet-stream")
    except Exception as e:
        logger.error(
            "Failed to download file",
            extra={"bucket": bucket_name, "object": object_name, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {str(e)}"
        )


@router.delete(
    "/{bucket_name}/{object_name:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete file",
    description="Delete a file from Minio storage.",
)
async def delete_file(
    bucket_name: str,
    object_name: str,
    service: Annotated[MinioService, Depends(get_minio_service)],
) -> None:
    """Delete file from Minio."""
    try:
        await service.delete_file(bucket_name, object_name)
    except Exception as e:
        logger.error(
            "Failed to delete file",
            extra={
                "bucket": bucket_name,
                "object": object_name,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get(
    "/objects/{bucket_name}/{object_name:path}",
    response_model=MinioObjectResponse,
    summary="Get object metadata",
    description="Get metadata for a specific object.",
)
async def get_object(
    bucket_name: str,
    object_name: str,
    service: Annotated[MinioService, Depends(get_minio_service)],
) -> MinioObjectResponse:
    """Get object metadata."""
    try:
        return await service.get_object(bucket_name, object_name)
    except Exception as e:
        logger.error(
            "Failed to get object",
            extra={"bucket": bucket_name, "object": object_name, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Object not found: {str(e)}"
        )


@router.get(
    "/objects/{bucket_name}",
    response_model=MinioListResponse,
    summary="List objects",
    description="List objects in a bucket with optional prefix filter.",
)
async def list_objects(
    bucket_name: str,
    service: Annotated[MinioService, Depends(get_minio_service)],
    prefix: str | None = Query(None, description="Prefix filter for objects"),
) -> MinioListResponse:
    """List objects in bucket."""
    try:
        return await service.list_objects(bucket_name, prefix=prefix)
    except Exception as e:
        logger.error(
            "Failed to list objects",
            extra={"bucket": bucket_name, "prefix": prefix, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list objects: {str(e)}"
        )


@router.get(
    "/presigned/upload/{bucket_name}/{object_name:path}",
    response_model=MinioPresignedUrlResponse,
    summary="Get upload URL",
    description="Generate presigned URL for uploading a file directly to Minio.",
)
async def get_upload_url(
    bucket_name: str,
    object_name: str,
    service: Annotated[MinioService, Depends(get_minio_service)],
    expires: int = Query(3600, ge=1, le=604800, description="Expiration in seconds"),
) -> MinioPresignedUrlResponse:
    """Generate presigned upload URL."""
    try:
        return await service.get_upload_url(
            bucket_name=bucket_name,
            object_name=object_name,
            expires=expires,
        )
    except Exception as e:
        logger.error(
            "Failed to generate upload URL",
            extra={"bucket": bucket_name, "object": object_name, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate upload URL: {str(e)}"
        )


@router.get(
    "/presigned/download/{bucket_name}/{object_name:path}",
    response_model=MinioPresignedUrlResponse,
    summary="Get download URL",
    description="Generate presigned URL for downloading a file directly from Minio.",
)
async def get_download_url(
    bucket_name: str,
    object_name: str,
    service: Annotated[MinioService, Depends(get_minio_service)],
    expires: int = Query(3600, ge=1, le=604800, description="Expiration in seconds"),
) -> MinioPresignedUrlResponse:
    """Generate presigned download URL."""
    try:
        return await service.get_download_url(
            bucket_name=bucket_name,
            object_name=object_name,
            expires=expires,
        )
    except Exception as e:
        logger.error(
            "Failed to generate download URL",
            extra={"bucket": bucket_name, "object": object_name, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )
