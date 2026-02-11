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
