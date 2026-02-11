"""Проверка наличия таблиц в тестовой схеме."""
import psycopg
from pydantic import PostgresDsn

dsn = PostgresDsn.build(
    scheme="postgresql",
    username="fastapi_starter_test",
    password="1234",
    host="localhost",
    port=5432,
    path="local_db",
)

with psycopg.connect(str(dsn), autocommit=True) as conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'fastapi_starter_test'
            """
        )
        tables = cur.fetchall()
        if tables:
            print("Таблицы в схеме fastapi_starter_test:")
            for t in tables:
                print(f"  - {t[0]}")
        else:
            print("Схема fastapi_starter_test пуста (таблиц нет)")
