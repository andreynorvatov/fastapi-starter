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

## Minio Storage Service

### Настройка

В файле `.env` добавьте переменные:

```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET=uploads
MINIO_REGION=us-east-1
```

### API Endpoints

Все эндпоинты доступны по префиксу `/minio`.

#### Управление бакетами

**Создать бакет**
```http
POST /minio/buckets
Content-Type: application/json

{
  "bucket_name": "my-bucket"
}
```

#### Загрузка файлов

**Загрузить файл (multipart/form-data)**
```http
POST /minio/upload
Content-Type: multipart/form-data

bucket_name: my-bucket
object_name: path/to/file.txt (опционально)
preserve_filename: true (опционально, по умолчанию false)
file: <binary data>
```

- `object_name` - опциональный путь к файлу в бакете. Если не указан, генерируется уникальное UUID имя.
- `preserve_filename` - если `true`, оригинальное имя файла сохраняется в метаданных и возвращается в ответе.
- При использовании `preserve_filename=true` расширение файла сохраняется в сгенерированном UUID имени.
- Файлы с одинаковыми оригинальными именами не перезаписываются, так как каждый получает уникальное имя.

**Получить URL для прямой загрузки (presigned PUT URL)**
```http
GET /minio/presigned/upload/{bucket_name}/{object_name}?expires=3600
```

#### Скачивание файлов

**Скачать файл**
```http
GET /minio/download/{bucket_name}/{object_name}
```

**Получить URL для скачивания (presigned GET URL)**
```http
GET /minio/presigned/download/{bucket_name}/{object_name}?expires=3600
```

#### Управление объектами

**Получить метаданные объекта**
```http
GET /minio/objects/{bucket_name}/{object_name}
```

**Удалить файл**
```http
DELETE /minio/delete
Content-Type: application/json

{
  "bucket_name": "my-bucket",
  "object_name": "path/to/file.txt"
}
```

**Список объектов в бакете**
```http
GET /minio/objects/{bucket_name}?prefix=optional/prefix/
```

### Использование в коде

```python
from src.minio_service.service import MinioService, get_minio_service

# Получение сервиса через DI
minio_service: MinioService = get_minio_service()

# Загрузка файла с автоматической генерацией UUID
with open("report.pdf", "rb") as f:
    file_data = f.read()
    result = await minio_service.upload_file(
        bucket_name="my-bucket",
        file_data=file_data,
        content_type="application/pdf",
        original_filename="report.pdf",
        preserve_filename=True
    )
# result.object_name - уникальное UUID имя (например, "a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf")
# result.original_filename - "report.pdf"

# Загрузка файла с указанием object_name (не рекомендуется, возможна перезапись)
result = await minio_service.upload_file(
    bucket_name="my-bucket",
    object_name="uploads/file.txt",
    file_data=file_data,
    content_type="text/plain"
)

# Скачивание файла
data = await minio_service.download_file("my-bucket", result.object_name)

# Получение presigned URL для загрузки
upload_url = await minio_service.get_upload_url(
    bucket_name="my-bucket",
    object_name=result.object_name,
    expires=3600
)

# Получение presigned URL для скачивания
download_url = await minio_service.get_download_url(
    bucket_name="my-bucket",
    object_name=result.object_name,
    expires=3600
)

# Удаление файла
await minio_service.delete_file("my-bucket", result.object_name)

# Список файлов
result = await minio_service.list_objects("my-bucket", prefix="uploads/")
for obj in result.objects:
    print(f"{obj.object_name} (original: {obj.original_filename}) - {obj.size} bytes")
```

### Предотвращение перезаписи файлов

Чтобы избежать перезаписи файлов с одинаковыми именами:

1. **Используйте автоматическую генерацию UUID** (не передавайте `object_name`):
   ```python
   result = await minio_service.upload_file(
       bucket_name="my-bucket",
       file_data=file_data,
       preserve_filename=True,
       original_filename=original_name
   )
   ```

2. **Сохраняйте оригинальное имя в метаданных** (`preserve_filename=True`):
   - Оригинальное имя файла сохраняется в метаданных Minio
   - Возвращается в поле `original_filename` ответа
   - Позволяет отслеживать, какой файл был загружен

3. **Расширение файла сохраняется**:
   - Если `preserve_filename=True` и `original_filename="document.pdf"`,
     то сгенерированное имя будет `"a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf"`

### Примечания

- Сервис автоматически создает бакет при первой загрузке файла, если бакет не существует
- Presigned URL имеют ограниченное время жизни (по умолчанию 1 час)
- Поддерживаются только HTTP методы GET и PUT для presigned URL
- Если `object_name` указан явно, файл может быть перезаписан при повторной загрузке с тем же именем
- Для надежной защиты от перезаписи используйте автоматическую генерацию UUID (не указывайте `object_name`)

### Запуск Minio

Запустите Minio через Docker:

```bash
docker run -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

Или используйте docker-compose (если настроен в проекте).

### Примечания

- Сервис автоматически создает бакет при первой загрузке файла, если бакет не существует
- Presigned URL имеют ограниченное время жизни (по умолчанию 1 час)
- Поддерживаются только HTTP методы GET и PUT для presigned URL
