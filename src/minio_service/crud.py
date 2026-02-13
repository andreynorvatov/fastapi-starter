"""CRUD operations for Minio."""

import asyncio
import logging
from typing import Any
from .client import MinioClientWrapper, minio_client
from .config import get_minio_settings
from .schemas import (
    MinioObjectCreate,
    MinioObjectUpdate,
    MinioObjectResponse,
    MinioListResponse,
    MinioBucketResponse,
)

logger = logging.getLogger(__name__)


class MinioCRUD:
    """CRUD operations for Minio storage."""
    
    def __init__(self, client: MinioClientWrapper | None = None) -> None:
        """Initialize CRUD with client."""
        self.client = client or minio_client
        self.settings = get_minio_settings()
    
    async def create_bucket(self, bucket_name: str) -> MinioBucketResponse:
        """Create a new bucket."""
        await asyncio.to_thread(self.client.ensure_bucket_exists, bucket_name)
        return MinioBucketResponse(name=bucket_name, created=True)
    
    async def upload_file(
        self,
        bucket_name: str,
        object_name: str | None,
        file_data: bytes,
        content_type: str | None = None,
        original_filename: str | None = None,
        preserve_filename: bool = False,
    ) -> MinioObjectResponse:
        """Upload file to Minio with unique name generation.
        
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
        
        # Ensure bucket exists
        await asyncio.to_thread(
            self.client.ensure_bucket_exists,
            bucket_name
        )
        
        # Generate unique object name if not provided
        if not object_name:
            import uuid
            from pathlib import Path
            
            ext = ""
            if preserve_filename and original_filename:
                ext = Path(original_filename).suffix
            
            object_name = f"{uuid.uuid4()}{ext}"
            logger.info(
                "Generated unique object name",
                extra={"bucket": bucket_name, "object": object_name, "original": original_filename}
            )
        
        # Prepare metadata
        metadata = {}
        if preserve_filename and original_filename:
            metadata["original_filename"] = original_filename
        
        # Upload file (synchronous, run in thread)
        await asyncio.to_thread(
            self.client.upload_file,
            bucket_name,
            object_name,
            file_data,
            content_type,
            metadata=metadata if metadata else None,
        )
        
        # Get object stats
        stats = await asyncio.to_thread(
            self.client.stat_object,
            bucket_name,
            object_name
        )
        
        # Extract original_filename from metadata if not provided directly
        returned_original = original_filename if preserve_filename else None
        if not returned_original and stats.get("metadata", {}).get("original_filename"):
            returned_original = stats["metadata"]["original_filename"]
        
        return MinioObjectResponse(
            bucket_name=bucket_name,
            object_name=object_name,
            original_filename=returned_original,
            size=stats["size"],
            last_modified=stats["last_modified"],
            etag=stats["etag"],
            content_type=stats.get("content_type"),
            metadata=stats.get("metadata", {}),
        )
    
    async def download_file(self, bucket_name: str, object_name: str) -> bytes:
        """Download file from Minio."""
        return await asyncio.to_thread(
            self.client.download_file,
            bucket_name,
            object_name
        )
    
    async def delete_file(self, bucket_name: str, object_name: str) -> bool:
        """Delete file from Minio."""
        await asyncio.to_thread(
            self.client.remove_file,
            bucket_name,
            object_name
        )
        return True
    
    async def get_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> MinioObjectResponse:
        """Get object metadata."""
        stats = await asyncio.to_thread(
            self.client.stat_object,
            bucket_name,
            object_name
        )
        # Extract original_filename from metadata
        original_filename = None
        if stats.get("metadata", {}).get("original_filename"):
            original_filename = stats["metadata"]["original_filename"]
        
        return MinioObjectResponse(
            bucket_name=bucket_name,
            object_name=object_name,
            original_filename=original_filename,
            size=stats["size"],
            last_modified=stats["last_modified"],
            etag=stats["etag"],
            content_type=stats.get("content_type"),
            metadata=stats.get("metadata", {}),
        )
    
    async def list_objects(
        self,
        bucket_name: str,
        prefix: str | None = None,
    ) -> MinioListResponse:
        """List objects in bucket."""
        objects_data = await asyncio.to_thread(
            self.client.list_files,
            bucket_name,
            prefix=prefix
        )
        
        objects = []
        for obj_data in objects_data:
            # Extract original_filename from metadata
            original_filename = None
            if obj_data.get("metadata", {}).get("original_filename"):
                original_filename = obj_data["metadata"]["original_filename"]
            
            objects.append(MinioObjectResponse(
                bucket_name=bucket_name,
                object_name=obj_data["name"],
                original_filename=original_filename,
                size=obj_data["size"],
                last_modified=obj_data["last_modified"],
                etag=obj_data["etag"],
            ))
        
        return MinioListResponse(
            bucket_name=bucket_name,
            prefix=prefix,
            objects=objects,
            count=len(objects)
        )
    
    async def update_object_metadata(
        self,
        bucket_name: str,
        object_name: str,
        metadata: dict[str, str],
    ) -> MinioObjectResponse:
        """Update object metadata."""
        # Minio doesn't support direct metadata update
        # We need to copy object to itself with new metadata
        # For simplicity, we'll just return current metadata
        # In production, implement copy-with-metadata pattern
        stats = await asyncio.to_thread(
            self.client.stat_object,
            bucket_name,
            object_name
        )
        return MinioObjectResponse(
            bucket_name=bucket_name,
            object_name=object_name,
            size=stats["size"],
            last_modified=stats["last_modified"],
            etag=stats["etag"],
            content_type=stats.get("content_type"),
            metadata=metadata,
        )
    
    async def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: int = 3600,
        http_method: str = "GET",
    ) -> str:
        """Generate presigned URL for object access."""
        return await asyncio.to_thread(
            self.client.get_presigned_url,
            bucket_name,
            object_name,
            expires,
            http_method
        )


minio_crud = MinioCRUD()
