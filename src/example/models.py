from datetime import datetime

from sqlmodel import Field, SQLModel


class Example(SQLModel, table=True):
    __tablename__ = "example"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    name: str = Field(index=True, max_length=50)
    full_name: str = Field(max_length=100)
    hashed_password: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(
        default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow}
    )
