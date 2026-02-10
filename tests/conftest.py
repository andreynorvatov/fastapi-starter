"""
Конфигурация pytest для асинхронных тестов.

Содержит фикстуры для:
- Подключения к тестовой базе данных
- Удаления и создания таблиц через alembic
- Генерации тестовых данных
- Асинхронного HTTP-клиента
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import patch

import nest_asyncio
import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pydantic import PostgresDsn
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from src.config import Settings
from src.database import get_async_session
from src.example.models import Example
from src.main import app


# =============================================================================
# Константы и настройки тестовой базы данных
# =============================================================================

TEST_DB_NAME = "local_db"


def get_test_settings() -> Settings:
    """Создает настройки для тестовой базы данных."""
    import os

    # Базовые настройки из переменных окружения или значений по умолчанию
    postgres_server = os.getenv("POSTGRES_SERVER", "localhost")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user = os.getenv("POSTGRES_USER", "fastapi_starter_test")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "1234")

    return Settings(
        ENVIRONMENT="local",
        PROJECT_NAME="Test Project",
        POSTGRES_SERVER=postgres_server,
        POSTGRES_PORT=postgres_port,
        POSTGRES_USER=postgres_user,
        POSTGRES_PASSWORD=postgres_password,
        POSTGRES_DB=TEST_DB_NAME,
    )


test_settings = get_test_settings()


# =============================================================================
# Управление базой данных
# =============================================================================


async def create_test_database() -> None:
    """Создает тестовую базу данных, если она не существует."""
    # Подключаемся к postgres (системной БД) для создания тестовой БД
    system_dsn = PostgresDsn.build(
        scheme="postgresql+asyncpg",
        username=test_settings.POSTGRES_USER,
        password=test_settings.POSTGRES_PASSWORD,
        host=test_settings.POSTGRES_SERVER,
        port=test_settings.POSTGRES_PORT,
        path="postgres",
    )

    engine = create_async_engine(str(system_dsn), isolation_level="AUTOCOMMIT")

    async with engine.connect() as conn:
        # Проверяем существование базы данных
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'")
        )
        exists = result.scalar() is not None

        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))

    await engine.dispose()


async def drop_test_database() -> None:
    """Удаляет тестовую базу данных."""
    system_dsn = PostgresDsn.build(
        scheme="postgresql+asyncpg",
        username=test_settings.POSTGRES_USER,
        password=test_settings.POSTGRES_PASSWORD,
        host=test_settings.POSTGRES_SERVER,
        port=test_settings.POSTGRES_PORT,
        path="postgres",
    )

    engine = create_async_engine(str(system_dsn), isolation_level="AUTOCOMMIT")

    async with engine.connect() as conn:
        # Отключаем все активные подключения к тестовой БД
        await conn.execute(
            text(
                f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
                AND pid <> pg_backend_pid()
                """
            )
        )
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'))

    await engine.dispose()


def run_alembic_migrations() -> None:
    """Запускает миграции alembic для тестовой базы данных."""
    alembic_cfg = Config("alembic.ini")

    # Устанавливаем URL тестовой базы данных
    alembic_cfg.set_main_option("sqlalchemy.url", str(test_settings.SQLALCHEMY_DATABASE_URI))

    # Сначала откатываем все миграции (если есть)
    try:
        command.downgrade(alembic_cfg, "base")
    except Exception:
        pass  # Игнорируем ошибки, если миграций нет

    # Применяем миграции до последней версии
    command.upgrade(alembic_cfg, "head")


async def clear_tables() -> None:
    """Очищает все таблицы в тестовой базе данных."""
    engine = create_async_engine(str(test_settings.SQLALCHEMY_DATABASE_URI))

    async with engine.begin() as conn:
        # Получаем список всех таблиц
        result = await conn.execute(
            text(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                """
            )
        )
        tables = [row[0] for row in result.fetchall()]

        # Очищаем все таблицы
        for table in tables:
            await conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))

    await engine.dispose()


# =============================================================================
# Engine и Session для тестов
# =============================================================================

test_engine = create_async_engine(
    str(test_settings.SQLALCHEMY_DATABASE_URI),
    pool_size=5,
    max_overflow=10,
    echo=False,
)

test_async_session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Создает event loop для всей сессии тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database() -> AsyncGenerator[None, None]:
    """
    Фикстура для настройки тестовой базы данных.

    Выполняется один раз за сессию:
    1. Создает тестовую базу данных
    2. Запускает миграции alembic
    3. После завершения всех тестов удаляет базу данных
    """
    # Создаем тестовую базу данных
    await create_test_database()

    # Запускаем миграции
    run_alembic_migrations()

    yield

    # Удаляем тестовую базу данных после всех тестов
    await drop_test_database()


@pytest.fixture(autouse=True)
async def reset_database() -> AsyncGenerator[None, None]:
    """
    Фикстура для очистки данных между тестами.

    Выполняется перед каждым тестом:
    - Очищает все таблицы
    - Генерирует свежие тестовые данные
    """
    # Очищаем таблицы перед каждым тестом
    await clear_tables()

    # Генерируем тестовые данные
    await generate_test_data()

    yield


async def generate_test_data() -> None:
    """Генерирует тестовые данные для всех таблиц."""
    async with test_async_session_factory() as session:
        # Создаем тестовые записи для Example
        example1 = Example(
            email="test1@example.com",
            name="Test User 1",
            full_name="Test User One",
            hashed_password="hashed_password_1",
            is_active=True,
        )
        example2 = Example(
            email="test2@example.com",
            name="Test User 2",
            full_name="Test User Two",
            hashed_password="hashed_password_2",
            is_active=True,
        )
        example_inactive = Example(
            email="inactive@example.com",
            name="Inactive User",
            full_name="Inactive Test User",
            hashed_password="hashed_password_inactive",
            is_active=False,
        )

        session.add_all([example1, example2, example_inactive])
        await session.commit()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Фикстура для получения сессии базы данных.

    Yields:
        AsyncSession: Асинхронная сессия для работы с БД
    """
    async with test_async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Фикстура для асинхронного HTTP-клиента.

    Переопределяет зависимость get_async_session для использования
    тестовой сессии базы данных.

    Yields:
        AsyncClient: Асинхронный HTTP-клиент для тестирования API
    """

    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # Переопределяем зависимость
    app.dependency_overrides[get_async_session] = override_get_async_session

    # Создаем тестовый клиент
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Очищаем переопределения зависимостей
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings_fixture() -> Settings:
    """
    Фикстура для получения настроек тестовой базы данных.

    Returns:
        Settings: Настройки для тестов
    """
    return test_settings


# =============================================================================
# Дополнительные утилиты для тестов
# =============================================================================


@pytest.fixture
async def example_data(db_session: AsyncSession) -> dict[str, Example]:
    """
    Фикстура, возвращающая словарь с тестовыми данными Example.

    Returns:
        dict: Словарь с предустановленными тестовыми записями
    """
    result = await db_session.execute(
        text("SELECT * FROM example WHERE email LIKE '%@example.com'")
    )
    examples = result.fetchall()

    return {
        "active_user_1": examples[0] if len(examples) > 0 else None,
        "active_user_2": examples[1] if len(examples) > 1 else None,
        "inactive_user": examples[2] if len(examples) > 2 else None,
    }
