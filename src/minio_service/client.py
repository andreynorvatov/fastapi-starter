"""Minio client wrapper."""

import logging
from typing import Any
from minio import Minio as MinioClient
from minio.error import S3Error
from .config import get_minio_settings

logger = logging.getLogger(__name__)


class MinioClientWrapper:
    """Wrapper for Minio client with error handling."""
    
    def __init__(self) -> None:
        """Initialize Minio client."""
        self._client: MinioClient | None = None
        self._settings = get_minio_settings()
    
    @property
    def client(self) -> MinioClient:
        """Get or create Minio client instance."""
        if self._client is None:
            config = self._settings.client_config
            self._client = MinioClient(**config)
            logger.info(
                "Minio client initialized",
                extra={"endpoint": config["endpoint"]}
            )
        return self._client
    
    def ensure_bucket_exists(self, bucket_name: str) -> None:
        """Ensure bucket exists, create if not."""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info("Bucket created", extra={"bucket": bucket_name})
        except S3Error as e:
            logger.error("Failed to ensure bucket", extra={"bucket": bucket_name, "error": str(e)})
            raise
    
    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_data: bytes,
        content_type: str | None = None,
        length: int | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Upload file to Minio.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object (file) in the bucket
            file_data: File content as bytes
            content_type: MIME type of the file
            length: Length of the file in bytes (calculated if not provided)
            metadata: Custom metadata to attach to the object
        """
        try:
            from io import BytesIO
            file_stream = BytesIO(file_data)
            file_length = length or len(file_data)
            
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=file_stream,
                length=file_length,
                content_type=content_type,
                metadata=metadata,
            )
            logger.info(
                "File uploaded",
                extra={"bucket": bucket_name, "object": object_name}
            )
        except S3Error as e:
            logger.error(
                "Failed to upload file",
                extra={"bucket": bucket_name, "object": object_name, "error": str(e)}
            )
            raise
    
    def download_file(self, bucket_name: str, object_name: str) -> bytes:
        """Download file from Minio."""
        try:
            response = self.client.get_object(bucket_name, object_name)
            try:
                data = response.read()
                logger.info(
                    "File downloaded",
                    extra={"bucket": bucket_name, "object": object_name}
                )
                return data
            finally:
                response.close()
                response.release_conn()
        except S3Error as e:
            logger.error(
                "Failed to download file",
                extra={"bucket": bucket_name, "object": object_name, "error": str(e)}
            )
            raise
    
    def remove_file(self, bucket_name: str, object_name: str) -> None:
        """Remove file from Minio."""
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(
                "File removed",
                extra={"bucket": bucket_name, "object": object_name}
            )
        except S3Error as e:
            logger.error(
                "Failed to remove file",
                extra={"bucket": bucket_name, "object": object_name, "error": str(e)}
            )
            raise
    
    def list_files(
        self,
        bucket_name: str,
        prefix: str | None = None,
        recursive: bool = True,
    ) -> list[dict[str, Any]]:
        """List files in bucket."""
        try:
            objects = self.client.list_objects(
                bucket_name,
                prefix=prefix,
                recursive=recursive,
            )
            
            result = []
            for obj in objects:
                result.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag,
                })
            return result
        except S3Error as e:
            logger.error(
                "Failed to list files",
                extra={"bucket": bucket_name, "prefix": prefix, "error": str(e)}
            )
            raise
    
    def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: int = 3600,
        http_method: str = "GET",
    ) -> str:
        """Generate presigned URL for object."""
        try:
            if http_method.upper() == "GET":
                url = self.client.presigned_get_object(
                    bucket_name, object_name, expires
                )
            elif http_method.upper() == "PUT":
                url = self.client.presigned_put_object(
                    bucket_name, object_name, expires
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {http_method}")
            
            logger.info(
                "Presigned URL generated",
                extra={
                    "bucket": bucket_name,
                    "object": object_name,
                    "method": http_method,
                }
            )
            return url
        except S3Error as e:
            logger.error(
                "Failed to generate presigned URL",
                extra={"bucket": bucket_name, "object": object_name, "error": str(e)}
            )
            raise
    
    def stat_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> dict[str, Any]:
        """Get object metadata."""
        try:
            stat = self.client.stat_object(bucket_name, object_name)
            return {
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "metadata": stat.metadata,
            }
        except S3Error as e:
            logger.error(
                "Failed to get object stats",
                extra={"bucket": bucket_name, "object": object_name, "error": str(e)}
            )
            raise


minio_client = MinioClientWrapper()
