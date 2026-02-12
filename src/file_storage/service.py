"""Сервис для работы с локальным файловым хранилищем.

Файлы хранятся в структуре:
{storage_root}/{prefix1}/{prefix2}/{uuid}
где prefix1 - первые 2 символа UUID (без дефисов)
      prefix2 - следующие 2 символа UUID (без дефисов)
"""

import uuid
from pathlib import Path
from typing import Optional

from src.config import settings
from src.logger import logger


class FileStorageService:
    """Сервис для сохранения и управления файлами на локальном диске."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        """Инициализация сервиса.

        Args:
            storage_path: Путь к корневой папке хранилища. Если не указан,
                         берется из настроек FILES_STORAGE_PATH.
        """
        self.storage_root = storage_path or settings.FILES_STORAGE_PATH
        self.storage_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"Инициализировано файловое хранилище: {self.storage_root}")

    def _get_prefix_parts(self, file_uuid: uuid.UUID) -> tuple[str, str]:
        """Получить две части префикса из UUID.

        Args:
            file_uuid: UUID файла

        Returns:
            Кортеж (prefix1, prefix2), где:
            - prefix1 - первые 2 символа UUID (без дефисов)
            - prefix2 - следующие 2 символа UUID (без дефисов)
        """
        uuid_str = str(file_uuid).replace("-", "")
        prefix1 = uuid_str[:2]
        prefix2 = uuid_str[2:4]
        return prefix1, prefix2

    def _get_file_path(self, file_uuid: uuid.UUID) -> Path:
        """Получить полный путь к файлу (без создания папок).

        Args:
            file_uuid: UUID файла

        Returns:
            Полный путь к файлу (имя файла = строковое представление UUID)
        """
        prefix1, prefix2 = self._get_prefix_parts(file_uuid)
        return self.storage_root / prefix1 / prefix2 / str(file_uuid)

    def save_file(
        self,
        content: bytes,
        file_uuid: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Сохранить файл в хранилище.

        Файл сохраняется с именем, равным строковому представлению UUID.

        Args:
            content: Содержимое файла в байтах
            file_uuid: UUID файла. Если не указан, генерируется новый

        Returns:
            UUID сохраненного файла
        """
        if file_uuid is None:
            file_uuid = uuid.uuid4()

        file_path = self._get_file_path(file_uuid)

        # Создаем папки, если их нет
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Проверяем, не существует ли уже файл с таким UUID
        if file_path.exists():
            logger.warning(f"Файл с UUID {file_uuid} уже существует: {file_path}")
            return file_uuid

        # Сохраняем файл
        file_path.write_bytes(content)
        logger.info(f"Файл сохранен: {file_path} (UUID: {file_uuid})")

        return file_uuid

    def get_file_path(self, file_uuid: uuid.UUID) -> Path:
        """Получить путь к файлу.

        Args:
            file_uuid: UUID файла

        Returns:
            Путь к файлу

        Raises:
            FileNotFoundError: Если файл не найден
        """
        file_path = self._get_file_path(file_uuid)

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path} (UUID: {file_uuid})")
            raise FileNotFoundError(f"Файл с UUID {file_uuid} не найден")

        return file_path

    def get_file_content(self, file_uuid: uuid.UUID) -> bytes:
        """Получить содержимое файла.

        Args:
            file_uuid: UUID файла

        Returns:
            Содержимое файла в байтах

        Raises:
            FileNotFoundError: Если файл не найден
        """
        file_path = self.get_file_path(file_uuid)
        return file_path.read_bytes()

    def delete_file(self, file_uuid: uuid.UUID) -> bool:
        """Удалить файл из хранилища.

        Args:
            file_uuid: UUID файла

        Returns:
            True если файл удален, False если файл не найден
        """
        try:
            file_path = self.get_file_path(file_uuid)
            file_path.unlink()
            logger.info(f"Файл удален: {file_path} (UUID: {file_uuid})")

            # Попытка удалить пустые префикс-папки (снизу вверх)
            prefix1, prefix2 = self._get_prefix_parts(file_uuid)
            prefix2_dir = self.storage_root / prefix1 / prefix2
            prefix1_dir = self.storage_root / prefix1

            try:
                prefix2_dir.rmdir()  # Удаляем только если папка пустая
                logger.debug(f"Удалена пустая папка: {prefix2_dir}")
            except OSError:
                pass  # Папка не пустая или не существует

            try:
                prefix1_dir.rmdir()  # Удаляем только если папка пустая
                logger.debug(f"Удалена пустая папка: {prefix1_dir}")
            except OSError:
                pass  # Папка не пустая или не существует

            return True
        except FileNotFoundError:
            logger.warning(f"Файл не найден при удалении: UUID {file_uuid}")
            return False

    def file_exists(self, file_uuid: uuid.UUID) -> bool:
        """Проверить существование файла.

        Args:
            file_uuid: UUID файла

        Returns:
            True если файл существует, иначе False
        """
        try:
            file_path = self._get_file_path(file_uuid)
            return file_path.exists()
        except Exception as e:
            logger.error(f"Ошибка при проверке существования файла: {e}")
            return False

    def list_files(self) -> list[dict]:
        """Получить список всех файлов в хранилище.

        Returns:
            Список словарей с информацией о файлах: uuid, path, size, prefix1, prefix2
        """
        files = []
        for prefix1_dir in self.storage_root.iterdir():
            if prefix1_dir.is_dir() and len(prefix1_dir.name) == 2:
                for prefix2_dir in prefix1_dir.iterdir():
                    if prefix2_dir.is_dir() and len(prefix2_dir.name) == 2:
                        for file_path in prefix2_dir.iterdir():
                            if file_path.is_file():
                                files.append({
                                    "uuid": file_path.name,
                                    "path": str(file_path),
                                    "size": file_path.stat().st_size,
                                    "prefix1": prefix1_dir.name,
                                    "prefix2": prefix2_dir.name,
                                })
        return files


# Глобальный экземпляр сервиса (инициализируется при импорте)
_file_storage_service: Optional[FileStorageService] = None


def get_file_storage_service() -> FileStorageService:
    """Получить экземпляр сервиса файлового хранилища.

    Используется как dependency injection в FastAPI.

    Returns:
        Экземпляр FileStorageService
    """
    global _file_storage_service
    if _file_storage_service is None:
        _file_storage_service = FileStorageService()
    return _file_storage_service
