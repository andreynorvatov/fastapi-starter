"""CRUD операции для работы с моделью File."""

import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc

from .models import File
from .schemas import FileCreate, FileUpdate


async def create_file(
    session: AsyncSession,
    file_create: FileCreate,
    file_id: uuid.UUID | None = None,
) -> File:
    """Создает новую запись о файле в базе данных.

    Args:
        session: Асинхронная сессия БД
        file_create: Данные для создания записи о файле
        file_id: UUID файла (опционально). Если не указан, генерируется новый.

    Returns:
        Созданный объект File
    """
    db_file = File(
        id=file_id or uuid.uuid4(),
        original_filename=file_create.original_filename,
        file_path=file_create.file_path,
        file_size=file_create.file_size,
        mime_type=file_create.mime_type,
        extension=file_create.extension,
        is_active=file_create.is_active,
    )
    session.add(db_file)
    await session.commit()
    await session.refresh(db_file)
    return db_file


async def get_file_by_uuid(session: AsyncSession, file_uuid) -> File | None:
    """Получает запись о файле по UUID.

    Args:
        session: Асинхронная сессия БД
        file_uuid: UUID файла

    Returns:
        Объект File или None если не найден
    """
    statement = select(File).where(File.id == file_uuid)
    result = await session.execute(statement)
    return result.scalars().first()


async def get_files(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
) -> list[File]:
    """Получает список файлов с пагинацией и опциональной фильтрацией.

    Args:
        session: Асинхронная сессия БД
        skip: Количество записей для пропуска (пагинация)
        limit: Максимальное количество записей
        is_active: Фильтр по статусу активности (None - все)

    Returns:
        Список объектов File
    """
    statement = select(File).order_by(desc(File.created_at)).offset(skip).limit(limit)

    if is_active is not None:
        statement = statement.where(File.is_active == is_active)

    result = await session.execute(statement)
    return result.scalars().all()


async def count_files(session: AsyncSession, is_active: bool | None = None) -> int:
    """Подсчитывает общее количество файлов.

    Args:
        session: Асинхронная сессия БД
        is_active: Фильтр по статусу активности (None - все)

    Returns:
        Количество файлов
    """
    from sqlalchemy import func

    statement = select(func.count(File.id))

    if is_active is not None:
        statement = statement.where(File.is_active == is_active)

    result = await session.execute(statement)
    return result.scalar() or 0


async def update_file(
    session: AsyncSession, file_uuid, file_update: FileUpdate
) -> File | None:
    """Обновляет запись о файле.

    Args:
        session: Асинхронная сессия БД
        file_uuid: UUID файла
        file_update: Данные для обновления

    Returns:
        Обновленный объект File или None если не найден
    """
    db_file = await get_file_by_uuid(session, file_uuid)
    if not db_file:
        return None

    update_data = file_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_file, key, value)

    session.add(db_file)
    await session.commit()
    await session.refresh(db_file)
    return db_file


async def soft_delete_file(session: AsyncSession, file_uuid) -> File | None:
    """Мягко удаляет файл (устанавливает is_active=False).

    Args:
        session: Асинхронная сессия БД
        file_uuid: UUID файла

    Returns:
        Объект File после мягкого удаления или None если не найден
    """
    db_file = await get_file_by_uuid(session, file_uuid)
    if not db_file:
        return None

    db_file.is_active = False
    session.add(db_file)
    await session.commit()
    await session.refresh(db_file)
    return db_file


async def hard_delete_file(session: AsyncSession, file_uuid) -> bool:
    """Физически удаляет запись о файле из базы данных.

    Args:
        session: Асинхронная сессия БД
        file_uuid: UUID файла

    Returns:
        True если запись была удалена, False если не найдена
    """
    db_file = await get_file_by_uuid(session, file_uuid)
    if not db_file:
        return False

    await session.delete(db_file)
    await session.commit()
    return True
