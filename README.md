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

1. [x] fastapi
2. [x] granian
3. [x] granian-reload
4. [x] pytest
5. [x] conftest.py асинхронный клиент
6. [x] test health_check
7. [x] ruff
8. [x] mypy
9. [x] config
10. [x] .env_template
11. [x] logging в приложении
12. [ ] alembic
13. [ ] ORM
14. [ ] compose-example postgres
15. [ ] conftest.py с БД 
16. [ ] Фоновые асинхронные задачи
17. [ ] Мониторинг
18. [ ] Задать уровень логирования из конфига
19. [ ] logging в midleware
20. [ ] Таймзона
21. [ ] Системная server-side rendering страница
	1. [ ] Инфо о версии
	2. [ ] Наименование
	3. [ ] Схема БД
	4. [ ] .env переменные
22. 