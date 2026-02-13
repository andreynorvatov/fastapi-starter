# План решения проблемы перезаписи файлов в Minio

## Цель
Предотвратить перезапись файлов с одинаковыми именами в Minio бакете.

## Выбранный подход
**Генерация уникальных имен файлов** с сохранением оригинального имени в метаданных.

### Причины выбора:
- Простая и надежная реализация
- Гарантированная уникальность (UUID4)
- Сохранение информации об оригинальном имени файла
- Не требует настройки Minio server
- Обратная совместимость

## Архитектурные изменения

### 1. Модели данных (src/minio_service/schemas.py)

#### Изменения в `MinioObjectResponse`:
```python
class MinioObjectResponse(BaseModel):
    bucket_name: str
    object_name: str          # UUID имя файла в бакете
    original_filename: str | None  # Оригинальное имя пользователя
    size: int
    last_modified: datetime
    etag: str
    content_type: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
```

#### Новая схема для загрузки:
```python
class MinioUploadRequest(BaseModel):
    bucket_name: str
    file: UploadFile
    object_name: str | None = None  # Если None - генерировать UUID
    preserve_filename: bool = False  # Сохранять оригинальное имя в метаданных
```

### 2. Логика загрузки (src/minio_service/crud.py)

#### Алгоритм в `upload_file`:
```python
async def upload_file(
    self,
    bucket_name: str,
    object_name: str | None,  # Может быть None
    file_data: bytes,
    content_type: str | None = None,
    preserve_filename: bool = False,
) -> MinioObjectResponse:
    
    # 1. Определить итоговое имя объекта
    if object_name is None or object_name == "":
        # Генерируем UUID с расширением
        import uuid
        from pathlib import Path
        
        ext = Path(original_name).suffix if preserve_filename else ""
        object_name = f"{uuid.uuid4()}{ext}"
    else:
        # Если имя указано, проверяем конфликт
        # (опционально - можно добавить суффикс)
        pass
    
    # 2. Подготовить метаданные
    metadata = {}
    if preserve_filename and original_name:
        metadata["original_filename"] = original_name
    
    # 3. Загрузить файл с метаданными
    await self.client.upload_file(
        bucket_name=bucket_name,
        object_name=object_name,
        file_data=file_data,
        content_type=content_type,
        metadata=metadata,
    )
    
    # 4. Вернуть ответ с original_filename
    return MinioObjectResponse(
        bucket_name=bucket_name,
        object_name=object_name,
        original_filename=original_name if preserve_filename else None,
        ...
    )
```

### 3. API Endpoints (src/minio_service/routes.py)

#### Изменения в `/upload` endpoint:
```python
@router.post(
    "/upload",
    response_model=MinioObjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    service: Annotated[MinioService, Depends(get_minio_service)],
    bucket_name: str = Form(...),
    object_name: str | None = Form(None),  # Опционально
    preserve_filename: bool = Form(False),  # Сохранять оригинальное имя
    file: UploadFile = File(...),
) -> MinioObjectResponse:
    """Upload file to Minio.
    
    Если object_name не указан, генерируется UUID.
    Если preserve_filename=True, оригинальное имя сохраняется в метаданных.
    """
    file_data = await file.read()
    original_filename = file.filename
    
    return await service.upload_file(
        bucket_name=bucket_name,
        object_name=object_name,
        file_data=file_data,
        content_type=file.content_type,
        original_filename=original_filename,
        preserve_filename=preserve_filename,
    )
```

### 4. Клиент Minio (src/minio_service/client.py)

#### Добавить поддержку метаданных:
```python
def upload_file(
    self,
    bucket_name: str,
    object_name: str,
    file_data: bytes,
    content_type: str | None = None,
    metadata: dict[str, str] | None = None,
) -> None:
    """Upload file to Minio with optional metadata."""
    from io import BytesIO
    
    file_stream = BytesIO(file_data)
    file_length = len(file_data)
    
    self.client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=file_stream,
        length=file_length,
        content_type=content_type,
        metadata=metadata,
    )
```

### 5. Миграция базы данных (если есть таблица files)

Если в БД есть таблица `files` с полями:
- `filename` (имя файла в Minio)
- `original_filename` (добавить nullable поле)

```python
# migrations/versions/xxxx_add_original_filename.py
def upgrade():
    op.add_column('files', sa.Column('original_filename', sa.String(), nullable=True))
```

## Обратная совместимость

### Сохранение старого API:
- Параметр `object_name` остается обязательным? → **Нет, становится опциональным**
- Если клиент передает `object_name`, он будет использоваться (но возможны конфликты!)
- Рекомендуется всегда использовать `preserve_filename=True` и не передавать `object_name`

### Миграция существующих данных:
1. Добавить скрипт для извлечения оригинальных имен из метаданных
2. Обновить записи в БД (если хранятся метаданные)

## Тестирование

### Unit тесты:
1. Загрузка без `object_name` → генерируется UUID
2. Загрузка с `preserve_filename=True` → оригинальное имя в метаданных
3. Загрузка с одинаковыми `object_name` → перезапись (предупреждение в логах)
4. Проверка извлечения `original_filename` из ответа

### Интеграционные тесты:
1. Загрузить файл, получить ответ с `object_name` (UUID)
2. Загрузить второй файл с тем же оригинальным именем → разные UUID
3. Скачать файл и проверить метаданные

## Документация

### Обновить README.md:
- Добавить раздел "Загрузка файлов в Minio"
- Примеры использования:
  ```python
  # Автоматическая генерация UUID
  response = client.post("/minio/upload", ...)
  
  # Сохранение оригинального имени
  response = client.post("/minio/upload", 
      data={"bucket_name": "docs", "preserve_filename": "true"},
      files={"file": ("report.pdf", content)}
  )
  ```

### Обновить OpenAPI/Swagger:
- Добавить описания параметров
- Добавить примеры запросов/ответов

## План внедрения

1. **Фаза 1**: Реализовать генерацию UUID в `crud.upload_file`
2. **Фаза 2**: Добавить `original_filename` в схемы и ответы
3. **Фаза 3**: Обновить `routes.upload_file` для поддержки опционального `object_name`
4. **Фаза 4**: Добавить тесты
5. **Фаза 5**: Миграция (если нужно)
6. **Фаза 6**: Обновить документацию
7. **Фаза 7**: Протестировать в dev-окружении

## Риски и mitigation

| Риск | Mitigation |
|------|------------|
| Существующие клиенты сломаются | Обеспечить обратную совместимость: если `object_name` передан, использовать его |
| Утеря связи файл-оригинальное имя | Всегда сохранять `original_filename` в метаданных |
| Большое количество UUID файлов в бакете | Использовать префиксы/папки для группировки (например, `uploads/YYYY/MM/DD/uuid`) |

## Альтернативные варианты (на будущее)

1. **Версионирование Minio**: включить bucket versioning для хранения всех версий
2. **Структура папок**: `{user_id}/{date}/{original_name}` с проверкой конфликтов
3. **База данных**: хранить маппинг UUID → оригинальное имя в отдельной таблице

## Критерии успеха

- [ ] Файлы с одинаковыми оригинальными именами не перезаписываются
- [ ] В ответе API возвращается `original_filename` (если был передан)
- [ ] Обратная совместимость со старыми клиентами
- [ ] Все тесты проходят
- [ ] Документация обновлена
