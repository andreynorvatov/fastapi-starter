"""Tests for Minio service schemas."""

import pytest
from datetime import datetime, timezone
from src.minio_service.schemas import (
    MinioObjectCreate,
    MinioObjectUpdate,
    MinioObjectResponse,
    MinioListResponse,
    MinioPresignedUrlResponse,
    MinioDeleteRequest,
    MinioBucketCreate,
    MinioBucketResponse,
)


class TestMinioObjectCreate:
    """Tests for MinioObjectCreate schema."""
    
    def test_valid_data(self) -> None:
        """Test with valid data."""
        data = MinioObjectCreate(
            bucket_name="test-bucket",
            object_name="path/to/file.txt",
            content_type="text/plain"
        )
        assert data.bucket_name == "test-bucket"
        assert data.object_name == "path/to/file.txt"
        assert data.content_type == "text/plain"
    
    def test_minimal_data(self) -> None:
        """Test with minimal data."""
        data = MinioObjectCreate(
            bucket_name="bucket",
            object_name="file.txt"
        )
        assert data.content_type is None
    
    def test_invalid_bucket_name(self) -> None:
        """Test with invalid bucket name."""
        with pytest.raises(ValueError):
            MinioObjectCreate(bucket_name="", object_name="file.txt")
        
        with pytest.raises(ValueError):
            MinioObjectCreate(bucket_name="a" * 64, object_name="file.txt")


class TestMinioObjectUpdate:
    """Tests for MinioObjectUpdate schema."""
    
    def test_valid_data(self) -> None:
        """Test with valid data."""
        data = MinioObjectUpdate(metadata={"key": "value"})
        assert data.metadata == {"key": "value"}
    
    def test_empty_metadata(self) -> None:
        """Test with empty metadata."""
        data = MinioObjectUpdate()
        assert data.metadata == {}


class TestMinioObjectResponse:
    """Tests for MinioObjectResponse schema."""
    
    def test_valid_data(self) -> None:
        """Test with valid data."""
        now = datetime.now(timezone.utc)
        data = MinioObjectResponse(
            bucket_name="test-bucket",
            object_name="file.txt",
            original_filename="report.pdf",
            size=1024,
            last_modified=now,
            etag="abc123",
            content_type="text/plain",
            metadata={"key": "value"},
        )
        assert data.bucket_name == "test-bucket"
        assert data.size == 1024
        assert data.last_modified == now
        assert data.original_filename == "report.pdf"
    
    def test_from_attributes(self) -> None:
        """Test from attributes."""
        # Simulate object with attributes
        class Obj:
            bucket_name = "bucket"
            object_name = "file.txt"
            size = 512
            last_modified = datetime.now(timezone.utc)
            etag = "xyz789"
            content_type = "text/plain"
            metadata = {}
            original_filename = None
        
        data = MinioObjectResponse.model_validate(Obj())
        assert data.bucket_name == "bucket"
        assert data.size == 512
        assert data.original_filename is None


class TestMinioListResponse:
    """Tests for MinioListResponse schema."""
    
    def test_valid_data(self) -> None:
        """Test with valid data."""
        obj = MinioObjectResponse(
            bucket_name="bucket",
            object_name="file.txt",
            original_filename="document.pdf",
            size=1024,
            last_modified=datetime.now(timezone.utc),
            etag="abc123",
        )
        data = MinioListResponse(
            bucket_name="bucket",
            objects=[obj],
            count=1,
        )
        assert data.count == 1
        assert len(data.objects) == 1
        assert data.objects[0].original_filename == "document.pdf"


class TestMinioPresignedUrlResponse:
    """Tests for MinioPresignedUrlResponse schema."""
    
    def test_valid_data(self) -> None:
        """Test with valid data."""
        data = MinioPresignedUrlResponse(
            url="https://example.com/presigned",
            expires_in=3600,
            http_method="GET",
            bucket_name="bucket",
            object_name="file.txt",
        )
        assert data.url.startswith("https://")
        assert data.expires_in == 3600
        assert data.http_method in ["GET", "PUT"]


class TestMinioDeleteRequest:
    """Tests for MinioDeleteRequest schema."""
    
    def test_valid_data(self) -> None:
        """Test with valid data."""
        data = MinioDeleteRequest(
            bucket_name="bucket",
            object_name="file.txt",
        )
        assert data.bucket_name == "bucket"
        assert data.object_name == "file.txt"


class TestMinioBucketCreate:
    """Tests for MinioBucketCreate schema."""
    
    def test_valid_data(self) -> None:
        """Test with valid data."""
        data = MinioBucketCreate(bucket_name="new-bucket")
        assert data.bucket_name == "new-bucket"


class TestMinioBucketResponse:
    """Tests for MinioBucketResponse schema."""
    
    def test_valid_data(self) -> None:
        """Test with valid data."""
        data = MinioBucketResponse(name="bucket", created=True)
        assert data.name == "bucket"
        assert data.created is True
