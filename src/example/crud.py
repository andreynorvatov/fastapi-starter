from passlib.context import CryptContext
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.example.models import Example
from src.example.schemas import ExampleCreate, ExampleUpdate
from fastapi import HTTPException

# Контекст для хеширования паролей с использованием bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_example_by_email(session: AsyncSession, email: str) -> Example | None:
    """Получает пользователя по email."""
    statement = select(Example).where(Example.email == email)
    result = await session.execute(statement)
    return result.scalars().first()


async def get_examples_count(session: AsyncSession) -> int:
    """Возвращает общее количество пользователей."""
    statement = select(func.count(Example.id))
    result = await session.execute(statement)
    return result.scalar() or 0


async def create_example(session: AsyncSession, example_create: ExampleCreate) -> Example:
    """Создает нового пользователя с хешированным паролем."""
    hashed_password = pwd_context.hash(example_create.password)

    example = Example(
        email=example_create.email,
        name=example_create.name,
        full_name=example_create.full_name,
        hashed_password=hashed_password,
    )

    session.add(example)
    await session.commit()
    await session.refresh(example)
    return example


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля и хеша."""
    return pwd_context.verify(plain_password, hashed_password)

async def delete_example(session: AsyncSession, example_id: int) -> None:
    """Удаляет запись по ID."""
    example = await session.get(Example, example_id)
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    await session.delete(example)
    await session.commit()

async def update_example(session: AsyncSession, example_id: int, example_update: ExampleUpdate) -> Example:
    """Обновляет запись Example."""
    db_example = await session.get(Example, example_id)
    if not db_example:
        raise HTTPException(status_code=404, detail="Example not found")
    update_data = example_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_example, key, value)
    session.add(db_example)
    await session.commit()
    await session.refresh(db_example)
    return db_example
