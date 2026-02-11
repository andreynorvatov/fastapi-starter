from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings

# Создание асинхронного движка с настройками пула подключений
async_engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    pool_size=settings.DB_POOL_SIZE,  # Количество постоянных соединений в пуле
    max_overflow=settings.DB_MAX_OVERFLOW,  # Дополнительные соединения сверх pool_size
    pool_timeout=settings.DB_POOL_TIMEOUT,  # Таймаут ожидания соединения из пула (секунды)
    pool_recycle=settings.DB_POOL_RECYCLE,  # Время жизни соединения до пересоздания (секунды)
    pool_pre_ping=settings.DB_POOL_PRE_PING,  # Проверка соединения перед использованием
    echo=False,  # Логирование SQL-запросов (отключено)
)

# Фабрика асинхронных сессий
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Не делать объекты "просроченными" после коммита
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронный генератор для получения сессии БД.
    
    Используется как dependency injection в FastAPI.
    Сессия автоматически закрывается при выходе из async with.
    
    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy
        
    Example:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with async_session_factory() as session:
        yield session
