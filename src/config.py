from pathlib import Path
from typing import Literal

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.logger import logger


class Settings(BaseSettings):
    """Настройки приложения."""
    
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    PROJECT_NAME: str
    APP_VERSION: str = "0.1"

    # Настройки PostgreSQL
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    # Настройки пула подключений к БД
    DB_POOL_SIZE: int = 10  # Количество постоянных соединений в пуле
    DB_MAX_OVERFLOW: int = 20  # Дополнительные соединения сверх pool_size
    DB_POOL_TIMEOUT: float = 30.0  # Таймаут ожидания соединения (секунды)
    DB_POOL_RECYCLE: int = 3600  # Время жизни соединения (секунды)
    DB_POOL_PRE_PING: bool = True  # Проверка соединения перед использованием
    
    # Настройки логирования
    LOG_LEVEL: str = "INFO"  # Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Настройки файлового хранилища
    FILES_STORAGE_PATH: Path = Path("./storage/files")  # Путь к корневой папке хранилища

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        """Вычисляемый URI для подключения к базе данных."""
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )


def init_settings(env_file_name: str = ".env") -> Settings:
    """
    Инициализирует настройки из файла окружения.
    
    Args:
        env_file_name: Имя файла с переменными окружения
        
    Returns:
        Settings: Объект с настройками приложения
    """
    from src.logger import set_log_level
    
    _ROOT_DIRECTORY: Path = Path(__file__).resolve().parent.parent
    env_file_abs_path = Path.joinpath(_ROOT_DIRECTORY, env_file_name)

    if not Path.exists(env_file_abs_path):
        logger.critical(f"Отсутствует файл: {env_file_abs_path}")
        exit(-1)
    
    settings_obj = Settings(_env_file=env_file_abs_path)
    # Применяем уровень логирования из настроек
    set_log_level(settings_obj.LOG_LEVEL)
    
    return settings_obj


settings = init_settings()  # type: ignore
