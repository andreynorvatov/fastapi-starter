"""
Тесты для CRUD операций модели File.
"""

import uuid

import pytest

from src.file_storage.crud import (
    count_files,
    create_file,
    get_file_by_uuid,
    get_files,
    hard_delete_file,
    soft_delete_file,
    update_file,
)
from src.file_storage.models import File
from src.file_storage.schemas import FileCreate, FileUpdate


class TestCreateFile:
    """Тесты для функции create_file."""

    @pytest.mark.asyncio
    async def test_create_file_success(self, db_session: AsyncSession) -> None:
        """Тест успешного создания записи о файле."""
        file_create = FileCreate(
            original_filename="test.txt",
            file_path="ab/cd/11111111-1111-1111-1111-111111111111",
            file_size=1024,
            mime_type="text/plain",
            extension=".txt",
            is_active=True,
        )

        result = await create_file(db_session, file_create)

        assert isinstance(result, File)
        assert result.id is not None
        assert result.original_filename == "test.txt"
        assert result.file_path == "ab/cd/11111111-1111-1111-1111-111111111111"
        assert result.file_size == 1024
        assert result.mime_type == "text/plain"
        assert result.extension == ".txt"
        assert result.is_active is True
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_create_file_persists_in_db(self, db_session: AsyncSession) -> None:
        """Тест что созданный файл сохраняется в БД."""
        file_create = FileCreate(
            original_filename="persist.txt",
            file_path="ef/gh/22222222-2222-2222-2222-222222222222",
            file_size=512,
            is_active=True,
        )

        created = await create_file(db_session, file_create)

        # Проверяем, что запись можно найти по UUID
        found = await get_file_by_uuid(db_session, created.id)
        assert found is not None
        assert found.id == created.id
        assert found.original_filename == "persist.txt"


class TestGetFileByUuid:
    """Тесты для функции get_file_by_uuid."""

    @pytest.mark.asyncio
    async def test_get_file_by_uuid_existing(
        self, db_session: AsyncSession, file_test_data: list[File]
    ) -> None:
        """Тест поиска существующего файла по UUID."""
        # Берем первый файл из тестовых данных
        file_uuid = file_test_data[0].id

        result = await get_file_by_uuid(db_session, file_uuid)

        assert result is not None
        assert result.id == file_uuid
        assert result.original_filename == file_test_data[0].original_filename

    @pytest.mark.asyncio
    async def test_get_file_by_uuid_not_existing(self, db_session: AsyncSession) -> None:
        """Тест поиска несуществующего файла по UUID."""
        non_existent_uuid = uuid.uuid4()
        result = await get_file_by_uuid(db_session, non_existent_uuid)
        assert result is None


class TestGetFiles:
    """Тесты для функции get_files."""

    @pytest.mark.asyncio
    async def test_get_files_default_params(
        self, db_session: AsyncSession, file_test_data: list[File]
    ) -> None:
        """Тест получения списка файлов с параметрами по умолчанию."""
        files = await get_files(db_session, skip=0, limit=100)

        assert len(files) == 3  # Все файлы из file_test_data
        # Проверяем, что файлы отсортированы по created_at desc
        for i in range(len(files) - 1):
            assert files[i].created_at >= files[i + 1].created_at

    @pytest.mark.asyncio
    async def test_get_files_with_pagination(
        self, db_session: AsyncSession, file_test_data: list[File]
    ) -> None:
        """Тест получения списка файлов с пагинацией."""
        files = await get_files(db_session, skip=0, limit=2)

        assert len(files) == 2

    @pytest.mark.asyncio
    async def test_get_files_with_skip(
        self, db_session: AsyncSession, file_test_data: list[File]
    ) -> None:
        """Тест получения списка файлов с пропуском."""
        files = await get_files(db_session, skip=1, limit=10)

        assert len(files) == 2  # Пропустили 1 из 3

    @pytest.mark.asyncio
    async def test_get_files_filter_active(
        self, db_session: AsyncSession, file_test_data: list[File]
    ) -> None:
        """Тест фильтрации по активным файлам."""
        files = await get_files(db_session, skip=0, limit=100, is_active=True)

        assert len(files) == 2  # Два активных файла в file_test_data
        for file in files:
            assert file.is_active is True

    @pytest.mark.asyncio
    async def test_get_files_filter_inactive(
        self, db_session: AsyncSession, file_test_data: list[File]
    ) -> None:
        """Тест фильтрации по неактивным файлам."""
        files = await get_files(db_session, skip=0, limit=100, is_active=False)

        assert len(files) == 1  # Один неактивный файл
        assert files[0].is_active is False

    @pytest.mark.asyncio
    async def test_get_files_empty_result(self, db_session: AsyncSession) -> None:
        """Тест получения пустого списка."""
        files = await get_files(db_session, skip=0, limit=100)
        assert len(files) == 0


