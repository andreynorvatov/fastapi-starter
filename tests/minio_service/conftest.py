"""Fixtures for Minio service tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from src.minio_service.schemas import (
    MinioObjectResponse,
    MinioListResponse,
    MinioBucketResponse,
)
from src.minio_service.service import MinioService


@pytest.fixture
def mock_minio_client():
    """Mock Minio client."""
    with patch("src.minio_service.client.minio_client") as mock:
        yield mock


@pytest.fixture
def sample_object_response() -> MinioObjectResponse:
    """Sample object response."""
    return MinioObjectResponse(
        bucket_name="test-bucket",
        object_name="test/file.txt",
        size=1024,
        last_modified=datetime.now(timezone.utc),
        etag="abc123",
        content_type="text/plain",
        metadata={"key": "value"},
    )


@pytest.fixture
def sample_list_response() -> MinioListResponse:
    """Sample list response."""
    obj1 = MinioObjectResponse(
        bucket_name="test-bucket",
        object_name="file1.txt",
        size=512,
        last_modified=datetime.now(timezone.utc),
        etag="def456",
    )
    obj2 = MinioObjectResponse(
        bucket_name="test-bucket",
        object_name="file2.txt",
        size=1024,
        last_modified=datetime.now(timezone.utc),
        etag="ghi789",
    )
    return MinioListResponse(
        bucket_name="test-bucket",
        prefix=None,
        objects=[obj1, obj2],
        count=2,
    )


@pytest.fixture
def minio_service(mock_minio_client) -> MinioService:
    """Create service with mocked client."""
    return MinioService()
