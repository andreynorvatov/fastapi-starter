import asyncio
import os
import sys
from asyncio import AbstractEventLoop
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Добавляем корневую директорию в Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# Фикстура для приложения FastAPI
@pytest.fixture
def app() -> FastAPI:
    """Создает и возвращает экземпляр FastAPI приложения."""
    from src.main import app

    return app


# Фикстура для синхронного тестового клиента
@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Создает синхронный тестовый клиент."""
    return TestClient(app)


# Асинхронная фикстура для асинхронного тестового клиента
@pytest_asyncio.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """Создает асинхронный тестовый клиент."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# Фикстура для event loop
@pytest.fixture(scope="session")
def event_loop() -> Generator[AbstractEventLoop]:
    """Создает event loop для асинхронных тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# # Пример фикстуры для заголовков аутентификации
# @pytest.fixture
# def auth_headers():
#     """Возвращает заголовки для аутентификации."""
#     return {
#         "Authorization": "Bearer test-token",
#         "Content-Type": "application/json"
#     }
#
#
# # Фикстура для тестовых данных
# @pytest.fixture
# def test_user_data():
#     """Возвращает тестовые данные пользователя."""
#     return {
#         "username": "testuser",
#         "email": "test@example.com",
#         "password": "testpassword123"
#     }
#
#
# # Фикстура для мока внешнего сервиса
# @pytest.fixture
# def mock_external_service(monkeypatch):
#     """Мокает вызов внешнего сервиса."""
#
#     async def mock_get_data(*args, **kwargs):
#         return {"mock": "data", "status": "success"}
#
#     monkeypatch.setattr("your_module.external_service_function", mock_get_data)
#
#
# # Асинхронная фикстура для временных данных
# @pytest_asyncio.fixture
# async def temporary_data():
#     """Создает временные данные для теста и очищает после."""
#     data = {"temp_id": 123, "name": "test"}
#
#     yield data
#
#     # Очистка после теста
#     await asyncio.sleep(0.1)  # Имитация асинхронной очистки
#
#
# # Фикстура для настройки тестовой среды
# @pytest.fixture(autouse=True)
# def setup_test_environment():
#     """Автоматически настраивает тестовую среду для каждого теста."""
#     # Настройки перед тестом
#     print("Setting up test environment...")
#
#     yield
#
#     # Очистка после теста
#     print("Cleaning up test environment...")
#
#
# # Конфигурация pytest
# def pytest_configure(config):
#     """Конфигурация pytest."""
#     config.addinivalue_line(
#         "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
#     )
#     config.addinivalue_line(
#         "markers", "integration: marks tests as integration tests"
#     )
#
#
# # Фильтр для отбора тестов
# def pytest_collection_modifyitems(config, items):
#     """Модифицирует коллекцию тестов."""
#     # Пример: пропускать тесты с маркером slow по умолчанию
#     if config.getoption("--runslow"):
#         # --runslow задан в командной строке, не пропускать медленные тесты
#         return
#
#     skip_slow = pytest.mark.skip(reason="need --runslow option to run")
#     for item in items:
#         if "slow" in item.keywords:
#             item.add_marker(skip_slow)
