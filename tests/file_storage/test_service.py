"""Тесты для FileStorageService."""

import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.file_storage.service import FileStorageService


@pytest.fixture
def temp_storage() -> TemporaryDirectory:
    """Временная директория для хранения файлов в тестах."""
    temp_dir = TemporaryDirectory()
    yield temp_dir
    temp_dir.cleanup()


@pytest.fixture
def storage_service(temp_storage: TemporaryDirectory) -> FileStorageService:
    """Экземпляр сервиса с временной директорией."""
    return FileStorageService(storage_path=Path(temp_storage.name))


def test_save_file_creates_uuid_and_file(storage_service: FileStorageService) -> None:
    """Тест сохранения файла с автоматической генерацией UUID."""
    content = b"Hello, World!"
    file_uuid = storage_service.save_file(content)

    assert isinstance(file_uuid, uuid.UUID)

    # Проверяем, что файл создан в правильной подпапке
    uuid_str = str(file_uuid).replace("-", "")
    prefix1 = uuid_str[:2]
    prefix2 = uuid_str[2:4]
    expected_path = storage_service.storage_root / prefix1 / prefix2 / str(file_uuid)
    assert expected_path.exists()
    assert expected_path.read_bytes() == content


def test_save_file_with_provided_uuid(
    storage_service: FileStorageService,
) -> None:
    """Тест сохранения файла с указанным UUID."""
    content = b"Specific UUID"
    specific_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    result_uuid = storage_service.save_file(content, file_uuid=specific_uuid)

    assert result_uuid == specific_uuid

    uuid_str = str(specific_uuid).replace("-", "")
    prefix1 = uuid_str[:2]
    prefix2 = uuid_str[2:4]
    expected_path = storage_service.storage_root / prefix1 / prefix2 / str(specific_uuid)
    assert expected_path.exists()
    assert expected_path.read_bytes() == content


def test_save_file_duplicate_uuid_returns_existing(
    storage_service: FileStorageService,
) -> None:
    """Тест поведения при попытке сохранить файл с существующим UUID."""
    content1 = b"First content"
    file_uuid = storage_service.save_file(content1)

    # Пытаемся сохранить с тем же UUID
    content2 = b"Second content"
    result_uuid = storage_service.save_file(content2, file_uuid=file_uuid)

    assert result_uuid == file_uuid

    # Файл должен остаться с первым содержимым
    uuid_str = str(file_uuid).replace("-", "")
    prefix1 = uuid_str[:2]
    prefix2 = uuid_str[2:4]
    file_path = storage_service.storage_root / prefix1 / prefix2 / str(file_uuid)
    assert file_path.read_bytes() == content1


def test_get_file_path(storage_service: FileStorageService) -> None:
    """Тест получения пути к файлу."""
    content = b"Get path test"
    file_uuid = storage_service.save_file(content)

    file_path = storage_service.get_file_path(file_uuid)
    assert file_path.exists()
    assert file_path.read_bytes() == content


def test_get_file_path_not_found(storage_service: FileStorageService) -> None:
    """Тест получения пути к несуществующему файлу."""
    non_existent_uuid = uuid.uuid4()

    with pytest.raises(FileNotFoundError):
        storage_service.get_file_path(non_existent_uuid)


def test_get_file_content(storage_service: FileStorageService) -> None:
    """Тест получения содержимого файла."""
    content = b"File content here"
    file_uuid = storage_service.save_file(content)

    retrieved_content = storage_service.get_file_content(file_uuid)
    assert retrieved_content == content


def test_delete_file(storage_service: FileStorageService) -> None:
    """Тест удаления файла."""
    content = b"To be deleted"
    file_uuid = storage_service.save_file(content)

    # Убедимся, что файл существует
    assert storage_service.file_exists(file_uuid)

    # Удаляем
    result = storage_service.delete_file(file_uuid)
    assert result is True
    assert not storage_service.file_exists(file_uuid)

    # Проверяем, что префикс-папки удалены (если были пустыми)
    uuid_str = str(file_uuid).replace("-", "")
    prefix1 = uuid_str[:2]
    prefix2 = uuid_str[2:4]
    prefix1_dir = storage_service.storage_root / prefix1
    prefix2_dir = prefix1_dir / prefix2

    # Поскольку это был единственный файл, обе папки должны быть удалены
    assert not prefix2_dir.exists(), f"Папка {prefix2_dir} должна быть удалена"
    assert not prefix1_dir.exists(), f"Папка {prefix1_dir} должна быть удалена"


def test_delete_file_not_found(storage_service: FileStorageService) -> None:
    """Тест удаления несуществующего файла."""
    non_existent_uuid = uuid.uuid4()
    result = storage_service.delete_file(non_existent_uuid)
    assert result is False


def test_file_exists(storage_service: FileStorageService) -> None:
    """Тест проверки существования файла."""
    content = b"Exists test"
    file_uuid = storage_service.save_file(content)

    assert storage_service.file_exists(file_uuid) is True

    storage_service.delete_file(file_uuid)
    assert storage_service.file_exists(file_uuid) is False


def test_list_files(storage_service: FileStorageService) -> None:
    """Тест получения списка всех файлов."""
    # Сохраняем несколько файлов
    uuid1 = storage_service.save_file(b"Content 1")
    uuid2 = storage_service.save_file(b"Content 2")
    uuid3 = storage_service.save_file(b"Content 3")

    files = storage_service.list_files()

    assert len(files) == 3
    uuids = [f["uuid"] for f in files]
    assert str(uuid1) in uuids
    assert str(uuid2) in uuids
    assert str(uuid3) in uuids

    for file_info in files:
        assert "path" in file_info
        assert "size" in file_info
        assert "prefix1" in file_info
        assert "prefix2" in file_info
        assert len(file_info["prefix1"]) == 2
        assert len(file_info["prefix2"]) == 2
        assert Path(file_info["path"]).exists()


def test_structure_creates_prefix_directories(
    storage_service: FileStorageService,
) -> None:
    """Тест, что файлы с разными префиксами создаются в разных папках."""
    # Создаем UUID, которые дают разные префиксы
    uuid1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
    uuid2 = uuid.UUID("22222222-2222-2222-2222-222222222222")

    storage_service.save_file(b"Content 1", file_uuid=uuid1)
    storage_service.save_file(b"Content 2", file_uuid=uuid2)

    uuid1_str = str(uuid1).replace("-", "")
    uuid2_str = str(uuid2).replace("-", "")
    prefix1_1 = uuid1_str[:2]
    prefix1_2 = uuid1_str[2:4]
    prefix2_1 = uuid2_str[:2]
    prefix2_2 = uuid2_str[2:4]

    # Проверяем, что префиксы первого уровня разные
    assert prefix1_1 != prefix2_1
    assert (storage_service.storage_root / prefix1_1).exists()
    assert (storage_service.storage_root / prefix2_1).exists()

    # Проверяем, что создались вторые уровни
    assert (storage_service.storage_root / prefix1_1 / prefix1_2).exists()
    assert (storage_service.storage_root / prefix2_1 / prefix2_2).exists()
