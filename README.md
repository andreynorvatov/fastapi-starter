#it #python

## Проверка кода
### Ruff

Проверить линтером и показать результат (без исправления):
```shell
uv run ruff check .
```
Проверить линтером и ❗исправить❗ файлы:
```shell
uv run ruff check . --fix
```
Проверить форматирование кода и показать результат (без исправления):
```shell
uv run ruff format . --check
```
Проверить форматирование кода и ❗исправить❗ файлы:
```shell
uv run ruff format .
```
### MyPy
Проверить статическую типизацию (без исправления):
```
uv run mypy .
```

## Запуск тестов
```shell
uv run pytest
uv run pytest -v
uv run pytest -vv
```

```shell
sh run_tests.sh
```

## Сервис файлового хранилища

### Настройка

В файле `.env` добавьте переменную:

```env
FILES_STORAGE_PATH=./storage/files
```

По умолчанию файлы хранятся в папке `./storage/files` относительно корня проекта.

### Структура хранилища

Файлы хранятся в структуре:

```
{storage_root}/{prefix}/{uuid}
```

где:
- `storage_root` - корневая папка хранилища (из `FILES_STORAGE_PATH`)
- `prefix` - первые 2 символа UUID (без дефисов)
- `uuid` - строковое представление UUID файла

Пример:
```
storage/files/
├── 12/
│   └── 12345678-1234-5678-1234-567812345678
├── ab/
│   └── abc123def-456-789-012-3456789abcde
└── ff/
    └── ffffffff-ffff-ffff-ffff-ffffffffffff
```

### Использование

#### Инициализация сервиса

```python
from src.file_storage.service import FileStorageService, get_file_storage_service

# Создание экземпляра (обычно не требуется, используйте dependency injection)
storage = FileStorageService()

# Или получение глобального экземпляра через DI
storage = get_file_storage_service()
```

#### Сохранение файла

```python
import uuid

# Сохранить файл с автоматической генерацией UUID
content = b"Hello, World!"
file_uuid = storage.save_file(content)
# file_uuid - объект uuid.UUID

# Сохранить файл с указанным UUID
specific_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
file_uuid = storage.save_file(content, file_uuid=specific_uuid)
```

#### Получение файла

```python
# Получить путь к файлу
file_path = storage.get_file_path(file_uuid)

# Получить содержимое файла
content = storage.get_file_content(file_uuid)
```

#### Проверка существования

```python
if storage.file_exists(file_uuid):
    print("Файл существует")
```

#### Удаление файла

```python
success = storage.delete_file(file_uuid)
if success:
    print("Файл удален")
```

#### Список всех файлов

```python
files = storage.list_files()
for file_info in files:
    print(f"UUID: {file_info['uuid']}")
    print(f"Path: {file_info['path']}")
    print(f"Size: {file_info['size']} bytes")
    print(f"Prefix: {file_info['prefix']}")
```

### Использование в FastAPI

```python
from fastapi import APIRouter, Depends, UploadFile
from src.file_storage.service import get_file_storage_service, FileStorageService

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile,
    storage: FileStorageService = Depends(get_file_storage_service)
) -> dict:
    content = await file.read()
    file_uuid = storage.save_file(content)
    return {"uuid": str(file_uuid)}

@router.get("/download/{file_uuid}")
async def download_file(
    file_uuid: str,
    storage: FileStorageService = Depends(get_file_storage_service)
):
    import uuid
    uid = uuid.UUID(file_uuid)
    file_path = storage.get_file_path(uid)
    return FileResponse(file_path, filename=file_uuid)
```
##  ASGI-сервер granian

### Запуск приложения
```shell
granian --interface asgi --workers 1 --host 0.0.0.0 --port 8000 src.main:app
```
или
```shell
sh run_app.sh
```
## Миграции alembic
### Локальная работа с alembic (если репозиторий спулен с git, шаг можно пропустить)
<details>
<summary>При первом запуске, если файла alembic.ini ещё нет</summary>
запустить в терминале команду:

```bash
alembic init migrations
# или
alembic init -t async migrations
```
После этого будет создана папка с миграциями и конфигурационный файл для алембика.

В alembic.ini задать адрес базы данных, в которую бдует происходить накат миграций.
В папке с миграциями, файл env.py, изменения в блок:
`from myapp import mymodel`
</details>
  
  
### Создание миграции (делается при любых изменениях моделей):  
```bash  
alembic revision --autogenerate -m"db create"
```  
### Накатывание финальной миграции  
```bash  
alembic upgrade heads
```  
### Откат миграции на 1 ревизию  
```bash  
alembic downgrade -1
```
### Ссылки
https://github.com/emmett-framework/granian
