from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.dependencies import get_db_connection
from src.example.crud import create_example, get_example_by_email
from src.example.models import Example
from src.example.schemas import ExampleCreate, ExampleRead

example_router = APIRouter()


@example_router.post("/create", response_model=ExampleRead)
async def create_example_endpoint(
    example: ExampleCreate, session: AsyncSession = Depends(get_db_connection)
) -> Example:
    # Проверка существования пользователя
    db_example = await get_example_by_email(session, example.email)
    if db_example:
        raise HTTPException(status_code=400, detail="Email already registered")

    return await create_example(session, example)


@example_router.get("/get/{example_id}", response_model=ExampleRead)
async def read_example(example_id: int, session: AsyncSession = Depends(get_db_connection)) -> Example:
    example = await session.get(Example, example_id)
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    return example.model_validate(example)


@example_router.get("/get-all", response_model=list[ExampleRead])
async def read_examples(
    skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_db_connection)
) -> list[ExampleRead]:
    statement = select(Example).offset(skip).limit(limit)
    result = await session.execute(statement)
    examples = result.scalars().all()
    return [ExampleRead.model_validate(example) for example in examples]
