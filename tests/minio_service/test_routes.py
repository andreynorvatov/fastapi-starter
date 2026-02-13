"""Tests for Minio API routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from src.main import app
from src.minio_service.schemas import (
    MinioObjectResponse,
    MinioListResponse,
    MinioPresignedUrlResponse,
    MinioBucketResponse,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_minio_service():
    """Create mock Minio service."""
    with patch("src.minio_service.routes.minio_service") as mock:
        yield mock


class TestMinioRoutes:
    """Tests for Minio API routes."""
    
    def test_create_bucket(self, client, mock_minio_service):
        """Test create bucket endpoint."""
        mock_minio_service.create_bucket = AsyncMock(
            return_value=MinioBucketResponse(name="test-bucket", created=True)
        )
        
        response = client.post(
            "/minio/buckets",
            json={"bucket_name": "test-bucket"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-bucket"
        assert data["created"] is True
    
    def test_upload_file(self, client, mock_minio_service):
        """Test upload file endpoint."""
        mock_minio_service.upload_file = AsyncMock(return_value=MinioObjectResponse(
            bucket_name="test-bucket",
            object_name="file.txt",
            original_filename="report.pdf",
            size=1024,
            last_modified=datetime.now(timezone.utc).isoformat(),
            etag="abc123",
        ))
        
        response = client.post(
            "/minio/upload",
            data={
                "bucket_name": "test-bucket",
                "object_name": "file.txt",
                "preserve_filename": "true",
            },
            files={"file": ("report.pdf", b"file content", "application/pdf")}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["bucket_name"] == "test-bucket"
        assert data["object_name"] == "file.txt"
        assert data["original_filename"] == "report.pdf"
    
    def test_upload_file_generates_uuid(self, client, mock_minio_service):
        """Test upload file without object_name generates UUID."""
        import uuid
        
        mock_uuid = "12345678-1234-5678-1234-567812345678"
        mock_minio_service.upload_file = AsyncMock(return_value=MinioObjectResponse(
            bucket_name="test-bucket",
            object_name=mock_uuid,
            original_filename="document.pdf",
            size=1024,
            last_modified=datetime.now(timezone.utc).isoformat(),
            etag="abc123",
        ))
        
        with patch("uuid.uuid4", return_value=uuid.UUID(mock_uuid)):
            response = client.post(
                "/minio/upload",
                data={
                    "bucket_name": "test-bucket",
                    "preserve_filename": "true",
                },
                files={"file": ("document.pdf", b"file content", "application/pdf")}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["object_name"] == mock_uuid
        assert data["original_filename"] == "document.pdf"
    
    def test_upload_file_preserves_extension(self, client, mock_minio_service):
        """Test that generated UUID preserves file extension."""
        mock_minio_service.upload_file = AsyncMock(return_value=MinioObjectResponse(
            bucket_name="test-bucket",
            object_name="uuid123456.pdf",
            original_filename="myfile.pdf",
            size=1024,
            last_modified=datetime.now(timezone.utc).isoformat(),
            etag="abc123",
        ))
        
        response = client.post(
            "/minio/upload",
            data={
                "bucket_name": "test-bucket",
                "preserve_filename": "true",
            },
            files={"file": ("myfile.pdf", b"file content", "application/pdf")}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["object_name"].endswith(".pdf")
        assert data["original_filename"] == "myfile.pdf"
    
    def test_upload_file_invalid(self, client, mock_minio_service):
        """Test upload file with invalid data."""
        mock_minio_service.upload_file = AsyncMock(
            side_effect=ValueError("File data cannot be empty")
        )
        
        response = client.post(
            "/minio/upload",
            data={
                "bucket_name": "test-bucket",
            },
            files={"file": ("file.txt", b"", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "File data cannot be empty" in response.json()["detail"]
    
    def test_download_file(self, client, mock_minio_service):
        """Test download file endpoint."""
        mock_minio_service.download_file = AsyncMock(return_value=b"file content")
        
        response = client.get("/minio/download/test-bucket/file.txt")
        
        assert response.status_code == 200
        assert response.content == b"file content"
    
    def test_delete_file(self, client, mock_minio_service):
        """Test delete file endpoint."""
        mock_minio_service.delete_file = AsyncMock(return_value=True)
        
        response = client.delete("/minio/test-bucket/file.txt")
        
        assert response.status_code == 204
    
    def test_get_object(self, client, mock_minio_service):
        """Test get object metadata endpoint."""
        mock_minio_service.get_object = AsyncMock(return_value=MinioObjectResponse(
            bucket_name="test-bucket",
            object_name="file.txt",
            original_filename=None,
            size=1024,
            last_modified=datetime.now(timezone.utc).isoformat(),
            etag="abc123",
        ))
        
        response = client.get("/minio/objects/test-bucket/file.txt")
        
        assert response.status_code == 200
        data = response.json()
        assert data["bucket_name"] == "test-bucket"
        assert data["original_filename"] is None
    
    def test_list_objects(self, client, mock_minio_service):
        """Test list objects endpoint."""
        mock_minio_service.list_objects = AsyncMock(return_value=MinioListResponse(
            bucket_name="test-bucket",
            prefix="docs/",
            objects=[
                MinioObjectResponse(
                    bucket_name="test-bucket",
                    object_name="doc1.pdf",
                    original_filename="document1.pdf",
                    size=1024,
                    last_modified=datetime.now(timezone.utc),
                    etag="abc123",
                ),
                MinioObjectResponse(
                    bucket_name="test-bucket",
                    object_name="doc2.pdf",
                    original_filename=None,
                    size=2048,
                    last_modified=datetime.now(timezone.utc),
                    etag="def456",
                ),
            ],
            count=2,
        ))
        
        response = client.get("/minio/objects/test-bucket", params={"prefix": "docs/"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["bucket_name"] == "test-bucket"
        assert data["prefix"] == "docs/"
        assert data["count"] == 2
        assert data["objects"][0]["original_filename"] == "document1.pdf"
        assert data["objects"][1]["original_filename"] is None
    
    def test_get_upload_url(self, client, mock_minio_service):
        """Test get upload URL endpoint."""
        mock_minio_service.get_upload_url = AsyncMock(return_value=MinioPresignedUrlResponse(
            url="https://example.com/upload",
            expires_in=3600,
            http_method="PUT",
            bucket_name="test-bucket",
            object_name="file.txt",
        ))
        
        response = client.get(
            "/minio/presigned/upload/test-bucket/file.txt",
            params={"expires": 3600}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["http_method"] == "PUT"
        assert "url" in data
    
    def test_get_download_url(self, client, mock_minio_service):
        """Test get download URL endpoint."""
        mock_minio_service.get_download_url = AsyncMock(return_value=MinioPresignedUrlResponse(
            url="https://example.com/download",
            expires_in=3600,
            http_method="GET",
            bucket_name="test-bucket",
            object_name="file.txt",
        ))
        
        response = client.get(
            "/minio/presigned/download/test-bucket/file.txt",
            params={"expires": 3600}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["http_method"] == "GET"
