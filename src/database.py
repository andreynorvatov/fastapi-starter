import asyncio
import sys
import logging
from typing import AsyncGenerator, Optional, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from src.logger import logger
from src.config import settings

class DatabaseManager:
    """Исправленный и оптимизированный менеджер подключения к базе данных"""

    def __init__(
            self,
            sqlalchemy_database_uri: str,
            *,
            echo: bool = False,
            pool_size: int = 5,
            max_overflow: int = 10,
            pool_timeout: int = 30,
            pool_recycle: int = 3600,
            pool_pre_ping: bool = True,
            isolation_level: str = "REPEATABLE READ"
    ):
        self.sqlalchemy_database_uri = sqlalchemy_database_uri
        self._engine: Optional[Any] = None
        self._session_factory: Optional[async_sessionmaker] = None

        # Конфигурация пула соединений
        self._echo = echo
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._pool_timeout = pool_timeout
        self._pool_recycle = pool_recycle
        self._pool_pre_ping = pool_pre_ping
        self._isolation_level = isolation_level

        # Настройка event loop для Windows
        self._setup_event_loop()

    def _setup_event_loop(self) -> None:
        """Настройка event loop для разных платформ"""
        if sys.platform == "win32":
            try:
                if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                    if isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
                        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            except Exception as e:
                logger.warning(f"Event loop setup warning: {e}")

    async def connect(self) -> None:
        """Установить подключение к базе данных с исправленным тестированием"""
        try:
            if self._engine:
                logger.warning("Database connection already established")
                return

            # Создаем engine с оптимизированными настройками
            self._engine = create_async_engine(
                self.sqlalchemy_database_uri,
                echo=self._echo,
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                pool_timeout=self._pool_timeout,
                pool_recycle=self._pool_recycle,
                pool_pre_ping=self._pool_pre_ping,
                # Используем более эффективный пул
                poolclass=AsyncAdaptedQueuePool,
                # Оптимизации для больших приложений
                future=True,

                connect_args={
                    "command_timeout": 60,
                    "server_settings": {
                        "jit": "off",
                        "application_name": settings.PROJECT_NAME
                    }
                } if "asyncpg" in self.sqlalchemy_database_uri else {}
            )

            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )

            # Проверка подключения
            result = await self._test_connection()

            logger.info(f"Database connection established successfully {result}")

        except SQLAlchemyError as e:
            logger.error(f"Database connection failed: {e}")
            await self._safe_dispose()
            raise ConnectionError(f"Failed to connect to database: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during database connection: {e}")
            await self._safe_dispose()
            raise

    async def _test_connection(self) -> None:
        """Правильное тестирование подключения к БД"""
        async with self._engine.connect() as conn:
            # Используем text() для SQL выражений
            result = await conn.execute(text("SELECT 1"))
            data = result.scalar()
            logger.warning(f"Data: {data}")
            if data != 1:
                raise ConnectionError("Database test query failed")

    async def _safe_dispose(self) -> None:
        """Безопасное освобождение ресурсов при ошибках"""
        if self._engine:
            try:
                await self._engine.dispose()
            except Exception as e:
                logger.warning(f"Error during engine dispose: {e}")
            finally:
                self._engine = None
                self._session_factory = None

    async def disconnect(self) -> None:
        """Закрыть подключение к базе данных с обработкой ошибок"""
        await self._safe_dispose()
        logger.info("Database connection closed successfully")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получить асинхронную сессию с улучшенной обработкой ошибок"""
        if not self._session_factory:
            raise RuntimeError("Database not connected. Call connect() first.")

        session: AsyncSession = self._session_factory()
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected error in database session: {e}")
            raise
        finally:
            await session.close()

    async def health_check(self) -> bool:
        """Проверить здоровье подключения к БД"""
        if not self._engine:
            return False

        try:
            async with self._engine.connect() as conn:
                # ИСПРАВЛЕННО: Используем text() для SQL
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        """Проверить, установлено ли подключение"""
        return self._engine is not None and not self._engine.closed

    @property
    def engine_stats(self) -> dict:
        """Получить статистику пула соединений"""
        if not self._engine:
            return {}

        try:
            pool = self._engine.pool
            return {
                "checkedout": pool.checkedout(),
                "checkedin": pool.checkedin(),
                "size": pool.size(),
                "overflow": pool.overflow(),
                "connections": pool.checkedin() + pool.checkedout()
            }
        except Exception as e:
            logger.warning(f"Could not get engine stats: {e}")
            return {}

    async def execute_raw(self, query: str, **params) -> Any:
        """Выполнить raw SQL запрос (для миграций и т.д.)"""
        if not self._engine:
            raise RuntimeError("Database not connected")

        async with self._engine.connect() as conn:
            # ИСПРАВЛЕННО: Используем text() для SQL
            result = await conn.execute(text(query), params)
            await conn.commit()
            return result

    async def fetch_one(self, query: str, **params) -> Optional[Any]:
        """Выполнить запрос и вернуть одну запись"""
        if not self._engine:
            raise RuntimeError("Database not connected")

        async with self._engine.connect() as conn:
            result = await conn.execute(text(query), params)
            return result.first()

    async def fetch_all(self, query: str, **params) -> list:
        """Выполнить запрос и вернуть все записи"""
        if not self._engine:
            raise RuntimeError("Database not connected")

        async with self._engine.connect() as conn:
            result = await conn.execute(text(query), params)
            return result.fetchall()

    def create_session(self) -> AsyncSession:
        """Создать сессию вручную (для транзакций)"""
        if not self._session_factory:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._session_factory()

    async def transactional(self, **kwargs) -> AsyncSession:
        """Создать сессию с настройками транзакции"""
        if not self._session_factory:
            raise RuntimeError("Database not connected. Call connect() first.")

        session = self._session_factory(**kwargs)
        return session


# Упрощенная фабрика для быстрого использования
class DatabaseManagerFactory:
    """Фабрика для создания менеджеров БД"""

    @staticmethod
    def create(
            database_uri: str,
            *,
            echo: bool = False,
            pool_size: int = 5,
            max_overflow: int = 10,
            **kwargs
    ) -> DatabaseManager:
        """Создать менеджер с указанными настройками"""
        return DatabaseManager(
            database_uri,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            **kwargs
        )

    @staticmethod
    def create_production(database_uri: str) -> DatabaseManager:
        """Создать менеджер для production"""
        return DatabaseManager(
            database_uri,
            echo=False,
            pool_size=20,
            max_overflow=30,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True
        )

    @staticmethod
    def create_development(database_uri: str) -> DatabaseManager:
        """Создать менеджер для development"""
        return DatabaseManager(
            database_uri,
            echo=True,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )

db_connection_pool = DatabaseManagerFactory.create_production(str(settings.SQLALCHEMY_DATABASE_URI))
