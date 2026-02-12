"""API routes для файлового хранилища."""

import mimetypes
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from src.database import get_async_session
from src.file_storage.crud import (
    count_files,
    create_file,
    get_file_by_uuid,
    get_files,
    soft_delete_file,
    update_file,
)
from src.file_storage.service import FileStorageService, get_file_storage_service
from src.file_storage.schemas import FileCreate, FileRead, FileUpdate
from src.schemas import PaginatedResponse
from src.logger import logger

file_storage_router = APIRouter()


@file_storage_router.post("/upload", response_model=FileRead)
async def upload_file(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    storage_service: FileStorageService = Depends(get_file_storage_service),
) -> FileRead:
    """Загружает файл в хранилище.

    - Сохраняет файл на диск с UUID как именем
    - Создает запись о файле в базе данных

    Args:
        file: Загружаемый файл
        session: Сессия БД
        storage_service: Сервис файлового хранилища

    Returns:
        Метаданные созданного файла

    Raises:
        HTTPException: При ошибках загрузки
    """
    try:
        # Читаем содержимое файла
        content = await file.read()

        # Генерируем UUID для файла
        import uuid

        file_uuid = uuid.uuid4()

        # Сохраняем файл на диск
        storage_service.save_file(content, file_uuid=file_uuid)

        # Получаем относительный путь к файлу
        # Формат: prefix1/prefix2/uuid
        uuid_str = str(file_uuid).replace("-", "")
        prefix1 = uuid_str[:2]
        prefix2 = uuid_str[2:4]
        relative_path = f"{prefix1}/{prefix2}/{file_uuid}"

        # Определяем расширение из оригинального имени
        original_filename = file.filename or "unnamed"
        extension = None
        if original_filename and "." in original_filename:
            extension = "." + original_filename.split(".")[-1]

        # Создаем запись в БД
        file_create = FileCreate(
            original_filename=original_filename,
            file_path=relative_path,
            file_size=len(content),
            mime_type=file.content_type,
            extension=extension,
            is_active=True,
        )

        db_file = await create_file(session, file_create, file_id=file_uuid)

        logger.info(f"Файл загружен: {original_filename} (UUID: {file_uuid})")
        return FileRead.model_validate(db_file)

    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при загрузке файла")


@file_storage_router.get("/{file_uuid}", response_model=FileRead)
async def get_file_metadata(
    file_uuid,
    session: AsyncSession = Depends(get_async_session),
) -> FileRead:
    """Получает метаданные файла.

    Args:
        file_uuid: UUID файла
        session: Сессия БД

    Returns:
        Метаданные файла

    Raises:
        HTTPException: 404 если файл не найден или не активен
    """
    import uuid as uuid_module

    try:
        file_uuid_obj = uuid_module.UUID(str(file_uuid))
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный UUID")

    db_file = await get_file_by_uuid(session, file_uuid_obj)
    if not db_file or not db_file.is_active:
        raise HTTPException(status_code=404, detail="Файл не найден")

    return FileRead.model_validate(db_file)


@file_storage_router.get("/{file_uuid}/content")
async def download_file(
    file_uuid,
    session: AsyncSession = Depends(get_async_session),
    storage_service: FileStorageService = Depends(get_file_storage_service),
) -> StreamingResponse:
    """Скачивает содержимое файла.

    Args:
        file_uuid: UUID файла
        session: Сессия БД
        storage_service: Сервис файлового хранилища

    Returns:
        StreamingResponse с содержимым файла

    Raises:
        HTTPException: 404 если файл не найден
    """
    import uuid as uuid_module

    try:
        file_uuid_obj = uuid_module.UUID(str(file_uuid))
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный UUID")

    db_file = await get_file_by_uuid(session, file_uuid_obj)
    if not db_file or not db_file.is_active:
        raise HTTPException(status_code=404, detail="Файл не найден")

    try:
        file_path = storage_service.get_file_path(file_uuid_obj)
        file_size = db_file.file_size
        mime_type = db_file.mime_type or "application/octet-stream"
        filename = db_file.original_filename

        # Читаем файл частями для потоковой передачи
        async def file_iterator():
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    yield chunk

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(file_size),
        }

        return StreamingResponse(
            file_iterator(),
            media_type=mime_type,
            headers=headers,
        )

    except FileNotFoundError:
        logger.error(f"Файл не найден на диске: UUID {file_uuid}")
        raise HTTPException(status_code=404, detail="Файл не найден на диске")
    except Exception as e:
        logger.error(f"Ошибка при скачивании файла {file_uuid}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при скачивании файла")


@file_storage_router.get("/", response_model=PaginatedResponse[FileRead])
async def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: bool | None = Query(None),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[FileRead]:
    """Получает список файлов с пагинацией и фильтрацией.

    Args:
        skip: Количество записей для пропуска
        limit: Максимальное количество записей
        is_active: Фильтр по статусу активности (None - все)
        session: Сессия БД

    Returns:
        Пагинированный список метаданных файлов
    """
    files = await get_files(session, skip=skip, limit=limit, is_active=is_active)
    total = await count_files(session, is_active=is_active)

    return PaginatedResponse(
        items=[FileRead.model_validate(file) for file in files],
        total=total,
        skip=skip,
        limit=limit,
    )


@file_storage_router.put("/{file_uuid}", response_model=FileRead)
async def update_file_metadata(
    file_uuid,
    file_update: FileUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> FileRead:
    """Обновляет метаданные файла.

    Args:
        file_uuid: UUID файла
        file_update: Данные для обновления
        session: Сессия БД

    Returns:
        Обновленные метаданные файла

    Raises:
        HTTPException: 404 если файл не найден
    """
    import uuid as uuid_module

    try:
        file_uuid_obj = uuid_module.UUID(str(file_uuid))
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный UUID")

    db_file = await update_file(session, file_uuid_obj, file_update)
    if not db_file:
        raise HTTPException(status_code=404, detail="Файл не найден")

    return FileRead.model_validate(db_file)


@file_storage_router.delete("/{file_uuid}", status_code=204)
async def delete_file(
    file_uuid,
    session: AsyncSession = Depends(get_async_session),
    storage_service: FileStorageService = Depends(get_file_storage_service),
) -> None:
    """Удаляет файл (мягкое удаление - устанавливает is_active=False).

    Файл удаляется с диска, запись в БД остается с is_active=False.

    Args:
        file_uuid: UUID файла
        session: Сессия БД
        storage_service: Сервис файлового хранилища

    Raises:
        HTTPException: 404 если файл не найден
    """
    import uuid as uuid_module

    try:
        file_uuid_obj = uuid_module.UUID(str(file_uuid))
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный UUID")

    # Проверяем существование файла в БД
    db_file = await get_file_by_uuid(session, file_uuid_obj)
    if not db_file or not db_file.is_active:
        raise HTTPException(status_code=404, detail="Файл не найден")

    # Удаляем файл с диска
    deleted = storage_service.delete_file(file_uuid_obj)
    if not deleted:
        logger.warning(f"Файл не найден на диске при удалении: UUID {file_uuid}")

    # Мягко удаляем запись в БД
    soft_deleted = await soft_delete_file(session, file_uuid_obj)
    if not soft_deleted:
        raise HTTPException(status_code=404, detail="Файл не найден в базе данных")

    logger.info(f"Файл мягко удален: {file_uuid} (is_active=False)")
    return None
