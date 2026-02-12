"""
Локальные фикстуры для тестов сервиса файлового хранилища.

Содержит фикстуры для:
- Генерации тестовых данных File
- Очистки таблицы files
- Переопределения FileStorageService для использования временной директории
"""

import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.file_storage.service import FileStorageService, get_file_storage_service
from tests.factories.file_factory import FileFactory


async def clear_files_table(session: AsyncSession, schema: str) -> None:
    """
    Очищает таблицу files в указанной схеме.

    Args:
        session: Асинхронная сессия БД
        schema: Имя схемы БД
    """
    await session.execute(
        text(f'TRUNCATE TABLE "{schema}"."files" RESTART IDENTITY CASCADE')
    )
    await session.commit()


@pytest.fixture
async def file_test_data(db_session: AsyncSession, test_settings_fixture) -> AsyncGenerator[list, None]:
    """
    Фикстура для генерации тестовых данных File.

    Очищает таблицу files перед и после теста, создаёт стандартный
    набор тестовых данных.

    Args:
        db_session: Асинхронная сессия БД
        test_settings_fixture: Настройки тестовой БД

    Yields:
        Список созданных экземпляров File
    """
    schema = test_settings_fixture.POSTGRES_USER

    # Очищаем таблицу перед тестом
    await clear_files_table(db_session, schema)

    # Создаём тестовые данные
    test_data = FileFactory.get_default_test_data()
    files = await FileFactory.create_batch(db_session, test_data)

    try:
        yield files
    finally:
        # Очищаем таблицу после теста
        await clear_files_table(db_session, schema)


@pytest.fixture
def temp_storage_dir() -> TemporaryDirectory:
    """
    Временная директория для хранения файлов в тестах API.

    Returns:
        TemporaryDirectory: Временная директория
    """
    temp_dir = TemporaryDirectory()
    yield temp_dir
    temp_dir.cleanup()


@pytest.fixture
def test_storage_service(temp_storage_dir: TemporaryDirectory) -> FileStorageService:
    """
    Экземпляр FileStorageService с временной директорией для тестов.

    Args:
        temp_storage_dir: Временная директория

    Returns:
        FileStorageService: Сервис с временным хранилищем
    """
    return FileStorageService(storage_path=Path(temp_storage_dir.name))


@pytest.fixture
async def client_with_storage(
    client: AsyncClient,
    test_storage_service: FileStorageService,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Расширенная фикстура client, которая также переопределяет
    get_file_storage_service для использования временного хранилища.

    Args:
        client: Базовый HTTP-клиент
        test_storage_service: Тестовый сервис хранилища

    Yields:
        AsyncClient: Клиент с переопределёнными зависимостями
    """

    async def override_get_file_storage_service() -> FileStorageService:
        return test_storage_service

    # Переопределяем зависимость
    app = client._transport.app  # type: ignore
    app.dependency_overrides[get_file_storage_service] = override_get_file_storage_service

    yield client

    # Очищаем переопределения
    app.dependency_overrides.clear()
