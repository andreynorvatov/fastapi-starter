"""
Фабрика для генерации тестовых данных модели Example.

Содержит методы для создания одиночных и множественных экземпляров
модели Example с предустановленными пресетами.
"""

from typing import Sequence

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.example.models import Example

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ExampleFactory:
    """
    Фабрика для создания тестовых данных модели Example.

    Предоставляет методы для создания одиночных экземпляров и пакетов,
    а также пресеты для типичных сценариев тестирования.
    """

    @staticmethod
    async def create(
        session: AsyncSession,
        email: str,
        name: str,
        full_name: str,
        password: str = "default_password",
        is_active: bool = True,
    ) -> Example:
        """
        Создаёт один экземпляр Example и сохраняет в БД.

        Args:
            session: Асинхронная сессия БД
            email: Email пользователя
            name: Краткое имя
            full_name: Полное имя
            password: Пароль (будет хеширован)
            is_active: Флаг активности

        Returns:
            Созданный экземпляр Example
        """
        hashed_password = pwd_context.hash(password)
        example = Example(
            email=email,
            name=name,
            full_name=full_name,
            hashed_password=hashed_password,
            is_active=is_active,
        )
        session.add(example)
        await session.commit()
        await session.refresh(example)
        return example

    @staticmethod
    async def create_batch(
        session: AsyncSession,
        examples_data: Sequence[dict],
    ) -> list[Example]:
        """
        Создаёт несколько экземпляров Example и сохраняет в БД.

        Args:
            session: Асинхронная сессия БД
            examples_data: Список словарей с данными для создания Example

        Returns:
            Список созданных экземпляров Example
        """
        examples = []
        for data in examples_data:
            password = data.get("password", "default_password")
            hashed_password = pwd_context.hash(password)
            example = Example(
                email=data["email"],
                name=data["name"],
                full_name=data["full_name"],
                hashed_password=hashed_password,
                is_active=data.get("is_active", True),
            )
            session.add(example)
            examples.append(example)

        await session.commit()

        # Refresh all examples to get their IDs
        for example in examples:
            await session.refresh(example)

        return examples

    @staticmethod
    async def create_active_user(
        session: AsyncSession,
        email: str = "active@example.com",
        name: str = "Active User",
        full_name: str = "Active Test User",
    ) -> Example:
        """
        Создаёт активного пользователя (пресет active_user).

        Args:
            session: Асинхронная сессия БД
            email: Email пользователя
            name: Краткое имя
            full_name: Полное имя

        Returns:
            Созданный экземпляр Example с is_active=True
        """
        return await ExampleFactory.create(
            session=session,
            email=email,
            name=name,
            full_name=full_name,
            password="active_password",
            is_active=True,
        )

    @staticmethod
    async def create_inactive_user(
        session: AsyncSession,
        email: str = "inactive@example.com",
        name: str = "Inactive User",
        full_name: str = "Inactive Test User",
    ) -> Example:
        """
        Создаёт неактивного пользователя (пресет inactive_user).

        Args:
            session: Асинхронная сессия БД
            email: Email пользователя
            name: Краткое имя
            full_name: Полное имя

        Returns:
            Созданный экземпляр Example с is_active=False
        """
        return await ExampleFactory.create(
            session=session,
            email=email,
            name=name,
            full_name=full_name,
            password="inactive_password",
            is_active=False,
        )

    @staticmethod
    def get_default_test_data() -> list[dict]:
        """
        Возвращает список тестовых данных по умолчанию.

        Используется для создания стандартного набора тестовых данных,
        который применялся в оригинальной функции generate_test_data_async.

        Returns:
            Список словарей с данными для создания Example
        """
        return [
            {
                "email": "test1@example.com",
                "name": "Test User 1",
                "full_name": "Test User One",
                "password": "password_1",
                "is_active": True,
            },
            {
                "email": "test2@example.com",
                "name": "Test User 2",
                "full_name": "Test User Two",
                "password": "password_2",
                "is_active": True,
            },
            {
                "email": "inactive@example.com",
                "name": "Inactive User",
                "full_name": "Inactive Test User",
                "password": "password_inactive",
                "is_active": False,
            },
        ]
