"""Tests for Minio CRUD operations."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from src.minio_service.crud import MinioCRUD
from src.minio_service.schemas import MinioObjectResponse


class TestMinioCRUD:
    """Tests for MinioCRUD."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock Minio client."""
        mock = MagicMock()
        mock.ensure_bucket_exists = MagicMock()
        mock.upload_file = MagicMock()
        mock.stat_object = MagicMock(return_value={
            "size": 1024,
            "last_modified": datetime.now(timezone.utc),
            "etag": "abc123",
            "content_type": "text/plain",
            "metadata": {},
        })
        mock.download_file = MagicMock(return_value=b"file content")
        mock.remove_file = MagicMock()
        mock.list_files = MagicMock(return_value=[
            {
                "name": "file1.txt",
                "size": 1024,
                "last_modified": datetime.now(timezone.utc),
                "etag": "abc123",
            }
        ])
        mock.get_presigned_url = MagicMock(return_value="https://example.com/presigned")
        return mock
    
    @pytest.fixture
    def crud(self, mock_client):
        """Create CRUD with mock client."""
        return MinioCRUD(client=mock_client)
    
    @pytest.mark.asyncio
    async def test_upload_file_with_object_name(self, crud, mock_client):
        """Test upload file with explicit object_name."""
        file_data = b"test data"
        result = await crud.upload_file(
            bucket_name="test-bucket",
            object_name="custom-name.txt",
            file_data=file_data,
        )
        
        assert result.bucket_name == "test-bucket"
        assert result.object_name == "custom-name.txt"
        assert result.original_filename is None
        mock_client.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_generates_uuid(self, crud, mock_client):
        """Test upload file without object_name generates UUID."""
        import uuid
        
        file_data = b"test data"
        mock_uuid = "12345678-1234-5678-1234-567812345678"
        
        with patch("uuid.uuid4", return_value=uuid.UUID(mock_uuid)):
            result = await crud.upload_file(
                bucket_name="test-bucket",
                object_name=None,
                file_data=file_data,
                preserve_filename=True,
                original_filename="document.pdf"
            )
        
        # Should generate UUID with .pdf extension
        assert result.object_name == f"{mock_uuid}.pdf"
        assert result.original_filename == "document.pdf"
        # Проверяем, что upload_file вызван с правильными параметрами
        call_args = mock_client.upload_file.call_args
        # call_args[0] - args tuple: (bucket_name, object_name, file_data, content_type)
        assert call_args[0][0] == "test-bucket"
        assert call_args[0][1] == f"{mock_uuid}.pdf"
        assert call_args[0][2] == file_data
        # content_type is the 4th positional arg (None)
        assert call_args[0][3] is None
        # Проверяем metadata в kwargs
        assert call_args[1].get("metadata", {}).get("original_filename") == "document.pdf"
    
    @pytest.mark.asyncio
    async def test_upload_file_preserves_extension(self, crud, mock_client):
        """Test that generated UUID preserves file extension."""
        import uuid
        
        file_data = b"test data"
        mock_uuid = "12345678-1234-5678-1234-567812345678"
        
        with patch("uuid.uuid4", return_value=uuid.UUID(mock_uuid)):
            result = await crud.upload_file(
                bucket_name="test-bucket",
                object_name=None,
                file_data=file_data,
                preserve_filename=True,
                original_filename="myfile.pdf"
            )
        
        assert result.object_name == f"{mock_uuid}.pdf"
        assert result.original_filename == "myfile.pdf"
        # Проверяем, что upload_file вызван с правильными параметрами
        call_args = mock_client.upload_file.call_args
        assert call_args[0][1] == f"{mock_uuid}.pdf"
    
    @pytest.mark.asyncio
    async def test_upload_file_without_preserve_filename(self, crud, mock_client):
        """Test upload file without preserve_filename."""
        import uuid
        
        file_data = b"test data"
        mock_uuid = "12345678-1234-5678-1234-567812345678"
        
        with patch("uuid.uuid4", return_value=uuid.UUID(mock_uuid)):
            result = await crud.upload_file(
                bucket_name="test-bucket",
                object_name=None,
                file_data=file_data,
                preserve_filename=False,
            )
        
        assert result.object_name == mock_uuid
        assert result.original_filename is None
        # Проверяем, что metadata не передается или пустой
        call_args = mock_client.upload_file.call_args
        # When metadata is empty dict, it's passed as None
        assert call_args[1].get("metadata") is None

    @pytest.mark.asyncio
    async def test_upload_file_default_preserves_filename(self, crud, mock_client):
        """Test upload file with default preserve_filename=True."""
        import uuid
        
        file_data = b"test data"
        mock_uuid = "12345678-1234-5678-1234-567812345678"
        
        with patch("uuid.uuid4", return_value=uuid.UUID(mock_uuid)):
            result = await crud.upload_file(
                bucket_name="test-bucket",
                object_name=None,
                file_data=file_data,
                preserve_filename=True,
                original_filename="document.pdf"
            )
        
        assert result.object_name == f"{mock_uuid}.pdf"
        assert result.original_filename == "document.pdf"
        call_args = mock_client.upload_file.call_args
        assert call_args[1].get("metadata", {}).get("original_filename") == "document.pdf"
    
    @pytest.mark.asyncio
    async def test_upload_file_extends_existing_uuid(self, crud, mock_client):
        """Test that if object_name is provided, it's used as-is."""
        file_data = b"test data"
        result = await crud.upload_file(
            bucket_name="test-bucket",
            object_name="existing-uuid.txt",
            file_data=file_data,
        )
        
        assert result.object_name == "existing-uuid.txt"
        assert result.original_filename is None
    
    @pytest.mark.asyncio
    async def test_upload_file_empty_data(self, crud):
        """Test upload file with empty data raises error."""
        with pytest.raises(ValueError, match="File data cannot be empty"):
            await crud.upload_file(
                bucket_name="test-bucket",
                object_name="file.txt",
                file_data=b"",
            )

    @pytest.mark.asyncio
    async def test_get_object_extracts_original_filename(self, crud, mock_client):
        """Test that get_object extracts original_filename from metadata."""
        # Setup mock with metadata containing original_filename
        mock_client.stat_object = MagicMock(return_value={
            "size": 1024,
            "last_modified": datetime.now(timezone.utc),
            "etag": "abc123",
            "content_type": "text/plain",
            "metadata": {"original_filename": "report.pdf"},
        })
        
        result = await crud.get_object(
            bucket_name="test-bucket",
            object_name="uuid-file.pdf"
        )
        
        assert result.bucket_name == "test-bucket"
        assert result.object_name == "uuid-file.pdf"
        assert result.original_filename == "report.pdf"
        assert result.size == 1024

    @pytest.mark.asyncio
    async def test_get_object_without_original_filename(self, crud, mock_client):
        """Test that get_object returns None when no original_filename in metadata."""
        mock_client.stat_object = MagicMock(return_value={
            "size": 1024,
            "last_modified": datetime.now(timezone.utc),
            "etag": "abc123",
            "content_type": "text/plain",
            "metadata": {},
        })
        
        result = await crud.get_object(
            bucket_name="test-bucket",
            object_name="file.txt"
        )
        
        assert result.original_filename is None

    @pytest.mark.asyncio
    async def test_list_objects_extracts_original_filename(self, crud, mock_client):
        """Test that list_objects extracts original_filename from metadata for each object."""
        mock_client.list_files = MagicMock(return_value=[
            {
                "name": "uuid1.pdf",
                "size": 1024,
                "last_modified": datetime.now(timezone.utc),
                "etag": "abc123",
                "metadata": {"original_filename": "document1.pdf"},
            },
            {
                "name": "uuid2.pdf",
                "size": 2048,
                "last_modified": datetime.now(timezone.utc),
                "etag": "def456",
                "metadata": {"original_filename": "document2.pdf"},
            },
            {
                "name": "uuid3.txt",
                "size": 512,
                "last_modified": datetime.now(timezone.utc),
                "etag": "ghi789",
                "metadata": {},  # No original filename
            },
        ])
        
        result = await crud.list_objects(
            bucket_name="test-bucket",
            prefix="docs/"
        )
        
        assert result.count == 3
        assert result.objects[0].original_filename == "document1.pdf"
        assert result.objects[1].original_filename == "document2.pdf"
        assert result.objects[2].original_filename is None
