from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime

# Для создания
class ExampleCreate(SQLModel):
    email: str
    name: str
    full_name: str
    password: str

# Для обновления
class ExampleUpdate(SQLModel):
    email: Optional[str] = None
    name: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

# Для ответа
class ExampleRead(SQLModel):
    id: int
    email: str
    name: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]