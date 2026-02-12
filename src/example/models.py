from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from src.model_mixins import TimestampMixin


class Example(SQLModel, TimestampMixin, table=True):
    __tablename__ = "example"

    id: int | None = Field(default=None, primary_key=True, description="Уникальный идентификатор записи")
    email: EmailStr = Field(index=True, unique=True, max_length=255, description="Электронная почта")
    name: str = Field(index=True, max_length=50, description="Имя пользователя")
    full_name: str = Field(max_length=100, description="Полное имя пользователя")
    hashed_password: str = Field(max_length=255, description="Хэшированный пароль пользователя")
    is_active: bool = Field(default=True, description="Статус активности пользователя")
