"""Общие схемы для API."""

from typing import Generic, TypeVar

from sqlmodel import SQLModel

T = TypeVar("T")


class PaginatedResponse(SQLModel, Generic[T]):
    """
    Универсальная схема для пагинированного ответа.
    
    Attributes:
        items: Список элементов текущей страницы
        total: Общее количество элементов
        skip: Количество пропущенных элементов
        limit: Максимальное количество элементов на странице
    """
    items: list[T]
    total: int
    skip: int
    limit: int
