from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from src.model_mixins import TimestampMixin


class Example(SQLModel, TimestampMixin, table=True):
    __tablename__ = "example"

    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(index=True, unique=True, max_length=255)
    name: str = Field(index=True, max_length=50)
    full_name: str = Field(max_length=100)
    hashed_password: str = Field(max_length=255)
    is_active: bool = Field(default=True)
