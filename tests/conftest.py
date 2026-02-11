import pytest
from collections.abc import AsyncGenerator, Generator
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pydantic import PostgresDsn
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.config import Settings
from src.database import get_async_session
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
# Управление базой данных (СИНХРОННЫЕ операции для подготовки)
# =============================================================================


def create_test_database_sync() -> None:
    """
    Синхронно создает тестовую базу данных, если она не существует.
    Использует синхронное подключение к postgres.
    """
    import psycopg

    system_dsn = PostgresDsn.build(
        scheme="postgresql",
        username=test_settings.POSTGRES_USER,
        password=test_settings.POSTGRES_PASSWORD,
        host=test_settings.POSTGRES_SERVER,
        port=test_settings.POSTGRES_PORT,
        path="postgres",
    )

    with psycopg.connect(str(system_dsn), autocommit=True) as conn:
        with conn.cursor() as cur:
            # Проверяем существование базы данных
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'")
            exists = cur.fetchone() is not None

            if not exists:
                cur.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')


def drop_all_tables() -> None:
    """
    Удаляет все таблицы в тестовой базе данных.
    Использует параметры из Settings для подключения и определения схемы.
    """
    import psycopg

    # Формируем DSN для подключения к тестовой базе данных
    sync_dsn = PostgresDsn.build(
        scheme="postgresql",
        username=test_settings.POSTGRES_USER,
        password=test_settings.POSTGRES_PASSWORD,
        host=test_settings.POSTGRES_SERVER,
        port=test_settings.POSTGRES_PORT,
        path=test_settings.POSTGRES_DB,
    )

    # Используем схему из настроек (POSTGRES_USER)
    schema = test_settings.POSTGRES_USER

    with psycopg.connect(str(sync_dsn), autocommit=True) as conn:
        with conn.cursor() as cur:
            # Получаем список всех таблиц в схеме пользователя
            cur.execute(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = %s
                """,
                (schema,)
            )
            tables = [row[0] for row in cur.fetchall()]

            if tables:
                # Удаляем все таблицы с указанием схемы
                for table in tables:
                    cur.execute(f'DROP TABLE IF EXISTS "{schema}"."{table}" CASCADE')


def run_alembic_migrations() -> None:
    """Запускает миграции alembic для тестовой базы данных."""
    alembic_cfg = Config("alembic.ini")

    # Устанавливаем URL тестовой базы данных (синхронный драйвер psycopg)
    sync_url = str(test_settings.SQLALCHEMY_DATABASE_URI).replace(
        "postgresql+asyncpg", "postgresql+psycopg"
    )
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

    # Сначала удаляем все таблицы (если есть) для чистого запуска миграций
    drop_all_tables()

    # Применяем миграции до последней версии
    command.upgrade(alembic_cfg, "head")


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> Generator[None, None, None]:
    """
    СИНХРОННАЯ фикстура для настройки тестовой базы данных.

    Выполняется один раз за сессию:
    1. Создает тестовую базу данных (синхронно)
    2. Запускает миграции alembic (синхронно)
    3. После завершения всех тестов удаляет все таблицы (синхронно)
    """
    # Создаем тестовую базу данных (синхронно)
    create_test_database_sync()

    # Запускаем миграции (синхронно)
    run_alembic_migrations()

    yield

    # Удаляем все таблицы после завершения всех тестов
    drop_all_tables()


async def clear_tables_async(session: AsyncSession) -> None:
    """
    Асинхронно очищает все таблицы в тестовой базе данных.
    Динамически получает список всех таблиц в схеме пользователя и очищает их.
    """
    schema = test_settings.POSTGRES_USER
    
    # Получаем список всех таблиц в схеме пользователя
    result = await session.execute(
        text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = :schema
        """),
        {"schema": schema}
    )
    tables = [row[0] for row in result.fetchall()]
    
    if tables:
        # Формируем SQL для очистки всех таблиц с указанием схемы
        tables_str = ", ".join(f'"{schema}"."{table}"' for table in tables)
        await session.execute(text(f"TRUNCATE TABLE {tables_str} RESTART IDENTITY CASCADE"))
        await session.commit()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Фикстура для получения сессии базы данных.
    
    Engine создаётся внутри фикстуры, чтобы гарантировать
    создание в правильном event loop (pytest-asyncio создаёт
    новый loop для каждого теста при asyncio_mode="auto").
    
    Очищает данные перед тестом и после теста для изоляции.

    Yields:
        AsyncSession: Асинхронная сессия для работы с БД
    """
    # Создаём engine внутри фикстуры, в правильном event loop
    engine = create_async_engine(
        str(test_settings.SQLALCHEMY_DATABASE_URI),
        poolclass=NullPool,  # Отключаем пулинг - каждое соединение создаётся в текущем loop
        echo=False,
    )
    
    async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_factory() as session:
        # Очищаем таблицы перед каждым тестом
        await clear_tables_async(session)
        
        try:
            yield session
        finally:
            # Очищаем данные после теста для изоляции
            await clear_tables_async(session)
            await session.close()
            await engine.dispose()


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
