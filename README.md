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
```

```shell
sh run_tests.sh
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

### Ссылки
https://github.com/emmett-framework/granian

## Backend

1. Starter
	1. [x] fastapi
	2. [x] granian
	3. [x] granian-reload
	4. [x] pytest
	5. [x] conftest.py асинхронный клиент
	6. [x] test health_check
	7. [x] ruff
	8. [x] mypy
	9. [ ] alembic
	10. [ ] ORM
	11. [ ] conftest.py с БД
	12. [ ] logging
	13. [ ] Фоновые асинхронные задачи
	14. [ ] Мониторинг
2. 