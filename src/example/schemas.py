from datetime import datetime

from sqlmodel import SQLModel


# Для создания
class ExampleCreate(SQLModel):
    email: str
    name: str
    full_name: str
    password: str


# Для обновления
class ExampleUpdate(SQLModel):
    email: str | None = None
    name: str | None = None
    full_name: str | None = None
    is_active: bool | None = None


# Для ответа
class ExampleRead(SQLModel):
    id: int
    email: str
    name: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