class TestCountFiles:
    """Тесты для функции count_files."""

    @pytest.mark.asyncio
    async def test_count_files_all(self, db_session: AsyncSession, file_test_data: list[File]) -> None:
        """Тест подсчёта всех файлов."""
        total = await count_files(db_session)
        assert total == 3

    @pytest.mark.asyncio
    async def test_count_files_active(self, db_session: AsyncSession, file_test_data: list[File]) -> None:
        """Тест подсчёта активных файлов."""
        total = await count_files(db_session, is_active=True)
        assert total == 2

    @pytest.mark.asyncio
    async def test_count_files_inactive(self, db_session: AsyncSession, file_test_data: list[File]) -> None:
        """Тест подсчёта неактивных файлов."""
        total = await count_files(db_session, is_active=False)
        assert total == 1

    @pytest.mark.asyncio
    async def test_count_files_empty(self, db_session: AsyncSession) -> None:
        """Тест подсчёта при пустой таблице."""
        total = await count_files(db_session)
        assert total == 0


class TestUpdateFile:
    """Тесты для функции update_file."""

    @pytest.mark.asyncio
    async def test_update_file_success(
        self, db_session: AsyncSession, file_test_data: list[File]
    ) -> None:
        """Тест успешного обновления файла."""
        file = file_test_data[0]
        file_update = FileUpdate(original_filename="updated_name.txt", is_active=False)

        result = await update_file(db_session, file.id, file_update)

        assert result is not None
        assert result.id == file.id
        assert result.original_filename == "updated_name.txt"
        assert result.is_active is False
        # Остальные поля должны остаться неизменными
        assert result.file_path == file.file_path
        assert result.file_size == file.file_size

    @pytest.mark.asyncio
    async def test_update_file_partial(
        self, db_session: AsyncSession, file_test_data: list[File]
    ) -> None:
        """Тест частичного обновления (только одно поле)."""
        file = file_test_data[0]
        file_update = FileUpdate(original_filename="partial_update.txt")

        result = await update_file(db_session, file.id, file_update)

        assert result is not None
        assert result.original_filename == "partial_update.txt"
        assert result.is_active == file.is_active  # Не изменилось

    @pytest.mark.asyncio
    async def test_update_file_not_found(self, db_session: AsyncSession) -> None:
        """Тест обновления несуществующего файла."""
        non_existent_uuid = uuid.uuid4()
        file_update = FileUpdate(original_filename="test.txt")

        result = await update_file(db_session, non_existent_uuid, file_update)
        assert result is None


class TestSoftDeleteFile:
    """Тесты для функции soft_delete_file."""

    @pytest.mark.asyncio
    async def test_soft_delete_file_success(
        self, db_session: AsyncSession, file_test_data: list[File]
    ) -> None:
        """Тест успешного мягкого удаления файла."""
        file = file_test_data[0]
        assert file.is_active is True

        result = await soft_delete_file(db_session, file.id)

        assert result is not None
        assert result.is_active is False

        # Проверяем, что файл всё ещё можно получить через get_file_by_uuid
        fetched = await get_file_by_uuid(db_session, file.id)
        assert fetched is not None
        assert fetched.is_active is False

    @pytest.mark.asyncio
    async def test_soft_delete_file_not_found(self, db_session: AsyncSession) -> None:
        """Тест мягкого удаления несуществующего файла."""
        non_existent_uuid = uuid.uuid4()
        result = await soft_delete_file(db_session, non_existent_uuid)
        assert result is None


class TestHardDeleteFile:
    """Тесты для функции hard_delete_file."""

    @pytest.mark.asyncio
    async def test_hard_delete_file_success(
        self, db_session: AsyncSession, file_test_data: list[File]
    ) -> None:
        """Тест успешного физического удаления файла."""
        file = file_test_data[0]

        result = await hard_delete_file(db_session, file.id)
        assert result is True

        # Проверяем, что файл удалён из БД
        fetched = await get_file_by_uuid(db_session, file.id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_hard_delete_file_not_found(self, db_session: AsyncSession) -> None:
        """Тест физического удаления несуществующего файла."""
        non_existent_uuid = uuid.uuid4()
        result = await hard_delete_file(db_session, non_existent_uuid)
        assert result is False
