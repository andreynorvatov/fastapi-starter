"""Pydantic schemas for Minio service."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class MinioObjectCreate(BaseModel):
    """Schema for creating/uploading an object."""
    
    bucket_name: str = Field(
        ...,
        min_length=1,
        max_length=63,
        description="Bucket name (1-63 characters)"
    )
    object_name: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Object name/path"
    )
    content_type: str | None = Field(
        default=None,
        description="MIME type of the file"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bucket_name": "uploads",
                "object_name": "documents/file.pdf",
                "content_type": "application/pdf"
            }
        }
    )


class MinioObjectUpdate(BaseModel):
    """Schema for updating object metadata."""
    
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Custom metadata key-value pairs"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metadata": {
                    "author": "John Doe",
                    "description": "Important document"
                }
            }
        }
    )


class MinioObjectResponse(BaseModel):
    """Schema for object response."""
    
    bucket_name: str
    object_name: str
    original_filename: str | None = Field(
        default=None,
        description="Original filename provided by user (if preserved)"
    )
    size: int = Field(..., ge=0, description="Size in bytes")
    last_modified: datetime
    etag: str
    content_type: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "bucket_name": "uploads",
                "object_name": "a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf",
                "original_filename": "report.pdf",
                "size": 1024000,
                "last_modified": "2025-02-13T07:00:00Z",
                "etag": "abc123def456",
                "content_type": "application/pdf",
                "metadata": {"original_filename": "report.pdf"}
            }
        }
    )


class MinioListResponse(BaseModel):
    """Schema for list of objects."""
    
    bucket_name: str
    prefix: str | None = None
    objects: list[MinioObjectResponse] = Field(default_factory=list)
    count: int = Field(..., ge=0, description="Total number of objects")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bucket_name": "uploads",
                "prefix": "documents/",
                "objects": [],
                "count": 0
            }
        }
    )


class MinioPresignedUrlResponse(BaseModel):
    """Schema for presigned URL response."""
    
    url: str = Field(..., description="Presigned URL")
    expires_in: int = Field(..., description="Expiration time in seconds")
    http_method: str = Field(..., description="HTTP method (GET or PUT)")
    bucket_name: str
    object_name: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://minio.example.com/...",
                "expires_in": 3600,
                "http_method": "GET",
                "bucket_name": "uploads",
                "object_name": "documents/file.pdf"
            }
        }
    )


class MinioDeleteRequest(BaseModel):
    """Schema for delete request."""
    
    bucket_name: str = Field(..., min_length=1)
    object_name: str = Field(..., min_length=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bucket_name": "uploads",
                "object_name": "documents/file.pdf"
            }
        }
    )


class MinioBucketCreate(BaseModel):
    """Schema for creating a bucket."""
    
    bucket_name: str = Field(
        ...,
        min_length=1,
        max_length=63,
        description="Bucket name"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bucket_name": "uploads"
            }
        }
    )


class MinioBucketResponse(BaseModel):
    """Schema for bucket response."""
    
    name: str
    created: bool = Field(
        ...,
        description="Whether bucket was created or already existed"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "uploads",
                "created": True
            }
        }
    )
