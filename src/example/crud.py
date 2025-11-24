from sqlmodel import Session, select
from src.example.models import Example
from src.example.schemas import ExampleCreate
from sqlalchemy.ext.asyncio import AsyncSession

async def get_example_by_email(session: AsyncSession, email: str) -> Example | None:
    statement = select(Example).where(Example.email == email)
    result = await session.execute(statement)
    return result.scalars().first()

async def create_example(session: AsyncSession, example_create: ExampleCreate) -> Example:
    hashed_password = hash(example_create.password)

    example = Example(
        email=example_create.email,
        name=example_create.name,
        full_name=example_create.full_name,
        hashed_password=hashed_password
    )

    session.add(example)
    await session.commit()
    await session.refresh(example)
    return example