from datetime import datetime

from pydantic import EmailStr
from sqlmodel import SQLModel


# Для создания
class ExampleCreate(SQLModel):
    """Схема для создания пользователя."""
    email: EmailStr
    name: str
    full_name: str
    password: str


# Для обновления
class ExampleUpdate(SQLModel):
    """Схема для обновления пользователя."""
    email: EmailStr | None = None
    name: str | None = None
    full_name: str | None = None
    is_active: bool | None = None


# Для ответа
class ExampleRead(SQLModel):
    """Схема для чтения пользователя."""
    id: int
    email: EmailStr
    name: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
