"""Tests for Minio service."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from src.minio_service.service import MinioService
from src.minio_service.schemas import (
    MinioObjectResponse,
    MinioListResponse,
    MinioPresignedUrlResponse,
    MinioBucketResponse,
)


class TestMinioService:
    """Tests for MinioService."""
    
    @pytest.fixture
    def mock_crud(self):
        """Create mock CRUD with AsyncMock methods."""
        mock = MagicMock()
        mock.create_bucket = AsyncMock(return_value=MinioBucketResponse(name="bucket", created=True))
        mock.upload_file = AsyncMock(return_value=MinioObjectResponse(
            bucket_name="bucket",
            object_name="file.txt",
            original_filename="report.pdf",
            size=1024,
            last_modified=datetime.now(timezone.utc),
            etag="abc123",
        ))
        mock.download_file = AsyncMock(return_value=b"file content")
        mock.delete_file = AsyncMock(return_value=True)
        mock.get_object = AsyncMock(return_value=MinioObjectResponse(
            bucket_name="bucket",
            object_name="file.txt",
            original_filename=None,
            size=1024,
            last_modified=datetime.now(timezone.utc),
            etag="abc123",
        ))
        mock.list_objects = AsyncMock(return_value=MinioListResponse(
            bucket_name="bucket",
            objects=[],
            count=0,
        ))
        mock.get_presigned_url = AsyncMock(return_value="https://example.com/presigned")
        return mock
    
    @pytest.fixture
    def service(self, mock_crud):
        """Create service with mock CRUD."""
        return MinioService(crud=mock_crud)
    
    @pytest.mark.asyncio
    async def test_create_bucket(self, service, mock_crud):
        """Test create bucket."""
        result = await service.create_bucket("bucket")
        assert result.name == "bucket"
        assert result.created is True
        mock_crud.create_bucket.assert_called_once_with("bucket")
    
    @pytest.mark.asyncio
    async def test_upload_file(self, service, mock_crud):
        """Test upload file."""
        file_data = b"test data"
        result = await service.upload_file("bucket", "file.txt", file_data)
        assert result.bucket_name == "bucket"
        assert result.size == 1024
        assert result.original_filename == "report.pdf"
        mock_crud.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_generates_uuid(self):
        """Test upload file without object_name generates UUID."""
        import uuid
        from unittest.mock import patch
        
        mock_crud = MagicMock()
        mock_uuid = "12345678-1234-5678-1234-567812345678"
        mock_crud.upload_file = AsyncMock(return_value=MinioObjectResponse(
            bucket_name="bucket",
            object_name=mock_uuid,
            original_filename="document.pdf",
            size=1024,
            last_modified=datetime.now(timezone.utc),
            etag="abc123",
        ))
        mock_crud.ensure_bucket_exists = AsyncMock()
        
        service = MinioService(crud=mock_crud)
        
        with patch("uuid.uuid4", return_value=uuid.UUID(mock_uuid)):
            result = await service.upload_file(
                bucket_name="bucket",
                file_data=b"test data",
                preserve_filename=True,
                original_filename="document.pdf"
            )
        
        assert result.object_name == mock_uuid
        assert result.original_filename == "document.pdf"
        mock_crud.upload_file.assert_called_once()
        # Проверяем, что upload_file вызван с object_name=None (будет сгенерирован в crud)
        call_args = mock_crud.upload_file.call_args
        assert call_args.kwargs.get("object_name") is None
        assert call_args.kwargs.get("preserve_filename") is True
        assert call_args.kwargs.get("original_filename") == "document.pdf"
    
    @pytest.mark.asyncio
    async def test_upload_file_with_preserve_filename(self, service, mock_crud):
        """Test upload file with preserve_filename=True."""
        file_data = b"test data"
        result = await service.upload_file(
            bucket_name="bucket",
            object_name="custom-name.txt",
            file_data=file_data,
            original_filename="myfile.txt",
            preserve_filename=True
        )
        # Mock returns "report.pdf" from fixture, but we check that params are passed correctly
        assert result.original_filename == "report.pdf"  # from mock
        mock_crud.upload_file.assert_called_once_with(
            bucket_name="bucket",
            object_name="custom-name.txt",
            file_data=file_data,
            content_type=None,
            original_filename="myfile.txt",
            preserve_filename=True
        )
    
    @pytest.mark.asyncio
    async def test_upload_file_empty(self, service):
        """Test upload file with empty data."""
        with pytest.raises(ValueError, match="File data cannot be empty"):
            await service.upload_file("bucket", "file.txt", b"")
    
    @pytest.mark.asyncio
    async def test_download_file(self, service, mock_crud):
        """Test download file."""
        result = await service.download_file("bucket", "file.txt")
        assert result == b"file content"
        mock_crud.download_file.assert_called_once_with("bucket", "file.txt")
    
    @pytest.mark.asyncio
    async def test_delete_file(self, service, mock_crud):
        """Test delete file."""
        result = await service.delete_file("bucket", "file.txt")
        assert result is True
        mock_crud.delete_file.assert_called_once_with("bucket", "file.txt")
    
    @pytest.mark.asyncio
    async def test_get_object(self, service, mock_crud):
        """Test get object."""
        result = await service.get_object("bucket", "file.txt")
        assert result.bucket_name == "bucket"
        mock_crud.get_object.assert_called_once_with("bucket", "file.txt")
    
    @pytest.mark.asyncio
    async def test_list_objects(self, service, mock_crud):
        """Test list objects."""
        result = await service.list_objects("bucket", prefix="docs/")
        assert result.bucket_name == "bucket"
        mock_crud.list_objects.assert_called_once_with("bucket", prefix="docs/")
    
    @pytest.mark.asyncio
    async def test_get_download_url(self, service, mock_crud):
        """Test get download URL."""
        result = await service.get_download_url("bucket", "file.txt", expires=7200)
        assert result.url == "https://example.com/presigned"
        assert result.http_method == "GET"
        mock_crud.get_presigned_url.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_upload_url(self, service, mock_crud):
        """Test get upload URL."""
        result = await service.get_upload_url("bucket", "file.txt", expires=7200)
        assert result.http_method == "PUT"
        mock_crud.get_presigned_url.assert_called()
