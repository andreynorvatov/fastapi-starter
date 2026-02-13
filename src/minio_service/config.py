"""Minio configuration."""

from typing import Optional
from pydantic import Field
from src.config import Settings, settings as global_settings


class MinioSettings:
    """Minio settings wrapper."""
    
    def __init__(self, settings: Optional[Settings] = None) -> None:
        """Initialize with application settings."""
        self._settings: Optional[Settings] = settings
        self._cached_config: Optional[dict] = None
    
    @property
    def settings(self) -> Settings:
        """Get settings instance, creating if needed."""
        if self._settings is None:
            self._settings = global_settings
        return self._settings
    
    @property
    def endpoint(self) -> str:
        return self.settings.MINIO_ENDPOINT
    
    @property
    def access_key(self) -> str:
        return self.settings.MINIO_ACCESS_KEY
    
    @property
    def secret_key(self) -> str:
        return self.settings.MINIO_SECRET_KEY
    
    @property
    def secure(self) -> bool:
        return self.settings.MINIO_SECURE
    
    @property
    def default_bucket(self) -> str:
        return self.settings.MINIO_BUCKET
    
    @property
    def region(self) -> str:
        return self.settings.MINIO_REGION
    
    @property
    def client_config(self) -> dict:
        """Return client configuration dictionary."""
        if self._cached_config is None:
            self._cached_config = {
                "endpoint": self.endpoint,
                "access_key": self.access_key,
                "secret_key": self.secret_key,
                "secure": self.secure,
                "region": self.region,
            }
        return self._cached_config


# Don't create global instance at module level to avoid early Settings initialization
# Create it lazily when needed
_minio_settings_instance: Optional[MinioSettings] = None


def get_minio_settings() -> MinioSettings:
    """Get or create MinioSettings instance."""
    global _minio_settings_instance
    if _minio_settings_instance is None:
        _minio_settings_instance = MinioSettings()
    return _minio_settings_instance


# For backward compatibility, but won't initialize at import time
minio_settings = None  # Will be initialized lazily via get_minio_settings()
