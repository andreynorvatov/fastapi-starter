"""Service layer for Minio operations."""

import logging
from typing import Any
from .crud import MinioCRUD
from .schemas import (
    MinioObjectCreate,
    MinioObjectResponse,
    MinioListResponse,
    MinioPresignedUrlResponse,
    MinioBucketResponse,
)

logger = logging.getLogger(__name__)


class MinioService:
    """Service for Minio operations with business logic."""
    
    def __init__(self, crud: MinioCRUD | None = None) -> None:
        """Initialize service with CRUD operations."""
        self.crud = crud or MinioCRUD()
    
    async def create_bucket(self, bucket_name: str) -> MinioBucketResponse:
        """Create a new bucket."""
        return await self.crud.create_bucket(bucket_name)
    
    async def upload_file(
        self,
        bucket_name: str,
        object_name: str | None = None,
        file_data: bytes | None = None,
        content_type: str | None = None,
        original_filename: str | None = None,
        preserve_filename: bool = False,
    ) -> MinioObjectResponse:
        """Upload file to Minio.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Optional object name. If None, generates UUID.
            file_data: File content as bytes
            content_type: MIME type of the file
            original_filename: Original filename from user
            preserve_filename: If True, saves original_filename in metadata
            
        Returns:
            MinioObjectResponse with object metadata
        """
        if not file_data:
            raise ValueError("File data cannot be empty")
        
        if object_name and len(object_name) > 1024:
            raise ValueError("Object name too long (max 1024 characters)")
        
        return await self.crud.upload_file(
            bucket_name=bucket_name,
            object_name=object_name,
            file_data=file_data,
            content_type=content_type,
            original_filename=original_filename,
            preserve_filename=preserve_filename,
        )
    
    async def download_file(self, bucket_name: str, object_name: str) -> bytes:
        """Download file from Minio."""
        return await self.crud.download_file(bucket_name, object_name)
    
    async def delete_file(self, bucket_name: str, object_name: str) -> bool:
        """Delete file from Minio."""
        return await self.crud.delete_file(bucket_name, object_name)
    
    async def get_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> MinioObjectResponse:
        """Get object metadata."""
        return await self.crud.get_object(bucket_name, object_name)
    
    async def list_objects(
        self,
        bucket_name: str,
        prefix: str | None = None,
    ) -> MinioListResponse:
        """List objects in bucket."""
        return await self.crud.list_objects(bucket_name, prefix=prefix)
    
    async def get_download_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: int = 3600,
    ) -> MinioPresignedUrlResponse:
        """Generate presigned download URL."""
        url = await self.crud.get_presigned_url(
            bucket_name=bucket_name,
            object_name=object_name,
            expires=expires,
            http_method="GET",
        )
        return MinioPresignedUrlResponse(
            url=url,
            expires_in=expires,
            http_method="GET",
            bucket_name=bucket_name,
            object_name=object_name,
        )
    
    async def get_upload_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: int = 3600,
    ) -> MinioPresignedUrlResponse:
        """Generate presigned upload URL."""
        url = await self.crud.get_presigned_url(
            bucket_name=bucket_name,
            object_name=object_name,
            expires=expires,
            http_method="PUT",
        )
        return MinioPresignedUrlResponse(
            url=url,
            expires_in=expires,
            http_method="PUT",
            bucket_name=bucket_name,
            object_name=object_name,
        )


minio_service = MinioService()
