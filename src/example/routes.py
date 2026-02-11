from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.database import get_async_session
from src.example.crud import create_example, get_example_by_email, get_examples_count, delete_example
from src.example.models import Example
from src.example.schemas import ExampleCreate, ExampleRead
from src.schemas import PaginatedResponse

example_router = APIRouter()


@example_router.post("/create", response_model=ExampleRead)
async def create_example_endpoint(
    example: ExampleCreate, session: AsyncSession = Depends(get_async_session)
) -> Example:
    """Создание нового пользователя."""
    db_example = await get_example_by_email(session, example.email)
    if db_example:
        raise HTTPException(status_code=400, detail="Email already registered")

    return await create_example(session, example)


@example_router.get("/get/{example_id}", response_model=ExampleRead)
async def read_example(example_id: int, session: AsyncSession = Depends(get_async_session)) -> Example:
    """Получение пользователя по ID."""
    example = await session.get(Example, example_id)
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    return example


@example_router.get("/get-all", response_model=PaginatedResponse[ExampleRead])
async def read_examples(
    skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_async_session)
) -> PaginatedResponse[ExampleRead]:
    """Получение списка пользователей с пагинацией."""
    statement = select(Example).offset(skip).limit(limit)
    result = await session.execute(statement)
    examples = result.scalars().all()
    
    total = await get_examples_count(session)
    
    return PaginatedResponse(
            items=[ExampleRead.model_validate(example) for example in examples],
            total=total,
            skip=skip,
            limit=limit,
        )
    
@example_router.delete("/delete/{example_id}", status_code=204)
async def delete_example_endpoint(example_id: int, session: AsyncSession = Depends(get_async_session)):
    """Удаляет запись по ID."""
    await delete_example(session, example_id)
    return
