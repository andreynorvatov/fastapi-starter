"""
Локальные фикстуры для тестов сервиса Example.

Содержит фикстуру для генерации тестовых данных модели Example.
"""

import pytest
from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories.example_factory import ExampleFactory


async def clear_example_table(session: AsyncSession, schema: str) -> None:
    """
    Очищает таблицу example в указанной схеме.

    Args:
        session: Асинхронная сессия БД
        schema: Имя схемы БД
    """
    await session.execute(
        text(f'TRUNCATE TABLE "{schema}"."example" RESTART IDENTITY CASCADE')
    )
    await session.commit()


@pytest.fixture
async def example_test_data(db_session: AsyncSession, test_settings_fixture) -> AsyncGenerator[list, None]:
    """
    Фикстура для генерации тестовых данных Example.

    Очищает таблицу example перед и после теста, создаёт стандартный
    набор тестовых данных.

    Args:
        db_session: Асинхронная сессия БД
        test_settings_fixture: Настройки тестовой БД

    Yields:
        Список созданных экземпляров Example
    """
    schema = test_settings_fixture.POSTGRES_USER

    # Очищаем таблицу перед тестом
    await clear_example_table(db_session, schema)

    # Создаём тестовые данные
    test_data = ExampleFactory.get_default_test_data()
    examples = await ExampleFactory.create_batch(db_session, test_data)

    try:
        yield examples
    finally:
        # Очищаем таблицу после теста
        await clear_example_table(db_session, schema)
