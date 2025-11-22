import asyncio
import sys
from typing import AsyncGenerator, Optional, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from src.logger import logger
from src.config import settings

class DatabaseManager:

    def __init__(
            self,
            sqlalchemy_database_uri: str,
            *,
            echo: bool = False,
            pool_size: int = 5,
            max_overflow: int = 10,
            pool_timeout: int = 30,
            pool_recycle: int = 3600,
            pool_pre_ping: bool = True
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

        # Настройка event loop для Windows
        self._setup_event_loop()

    def _setup_event_loop(self) -> None:
        """Настройка event loop"""
        if sys.platform == "win32":
            try:
                if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                    if isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
                        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            except Exception as e:
                logger.warning(f"Предупреждение о настройке цикла событий: {e}")

    async def connect(self) -> None:
        """Установить подключение к базе данных"""
        try:
            if self._engine:
                logger.warning("Соединение с базой данных уже установлено")
                return

            # Создаем engine с оптимизированными настройками
            self._engine = create_async_engine(
                self.sqlalchemy_database_uri,
                # Включение логгирования SQL-запросов (полезно для отладки, но снижает производительность)
                echo=self._echo,
                # Размер постоянного пула подключений - количество соединений, которые постоянно поддерживаются открытыми
                pool_size=self._pool_size,
                # Максимальное количество дополнительных подключений сверх pool_size, которые могут быть созданы при нагрузке
                max_overflow=self._max_overflow,
                # Таймаут в секундах для получения подключения из пула перед возникновением ошибки
                pool_timeout=self._pool_timeout,
                # Время в секундах, после которого подключение пересоздается (предотвращает использование устаревших соединений)
                pool_recycle=self._pool_recycle,
                # Включение проверки жизнеспособности подключения перед использованием (устраняет "поломанные" соединения)
                pool_pre_ping=self._pool_pre_ping,
                # Класс пула подключений - AsyncAdaptedQueuePool адаптирует стандартный QueuePool для асинхронной работы
                poolclass=AsyncAdaptedQueuePool,
                # Использование будущего API SQLAlchemy 2.0 (рекомендуется для новых проектов)
                future=True,

                connect_args={
                    # Таймаут в секундах для установки подключения к базе данных
                    "command_timeout": 60,
                    "server_settings": {
                        # Отключение JIT-компилятора (может улучшить производительность для коротких запросов)
                        "jit": "off",
                        # Имя приложения, которое будет отображаться в pg_stat_activity
                        "application_name": settings.PROJECT_NAME
                    }
                } if "asyncpg" in self.sqlalchemy_database_uri else {} # Применяем настройки только для asyncpg
            )

            self._session_factory = async_sessionmaker(
                # Движок базы данных, с которым будет ассоциирована сессия
                self._engine,
                # Класс сессии, который будет создаваться фабрикой
                # AsyncSession - асинхронная версия Session из SQLAlchemy
                class_=AsyncSession,
                # Отключает автоматическое истечение срока действия объектов после коммита
                # False - объекты остаются привязанными к сессии и доступны для использования после коммита
                # True - объекты становятся "деттаченными" после коммита и требуют перезагрузки
                expire_on_commit=False,
                # Автоматически отправляет pending изменения в базу данных перед выполнением запросов
                # True - обеспечивает консистентность данных, но добавляет дополнительный FLUSH
                # Особенно полезно при сложных операциях с несколькими зависимыми объектами
                autoflush=True,
                # Отключает автоматический коммит для каждой операции
                # False - требует явного вызова commit() для сохранения изменений
                # Позволяет использовать транзакции и откатывать изменения при ошибках
                autocommit=False,
            )

            # Проверка подключения
            result = await self._test_connection()

            logger.info(f"Соединение с базой данных успешно установлено {result}")

        except SQLAlchemyError as e:
            logger.error(f"Не удалось подключиться к базе данных: {e}")
            await self._safe_dispose()
            raise ConnectionError(f"Не удалось подключиться к базе данных: {e}") from e
        except Exception as e:
            logger.error(f"Неожиданная ошибка при подключении к базе данных: {e}")
            await self._safe_dispose()
            raise

    async def _test_connection(self) -> None:
        """Проверка подключения к БД"""
        async with self._engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            data = result.scalar()
            logger.warning(f"Data: {data}")
            if data != 1:
                raise ConnectionError("Тестовый запрос 'SELECT 1' к базе данных не выполнен")

    async def _safe_dispose(self) -> None:
        """Безопасное освобождение ресурсов при ошибках"""
        if self._engine:
            try:
                await self._engine.dispose()
            except Exception as e:
                logger.warning(f"Ошибка при освобождении ресурсов подключения к БД: {e}")
            finally:
                self._engine = None
                self._session_factory = None

    async def disconnect(self) -> None:
        """Закрыть подключение к базе данных с обработкой ошибок"""
        await self._safe_dispose()
        logger.info("Соединение с базой данных успешно закрыто")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получить асинхронную сессию с улучшенной обработкой ошибок"""
        if not self._session_factory:
            raise RuntimeError("База данных не подключена. Сначала вызовите connect().")

        session: AsyncSession = self._session_factory()
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка сеанса базы данных: {e}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Неожиданная ошибка в сеансе базы данных: {e}")
            raise
        finally:
            await session.close()

    @property
    async def engine_stats(self) -> dict:
        """
        Получить статистику пула соединений асинхронно

        Returns:
            dict: Статистика пула соединений с ключами:
                - checkedout: количество используемых соединений
                - checkedin: количество свободных соединений в пуле
                - size: текущий размер пула
                - overflow: количество соединений сверх лимита
                - connections: общее количество активных соединений

        Raises:
            RuntimeError: Если подключение к базе данных не установлено

        Example:
            stats = await db_manager.get_engine_stats()
            print(f"Active connections: {stats['connections']}")
        """
        if not self._engine:
            return {}

        # Конфигурация пула
        pool_config = {
            "pool_size": getattr(self, '_pool_size', 'unknown'),
            "max_overflow": getattr(self, '_max_overflow', 'unknown'),
            "pool_timeout": getattr(self, '_pool_timeout', 'unknown'),
            "pool_recycle": getattr(self, '_pool_recycle', 'unknown'),
            "pool_pre_ping": getattr(self, '_pool_pre_ping', 'unknown'),
            "isolation_level": getattr(self, '_isolation_level', 'unknown'),
            "engine_echo": getattr(self, '_echo', False)
        }

        try:
            pool = self._engine.pool
            return {
                # Текущее состояние
                "checkedout": pool.checkedout(),
                "checkedin": pool.checkedin(),
                "size": pool.size(),
                "overflow": pool.overflow(),
                "connections": pool.checkedin() + pool.checkedout(),

                # Конфигурация пула
                "pool_config": pool_config
            }
        except Exception as e:
            logger.warning(f"Не удалось получить статистику пула соединений: {e}")
            return {}
    # ------------------

    # TODO move in repository
    async def execute_raw(self, query: str, **params) -> Any:
        """Выполнить raw SQL запрос (для миграций и т.д.)"""
        if not self._engine:
            raise RuntimeError("Database not connected")

        async with self._engine.connect() as conn:
            # Используем text() для SQL
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
    def create_production(database_uri: str) -> DatabaseManager:
        """Создать менеджер для production"""
        return DatabaseManager(
            database_uri,
            echo=False,
            pool_size=1,
            max_overflow=5,
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
