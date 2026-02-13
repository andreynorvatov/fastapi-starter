# Docker конфигурация

Проект содержит конфигурационные файлы для запуска приложения в Docker:

## Файлы

- `Dockerfile.prod` - production образ с multi-stage сборкой, non-root пользователем, healthcheck
- `Dockerfile.dev` - development образ с поддержкой hot-reload
- `docker-compose.prod.yml` - production оркестрация (PostgreSQL + API)
- `docker-compose.dev.yml` - development оркестрация (PostgreSQL + API с live-reload)
- `.dockerignore` - исключает ненужные файлы из образа

## Требования

- Docker и Docker Compose установлены
- Файл `.env` присутствует в корне проекта с необходимыми переменными окружения

## Быстрый старт

### Development (с hot-reload)

```bash
docker-compose -f docker-compose.dev.yml up --build
```

Приложение будет доступно: http://localhost:8000
Health check: http://localhost:8000/system/health

### Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Приложение будет доступно: http://localhost:8000
Health check: http://localhost:8000/system/health

## Переменные окружения

Основные переменные (определяются в `.env`):

```env
# Postgres
POSTGRES_DB_ADMIN=local_db
POSTGRES_USER_ADMIN=admin
POSTGRES_PASSWORD_ADMIN=1234

# Приложение
ENVIRONMENT=development  # или production
LOG_LEVEL=INFO
PROJECT_NAME="FastAPI Starter"
APP_VERSION=0.3

# Подключение к БД (переопределяются в docker-compose)
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=local_db
POSTGRES_USER=fastapi_starter
POSTGRES_PASSWORD=1234
```

## Особенности

- **Production образ**: multi-stage сборка, non-root пользователь `appuser`, 2 workers, healthcheck
- **Development образ**: включает dev зависимости, 1 worker, hot-reload
- **Storage**: В production используется volume `storage_data` для сохранения файлов
- **Health check**: Эндпоинт `/system/health` проверяет доступность БД и приложения
- **Зависимости**: Управляются через `uv` (быстрый менеджер пакетов Python)

## Команды

### Пересборка production образа

```bash
docker-compose -f docker-compose.prod.yml build --no-cache api
```

### Просмотр логов

```bash
docker-compose -f docker-compose.prod.yml logs -f api
```

### Остановка

```bash
docker-compose -f docker-compose.prod.yml down
# Для удаления volumes (включая данные БД и файлы)
docker-compose -f docker-compose.prod.yml down -v
```

### Выполнение миграций

```bash
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head
```

## Примечания

- В development режиме код монтируется как volume, изменения применяются без перезагрузки контейнера (granian --reload)
- В production режиме код встроен в образ, для изменений требуется пересборка
- Для работы healthcheck убедитесь, что эндпоинт `/system/health` доступен
