"""
Фабрика для генерации тестовых данных модели File.

Содержит методы для создания одиночных и множественных экземпляров
модели File с предустановленными пресетами.
"""

import uuid
from pathlib import Path
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from src.file_storage.models import File


class FileFactory:
    """
    Фабрика для создания тестовых данных модели File.
    """

    @staticmethod
    async def create(
        session: AsyncSession,
        original_filename: str,
        file_path: str,
        file_size: int,
        mime_type: str | None = None,
        extension: str | None = None,
        is_active: bool = True,
    ) -> File:
        """
        Создаёт один экземпляр File и сохраняет в БД.

        Args:
            session: Асинхронная сессия БД
            original_filename: Оригинальное имя файла
            file_path: Относительный путь к файлу
            file_size: Размер файла в байтах
            mime_type: MIME-тип
            extension: Расширение файла
            is_active: Флаг активности

        Returns:
            Созданный экземпляр File
        """
        file = File(
            id=uuid.uuid4(),
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            extension=extension,
            is_active=is_active,
        )
        session.add(file)
        await session.commit()
        await session.refresh(file)
        return file

    @staticmethod
    async def create_batch(
        session: AsyncSession,
        files_data: Sequence[dict],
    ) -> list[File]:
        """
        Создаёт несколько экземпляров File и сохраняет в БД.

        Args:
            session: Асинхронная сессия БД
            files_data: Список словарей с данными для создания File

        Returns:
            Список созданных экземпляров File
        """
        files = []
        for data in files_data:
            file = File(
                id=uuid.uuid4(),
                original_filename=data["original_filename"],
                file_path=data["file_path"],
                file_size=data["file_size"],
                mime_type=data.get("mime_type"),
                extension=data.get("extension"),
                is_active=data.get("is_active", True),
            )
            session.add(file)
            files.append(file)

        await session.commit()

        for file in files:
            await session.refresh(file)

        return files

    @staticmethod
    async def create_active_file(
        session: AsyncSession,
        original_filename: str = "active_file.txt",
        file_size: int = 1024,
        mime_type: str = "text/plain",
        extension: str = ".txt",
    ) -> File:
        """
        Создаёт активный файл (пресет active_file).

        Args:
            session: Асинхронная сессия БД
            original_filename: Имя файла
            file_size: Размер файла
            mime_type: MIME-тип
            extension: Расширение

        Returns:
            Созданный экземпляр File с is_active=True
        """
        file_uuid = uuid.uuid4()
        file_path = f"{str(file_uuid)[:2]}/{str(file_uuid)[2:4]}/{file_uuid}"

        return await FileFactory.create(
            session=session,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            extension=extension,
            is_active=True,
        )

    @staticmethod
    async def create_inactive_file(
        session: AsyncSession,
        original_filename: str = "inactive_file.txt",
        file_size: int = 512,
        mime_type: str = "text/plain",
        extension: str = ".txt",
    ) -> File:
        """
        Создаёт неактивный файл (пресет inactive_file).

        Args:
            session: Асинхронная сессия БД
            original_filename: Имя файла
            file_size: Размер файла
            mime_type: MIME-тип
            extension: Расширение

        Returns:
            Созданный экземпляр File с is_active=False
        """
        file_uuid = uuid.uuid4()
        file_path = f"{str(file_uuid)[:2]}/{str(file_uuid)[2:4]}/{file_uuid}"

        return await FileFactory.create(
            session=session,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            extension=extension,
            is_active=False,
        )

    @staticmethod
    def get_default_test_data() -> list[dict]:
        """
        Возвращает список тестовых данных по умолчанию.

        Returns:
            Список словарей с данными для создания File
        """
        return [
            {
                "original_filename": "test_file_1.txt",
                "file_path": "ab/cd/11111111-1111-1111-1111-111111111111",
                "file_size": 1024,
                "mime_type": "text/plain",
                "extension": ".txt",
                "is_active": True,
            },
            {
                "original_filename": "test_file_2.jpg",
                "file_path": "ef/gh/22222222-2222-2222-2222-222222222222",
                "file_size": 2048,
                "mime_type": "image/jpeg",
                "extension": ".jpg",
                "is_active": True,
            },
            {
                "original_filename": "inactive_file.pdf",
                "file_path": "ij/kl/33333333-3333-3333-3333-333333333333",
                "file_size": 512,
                "mime_type": "application/pdf",
                "extension": ".pdf",
                "is_active": False,
            },
        ]
