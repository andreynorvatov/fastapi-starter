"""
Тесты для API эндпоинтов файлового хранилища.
"""

import io
import uuid

import pytest
from httpx import AsyncClient

from src.file_storage.models import File
from src.file_storage.schemas import FileCreate
from src.file_storage.crud import create_file


class TestUploadFile:
    """Тесты для POST /files/upload эндпоинта."""

    @pytest.mark.asyncio
    async def test_upload_file_success(
        self, client_with_storage: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Тест успешной загрузки файла."""
        file_content = b"Test file content"
        filename = "test.txt"

        # Создаём файл для загрузки
        files = {"file": (filename, io.BytesIO(file_content), "text/plain")}

        response = await client_with_storage.post("/files/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Проверяем структуру ответа
        assert "id" in data
        assert data["original_filename"] == filename
        assert data["file_size"] == len(file_content)
        assert data["mime_type"] == "text/plain"
        assert data["extension"] == ".txt"
        assert data["is_active"] is True
        assert "created_at" in data
        assert "updated_at" in data

        # Проверяем, что запись создана в БД
        file_uuid = uuid.UUID(data["id"])
        db_file = await db_session.get(File, file_uuid)
        assert db_file is not None
        assert db_file.original_filename == filename

    @pytest.mark.asyncio
    async def test_upload_file_different_mime(
        self, client_with_storage: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Тест загрузки файла с другим MIME-типом."""
        file_content = b"Image data"
        filename = "image.jpg"

        files = {"file": (filename, io.BytesIO(file_content), "image/jpeg")}

        response = await client_with_storage.post("/files/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["mime_type"] == "image/jpeg"
        assert data["extension"] == ".jpg"

    @pytest.mark.asyncio
    async def test_upload_file_no_extension(
        self, client_with_storage: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Тест загрузки файла без расширения."""
        file_content = b"No extension file"
        filename = "noextension"

        files = {"file": (filename, io.BytesIO(file_content), "text/plain")}

        response = await client_with_storage.post("/files/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["extension"] is None

    @pytest.mark.asyncio
    async def test_upload_empty_file(
        self, client_with_storage: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Тест загрузки пустого файла."""
        file_content = b""
        filename = "empty.txt"

        files = {"file": (filename, io.BytesIO(file_content), "text/plain")}

        response = await client_with_storage.post("/files/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["file_size"] == 0


class TestGetFileMetadata:
    """Тесты для GET /files/{file_uuid} эндпоинта."""

    @pytest.mark.asyncio
    async def test_get_file_metadata_success(
        self,
        client_with_storage: AsyncClient,
        db_session: AsyncSession,
        test_storage_service: FileStorageService,
    ) -> None:
        """Тест получения метаданных существующего файла."""
        # Создаём файл на диске и в БД
        file_content = b"Test content"
        file_uuid = test_storage_service.save_file(file_content)

        # Создаём запись в БД с тем же UUID
        uuid_str = str(file_uuid).replace("-", "")
        prefix1 = uuid_str[:2]
        prefix2 = uuid_str[2:4]
        relative_path = f"{prefix1}/{prefix2}/{file_uuid}"

        file_create = FileCreate(
            original_filename="metadata_test.txt",
            file_path=relative_path,
            file_size=len(file_content),
            mime_type="text/plain",
            extension=".txt",
            is_active=True,
        )
        await create_file(db_session, file_create, file_id=file_uuid)

        # Запрашиваем метаданные
        response = await client_with_storage.get(f"/files/{file_uuid}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(file_uuid)
        assert data["original_filename"] == "metadata_test.txt"
        assert data["file_size"] == len(file_content)

    @pytest.mark.asyncio
    async def test_get_file_metadata_not_found(
        self, client_with_storage: AsyncClient
    ) -> None:
        """Тест получения метаданных несуществующего файла."""
        non_existent_uuid = uuid.uuid4()

        response = await client_with_storage.get(f"/files/{non_existent_uuid}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Файл не найден"

    @pytest.mark.asyncio
    async def test_get_file_metadata_invalid_uuid(
        self, client_with_storage: AsyncClient
    ) -> None:
        """Тест получения метаданных с некорректным UUID."""
        response = await client_with_storage.get("/files/invalid-uuid")

        assert response.status_code == 400
        assert response.json()["detail"] == "Некорректный UUID"

    @pytest.mark.asyncio
    async def test_get_file_metadata_inactive(
        self,
        client_with_storage: AsyncClient,
        db_session: AsyncSession,
        test_storage_service: FileStorageService,
    ) -> None:
        """Тест получения метаданных неактивного файла."""
        # Создаём неактивный файл
        file_uuid = uuid.uuid4()
        file_content = b"Test"
        test_storage_service.save_file(file_content, file_uuid=file_uuid)

        uuid_str = str(file_uuid).replace("-", "")
        prefix1 = uuid_str[:2]
        prefix2 = uuid_str[2:4]
        relative_path = f"{prefix1}/{prefix2}/{file_uuid}"

        file_create = FileCreate(
            original_filename="inactive.txt",
            file_path=relative_path,
            file_size=len(file_content),
            is_active=False,
        )
        await create_file(db_session, file_create, file_id=file_uuid)

        response = await client_with_storage.get(f"/files/{file_uuid}")
        assert response.status_code == 404


class TestDownloadFile:
    """Тесты для GET /files/{file_uuid}/content эндпоинта."""

    @pytest.mark.asyncio
    async def test_download_file_success(
        self,
        client_with_storage: AsyncClient,
        db_session: AsyncSession,
        test_storage_service: FileStorageService,
    ) -> None:
        """Тест успешного скачивания файла."""
        file_content = b"Download me"
        file_uuid = test_storage_service.save_file(file_content)

        # Создаём запись в БД с тем же UUID
        uuid_str = str(file_uuid).replace("-", "")
        prefix1 = uuid_str[:2]
        prefix2 = uuid_str[2:4]
        relative_path = f"{prefix1}/{prefix2}/{file_uuid}"

        file_create = FileCreate(
            original_filename="download_test.txt",
            file_path=relative_path,
            file_size=len(file_content),
            mime_type="text/plain",
            extension=".txt",
            is_active=True,
        )
        await create_file(db_session, file_create, file_id=file_uuid)

        response = await client_with_storage.get(f"/files/{file_uuid}/content")

        assert response.status_code == 200
        assert response.content == file_content
        assert response.headers["content-disposition"] == f'attachment; filename="download_test.txt"'
        assert response.headers["content-length"] == str(len(file_content))

    @pytest.mark.asyncio
    async def test_download_file_not_found(
        self, client_with_storage: AsyncClient
    ) -> None:
        """Тест скачивания несуществующего файла."""
        non_existent_uuid = uuid.uuid4()

        response = await client_with_storage.get(f"/files/{non_existent_uuid}/content")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_file_missing_on_disk(
        self,
        client_with_storage: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Тест скачивания когда запись в БД есть, а файла на диске нет."""
        file_uuid = uuid.uuid4()

        # Создаём запись в БД без файла на диске
        uuid_str = str(file_uuid).replace("-", "")
        prefix1 = uuid_str[:2]
        prefix2 = uuid_str[2:4]
        relative_path = f"{prefix1}/{prefix2}/{file_uuid}"

        file_create = FileCreate(
            original_filename="missing.txt",
            file_path=relative_path,
            file_size=100,
            is_active=True,
        )
        await create_file(db_session, file_create, file_id=file_uuid)

        response = await client_with_storage.get(f"/files/{file_uuid}/content")
        assert response.status_code == 404
        # Проверяем, что в ответе есть сообщение об ошибке (может быть на русском или английском)
        detail = response.json()["detail"]
        assert "не найден" in detail or "not found" in detail


class TestListFiles:
    """Тесты для GET /files/ эндпоинта."""

    @pytest.mark.asyncio
    async def test_list_files_default(
        self,
        client_with_storage: AsyncClient,
        file_test_data: list[File],
    ) -> None:
        """Тест получения списка файлов с параметрами по умолчанию."""
        response = await client_with_storage.get("/files/")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        # По умолчанию is_active=None (все файлы)
        assert data["total"] == 3
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_files_active_only(
        self,
        client_with_storage: AsyncClient,
        file_test_data: list[File],
    ) -> None:
        """Тест фильтрации только активных файлов."""
        response = await client_with_storage.get("/files/?is_active=true")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert len(data["items"]) == 2
        for item in data["items"]:
            assert item["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_files_inactive_only(
        self,
        client_with_storage: AsyncClient,
        file_test_data: list[File],
    ) -> None:
        """Тест фильтрации только неактивных файлов."""
        response = await client_with_storage.get("/files/?is_active=false")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["is_active"] is False

    @pytest.mark.asyncio
    async def test_list_files_pagination(
        self,
        client_with_storage: AsyncClient,
        file_test_data: list[File],
    ) -> None:
        """Тест пагинации."""
        response = await client_with_storage.get("/files/?skip=0&limit=2")

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 2
        assert data["skip"] == 0
        assert data["limit"] == 2
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_list_files_skip(
        self,
        client_with_storage: AsyncClient,
        file_test_data: list[File],
    ) -> None:
        """Тест пропуска записей."""
        response = await client_with_storage.get("/files/?skip=1&limit=10")

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 2
        assert data["skip"] == 1

    @pytest.mark.asyncio
    async def test_list_files_empty(
        self, client_with_storage: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Тест пустого списка."""
        # Таблица уже очищена фикстурой file_test_data, но для ясности
        response = await client_with_storage.get("/files/?skip=100")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0


class TestUpdateFileMetadata:
    """Тесты для PUT /files/{file_uuid} эндпоинта."""

    @pytest.mark.asyncio
    async def test_update_file_metadata_success(
        self,
        client_with_storage: AsyncClient,
        db_session: AsyncSession,
        file_test_data: list[File],
    ) -> None:
        """Тест успешного обновления метаданных."""
        file = file_test_data[0]
        payload = {
            "original_filename": "updated_name.txt",
            "is_active": False,
        }

        response = await client_with_storage.put(f"/files/{file.id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(file.id)
        assert data["original_filename"] == "updated_name.txt"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_file_partial(
        self,
        client_with_storage: AsyncClient,
        db_session: AsyncSession,
        file_test_data: list[File],
    ) -> None:
        """Тест частичного обновления."""
        file = file_test_data[0]
        payload = {"original_filename": "partial_update.txt"}

        response = await client_with_storage.put(f"/files/{file.id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["original_filename"] == "partial_update.txt"
        assert data["is_active"] == file.is_active  # Не изменилось

    @pytest.mark.asyncio
    async def test_update_file_not_found(
        self, client_with_storage: AsyncClient
    ) -> None:
        """Тест обновления несуществующего файла."""
        non_existent_uuid = uuid.uuid4()
        payload = {"original_filename": "test.txt"}

        response = await client_with_storage.put(f"/files/{non_existent_uuid}", json=payload)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_file_invalid_uuid(
        self, client_with_storage: AsyncClient
    ) -> None:
        """Тест обновления с некорректным UUID."""
        payload = {"original_filename": "test.txt"}

        response = await client_with_storage.put("/files/invalid-uuid", json=payload)

        assert response.status_code == 400


class TestDeleteFile:
    """Тесты для DELETE /files/{file_uuid} эндпоинта."""

    @pytest.mark.asyncio
    async def test_delete_file_success(
        self,
        client_with_storage: AsyncClient,
        db_session: AsyncSession,
        test_storage_service: FileStorageService,
    ) -> None:
        """Тест успешного удаления файла."""
        # Создаём файл
        file_content = b"To delete"
        file_uuid = test_storage_service.save_file(file_content)

        # Создаём запись в БД с тем же UUID
        uuid_str = str(file_uuid).replace("-", "")
        prefix1 = uuid_str[:2]
        prefix2 = uuid_str[2:4]
        relative_path = f"{prefix1}/{prefix2}/{file_uuid}"

        file_create = FileCreate(
            original_filename="delete_me.txt",
            file_path=relative_path,
            file_size=len(file_content),
            is_active=True,
        )
        await create_file(db_session, file_create, file_id=file_uuid)

        # Удаляем
        response = await client_with_storage.delete(f"/files/{file_uuid}")

        assert response.status_code == 204

        # Проверяем, что файл удалён с диска
        assert not test_storage_service.file_exists(file_uuid)

        # Проверяем, что запись в БД имеет is_active=False
        db_file = await db_session.get(File, file_uuid)
        assert db_file is not None
        assert db_file.is_active is False

    @pytest.mark.asyncio
    async def test_delete_file_not_found(
        self, client_with_storage: AsyncClient
    ) -> None:
        """Тест удаления несуществующего файла."""
        non_existent_uuid = uuid.uuid4()

        response = await client_with_storage.delete(f"/files/{non_existent_uuid}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_file_invalid_uuid(
        self, client_with_storage: AsyncClient
    ) -> None:
        """Тест удаления с некорректным UUID."""
        response = await client_with_storage.delete("/files/invalid-uuid")

        assert response.status_code == 400


class TestHardDeleteFile:
    """Тесты для DELETE /files/{file_uuid}/hard эндпоинта."""

    @pytest.mark.asyncio
    async def test_hard_delete_file_success(
        self,
        client_with_storage: AsyncClient,
        db_session: AsyncSession,
        test_storage_service: FileStorageService,
    ) -> None:
        """Тест успешного жесткого удаления файла."""
        # Создаём файл
        file_content = b"To hard delete"
        file_uuid = test_storage_service.save_file(file_content)

        # Создаём запись в БД с тем же UUID
        uuid_str = str(file_uuid).replace("-", "")
        prefix1 = uuid_str[:2]
        prefix2 = uuid_str[2:4]
        relative_path = f"{prefix1}/{prefix2}/{file_uuid}"

        file_create = FileCreate(
            original_filename="hard_delete_me.txt",
            file_path=relative_path,
            file_size=len(file_content),
            is_active=True,
        )
        await create_file(db_session, file_create, file_id=file_uuid)

        # Жестко удаляем
        response = await client_with_storage.delete(f"/files/{file_uuid}/hard")

        assert response.status_code == 204

        # Проверяем, что файл удалён с диска
        assert not test_storage_service.file_exists(file_uuid)

        # Проверяем, что запись в БД полностью удалена
        db_file = await db_session.get(File, file_uuid)
        assert db_file is None

    @pytest.mark.asyncio
    async def test_hard_delete_file_not_found(
        self, client_with_storage: AsyncClient
    ) -> None:
        """Тест жесткого удаления несуществующего файла."""
        non_existent_uuid = uuid.uuid4()

        response = await client_with_storage.delete(f"/files/{non_existent_uuid}/hard")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_hard_delete_file_invalid_uuid(
        self, client_with_storage: AsyncClient
    ) -> None:
        """Тест жесткого удаления с некорректным UUID."""
        response = await client_with_storage.delete("/files/invalid-uuid/hard")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_hard_delete_file_removes_from_db_and_disk(
        self,
        client_with_storage: AsyncClient,
        db_session: AsyncSession,
        test_storage_service: FileStorageService,
    ) -> None:
        """Тест что жесткое удаление удаляет и с диска и из БД."""
        # Создаём файл
        file_content = b"Complete deletion test"
        file_uuid = test_storage_service.save_file(file_content)

        # Создаём запись в БД
        uuid_str = str(file_uuid).replace("-", "")
        prefix1 = uuid_str[:2]
        prefix2 = uuid_str[2:4]
        relative_path = f"{prefix1}/{prefix2}/{file_uuid}"

        file_create = FileCreate(
            original_filename="complete_delete.txt",
            file_path=relative_path,
            file_size=len(file_content),
            is_active=True,
        )
        await create_file(db_session, file_create, file_id=file_uuid)

        # Проверяем что файл существует
        assert test_storage_service.file_exists(file_uuid)
        db_file = await db_session.get(File, file_uuid)
        assert db_file is not None

        # Жестко удаляем
        response = await client_with_storage.delete(f"/files/{file_uuid}/hard")
        assert response.status_code == 204

        # Проверяем что файл удален с диска
        assert not test_storage_service.file_exists(file_uuid)

        # Проверяем что запись удалена из БД
        db_file_after = await db_session.get(File, file_uuid)
        assert db_file_after is None
