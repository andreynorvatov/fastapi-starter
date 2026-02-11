"""
Тесты для сервиса Example.

Содержит тесты для:
- CRUD операций (get_example_by_email, create_example)
- API эндпоинтов (create, get, get-all)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.example.crud import create_example, get_example_by_email
from src.example.models import Example
from src.example.schemas import ExampleCreate


# =============================================================================
# Тесты CRUD функций
# =============================================================================


class TestGetExampleByEmail:
    """Тесты для функции get_example_by_email."""

    @pytest.mark.asyncio
    async def test_get_example_by_email_existing(
        self, db_session: AsyncSession, example_test_data: list[Example]
    ) -> None:
        """Тест поиска существующего пользователя по email."""
        # Используем данные из example_test_data (test1@example.com)
        result = await get_example_by_email(db_session, "test1@example.com")

        assert result is not None
        assert result.email == "test1@example.com"
        assert result.name == "Test User 1"
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_get_example_by_email_not_existing(self, db_session: AsyncSession) -> None:
        """Тест поиска несуществующего пользователя по email."""
        result = await get_example_by_email(db_session, "nonexistent@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_example_by_email_inactive_user(
        self, db_session: AsyncSession, example_test_data: list[Example]
    ) -> None:
        """Тест поиска неактивного пользователя по email."""
        result = await get_example_by_email(db_session, "inactive@example.com")

        assert result is not None
        assert result.email == "inactive@example.com"
        assert result.is_active is False


class TestCreateExample:
    """Тесты для функции create_example."""

    @pytest.mark.asyncio
    async def test_create_example_success(self, db_session: AsyncSession) -> None:
        """Тест успешного создания пользователя."""
        example_create = ExampleCreate(
            email="new@example.com",
            name="New User",
            full_name="New Test User",
            password="plain_password",
        )

        result = await create_example(db_session, example_create)

        assert result.id is not None
        assert result.email == "new@example.com"
        assert result.name == "New User"
        assert result.full_name == "New Test User"
        assert result.hashed_password != "plain_password"  # Пароль должен быть хеширован
        assert result.hashed_password.startswith("$2b$")  # bcrypt hash format
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_create_example_persists_in_db(self, db_session: AsyncSession) -> None:
        """Тест что созданный пользователь сохраняется в БД."""
        example_create = ExampleCreate(
            email="persist@example.com",
            name="Persist User",
            full_name="Persist Test User",
            password="password123",
        )

        created = await create_example(db_session, example_create)

        # Проверяем что запись можно найти по email
        found = await get_example_by_email(db_session, "persist@example.com")
        assert found is not None
        assert found.id == created.id
        assert found.email == created.email


# =============================================================================
# Тесты API эндпоинтов
# =============================================================================


class TestCreateExampleEndpoint:
    """Тесты для POST /example/create эндпоинта."""

    @pytest.mark.asyncio
    async def test_create_example_endpoint_success(self, client: AsyncClient) -> None:
        """Тест успешного создания пользователя через API."""
        payload = {
            "email": "api_new@example.com",
            "name": "API User",
            "full_name": "API Test User",
            "password": "secure_password",
        }

        response = await client.post("/example/create", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "api_new@example.com"
        assert data["name"] == "API User"
        assert data["full_name"] == "API Test User"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_example_endpoint_duplicate_email(
        self, client: AsyncClient, example_test_data: list[Example]
    ) -> None:
        """Тест создания пользователя с дублирующимся email."""
        payload = {
            "email": "test1@example.com",  # Уже существует из example_test_data
            "name": "Duplicate User",
            "full_name": "Duplicate Test User",
            "password": "password",
        }

        response = await client.post("/example/create", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    @pytest.mark.asyncio
    async def test_create_example_endpoint_missing_fields(self, client: AsyncClient) -> None:
        """Тест создания пользователя с отсутствующими полями."""
        payload = {
            "email": "incomplete@example.com",
            "name": "Incomplete User",
            # Отсутствуют full_name и password
        }

        response = await client.post("/example/create", json=payload)

        assert response.status_code == 422  # Validation error


class TestReadExampleEndpoint:
    """Тесты для GET /example/get/{example_id} эндпоинта."""

    @pytest.mark.asyncio
    async def test_read_example_existing(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        example_test_data: list[Example],
    ) -> None:
        """Тест получения существующего пользователя по ID."""
        # Получаем пользователя из БД через CRUD функцию
        user = await get_example_by_email(db_session, "test1@example.com")
        assert user is not None, "Тестовый пользователь должен существовать в БД"
        user_id = user.id

        response = await client.get(f"/example/get/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "test1@example.com"

    @pytest.mark.asyncio
    async def test_read_example_not_found(self, client: AsyncClient) -> None:
        """Тест получения несуществующего пользователя."""
        response = await client.get("/example/get/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Example not found"

    @pytest.mark.asyncio
    async def test_read_example_invalid_id(self, client: AsyncClient) -> None:
        """Тест получения пользователя с некорректным ID."""
        response = await client.get("/example/get/invalid")

        assert response.status_code == 422  # Validation error


class TestReadExamplesEndpoint:
    """Тесты для GET /example/get-all эндпоинта."""

    @pytest.mark.asyncio
    async def test_read_examples_default_params(
        self, client: AsyncClient, example_test_data: list[Example]
    ) -> None:
        """Тест получения списка пользователей с параметрами по умолчанию."""
        response = await client.get("/example/get-all")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        # Должны быть 3 записи из example_test_data
        assert len(data["items"]) == 3
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_read_examples_with_pagination(
        self, client: AsyncClient, example_test_data: list[Example]
    ) -> None:
        """Тест получения списка пользователей с пагинацией."""
        # Получаем только 2 записи
        response = await client.get("/example/get-all?skip=0&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["skip"] == 0
        assert data["limit"] == 2

    @pytest.mark.asyncio
    async def test_read_examples_with_skip(
        self, client: AsyncClient, example_test_data: list[Example]
    ) -> None:
        """Тест получения списка пользователей с пропуском записей."""
        # Пропускаем первую запись
        response = await client.get("/example/get-all?skip=1&limit=10")

        assert response.status_code == 200
        data = response.json()
        # Должны получить 2 записи (пропустили 1 из 3)
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["skip"] == 1

    @pytest.mark.asyncio
    async def test_read_examples_empty_result(self, client: AsyncClient) -> None:
        """Тест получения пустого списка при большом skip."""
        response = await client.get("/example/get-all?skip=100&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_read_examples_response_structure(
        self, client: AsyncClient, example_test_data: list[Example]
    ) -> None:
        """Тест структуры ответа списка пользователей."""
        response = await client.get("/example/get-all")

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert "id" in item
            assert "email" in item
            assert "name" in item
            assert "full_name" in item
            assert "is_active" in item
            assert "created_at" in item
            assert "updated_at" in item
            # hashed_password не должен быть в ответе
            assert "hashed_password" not in item

class TestDeleteExampleEndpoint:
    """Тесты для DELETE /example/delete/{example_id} эндпоинта."""

    @pytest.mark.asyncio
    async def test_delete_example_success(self, client: AsyncClient, db_session: AsyncSession, example_test_data: list[Example]):
        # Удаление первого Example
        example_id = example_test_data[0].id
        response = await client.delete(f"/example/delete/{example_id}")
        assert response.status_code == 204

        # Проверка удаления из БД
        from src.example.crud import get_example_by_email
        deleted = await get_example_by_email(db_session, example_test_data[0].email)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_example_not_found(self, client: AsyncClient):
        response = await client.delete("/example/delete/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Example not found"


class TestUpdateExampleEndpoint:
    """Тесты для PUT /example/update/{example_id} эндпоинта."""

    @pytest.mark.asyncio
    async def test_update_example_success(self, client: AsyncClient, db_session: AsyncSession, example_test_data: list[Example]):
        # Обновляем первое Example
        example_id = example_test_data[0].id
        payload = {
            "name": "Updated Name",
            "full_name": "Updated Full Name",
            "is_active": False
        }
        response = await client.put(f"/example/update/{example_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == example_id
        assert data["name"] == "Updated Name"
        assert data["full_name"] == "Updated Full Name"
        assert data["is_active"] is False
        # Проверяем, что запись в БД обновилась
        from src.example.crud import get_example_by_email
        updated = await get_example_by_email(db_session, example_test_data[0].email)
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.full_name == "Updated Full Name"
        assert updated.is_active is False

    @pytest.mark.asyncio
    async def test_update_example_not_found(self, client: AsyncClient):
        payload = {"name": "Doesn't matter"}
        response = await client.put("/example/update/99999", json=payload)
        assert response.status_code == 404
        assert response.json()["detail"] == "Example not found"

    @pytest.mark.asyncio
    async def test_update_example_invalid_id(self, client: AsyncClient):
        payload = {"name": "Invalid"}
        response = await client.put("/example/update/invalid", json=payload)
        assert response.status_code == 422

