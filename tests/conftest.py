import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

import sys
from pathlib import Path

_ROOT_DIRECTORY: Path = Path(__file__).resolve().parent.parent
sys.path.append(str(_ROOT_DIRECTORY))

# Импортируем приложения и модели
from src.main import app
from src.example.models import SQLModel
from src.dependencies import get_db_connection
from src.config import init_settings, Settings

settings = init_settings(".env.test")

# Тестовая база данных
TEST_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)

# Создаем асинхронный движок для тестов
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=0
)

# Создаем фабрику сессий
AsyncTestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Переопределенная зависимость для получения сессии БД"""
    async with AsyncTestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Фикстура для event loop на всю сессию"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Создание и очистка тестовой базы данных"""
    # Создаем все таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    # Очищаем после тестов
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для тестовой сессии БД"""
    async with AsyncTestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
def client(db_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Фикстура для тестового клиента FastAPI"""

    # Подменяем зависимость get_db
    app.dependency_overrides[get_db_connection] = lambda: db_session

    with TestClient(app) as test_client:
        yield test_client

    # Очищаем подмены после теста
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для асинхронного тестового клиента"""

    # Подменяем зависимость get_db
    app.dependency_overrides[get_db_connection] = lambda: db_session

    # Создаем асинхронный клиент
    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as client:
        yield client

    # Очищаем подмены после теста
    app.dependency_overrides.clear()


# # Фикстуры для тестовых данных
# @pytest_asyncio.fixture
# async def test_user(db_session: AsyncSession):
#     """Создание тестового пользователя"""
#     from app.models.user import User
#     from app.schemas.user import UserCreate
#
#     user_data = UserCreate(
#         email="test@example.com",
#         username="testuser",
#         password="testpassword123"
#     )
#
#     user = User(
#         email=user_data.email,
#         username=user_data.username,
#         hashed_password=user_data.password  # В реальном коде хэшируйте пароль
#     )
#
#     db_session.add(user)
#     await db_session.commit()
#     await db_session.refresh(user)
#
#     return user
#

# @pytest_asyncio.fixture
# async def authenticated_client(client: TestClient, test_user):
#     """Клиент с аутентификацией"""
#     # Получаем токен
#     login_data = {
#         "username": test_user.email,
#         "password": "testpassword123"
#     }
#
#     response = client.post("/auth/login", data=login_data)
#     token = response.json()["access_token"]
#
#     # Устанавливаем заголовок авторизации
#     client.headers.update({"Authorization": f"Bearer {token}"})
#
#     return client
#

# # Фикстуры для моков
# @pytest.fixture
# def mock_external_service():
#     """Мок внешнего сервиса"""
#     from unittest.mock import MagicMock
#
#     mock = MagicMock()
#     mock.get_data.return_value = {"status": "success", "data": "mocked"}
#
#     return mock
#
#
# # Опционально: фикстура для заглушек зависимостей
# @pytest.fixture(autouse=True)
# def mock_dependencies(monkeypatch):
#     """Автоматическая заглушка внешних зависимостей"""
#     # Пример: заглушка отправки email
#     monkeypatch.setattr(
#         "app.services.email.send_email",
#         lambda *args, **kwargs: None
#     )
#
#     # Пример: заглушка кэша
#     monkeypatch.setattr(
#         "app.core.cache.redis_client",
#         None  # или мок-объект
#     )
#
#
# # Хуки для улучшения отчетов
# def pytest_sessionfinish(session, exitstatus):
#     """Вызывается в конце тестовой сессии"""
#     print(f"\n{'=' * 50}")
#     print(f"Тесты завершены со статусом: {exitstatus}")
#     print(f"{'=' * 50}")
#
#
# # Конфигурация pytest
# def pytest_configure(config):
#     """Конфигурация pytest"""
#     config.addinivalue_line(
#         "markers",
#         "slow: маркировка медленных тестов"
#     )
#     config.addinivalue_line(
#         "markers",
#         "integration: интеграционные тесты"
#     )
#     config.addinivalue_line(
#         "markers",
#         "e2e: end-to-end тесты"
#     )