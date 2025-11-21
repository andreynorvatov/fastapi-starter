import asyncio
import sys

from src.config import settings
from src.logger import logger


class DatabaseManager:
    """Менеджер подключения к базе данных"""

    def __init__(self, sqlalchemy_database_uri: str):
        self.sqlalchemy_database_uri = sqlalchemy_database_uri

        self.engine = None
        self.session_factory = None

        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def connect(self):
        """Установить подключение к базе данных"""
        try:
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

            self.engine = create_async_engine(
                self.sqlalchemy_database_uri,
                echo=False,
                pool_size=4,
                max_overflow=1,
                pool_pre_ping=True
            )

            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )

            logger.info("Database connection established")

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    async def disconnect(self):
        """Закрыть подключение к базе данных"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

    async def get_session(self):
        """Получить асинхронную сессию"""
        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()


# Создаем глобальный экземпляр
db_connection_pool = DatabaseManager(str(settings.SQLALCHEMY_DATABASE_URI))
