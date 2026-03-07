from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class BaseInfraSettings(BaseSettings):
    """
    Base configuration for all LicensePanel infrastructure components.
    Centralizes shared environment variables to ensure consistency.
    """
    
    MAINTENANCE_MODE: bool = False
    DEBUG: bool = True

    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_SSL: bool = False
    DB_SSL_CA: Optional[str] = None
    DB_AUTH_TOKEN: Optional[str] = None

    CSRF_SECRET: str
    MASTER_ENCRYPTION_KEY: str
    INFRA_ADMIN_KEY: str
    INFRA_CORE_KEY: str
    HF_ACCESS_TOKEN: Optional[str] = None

    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    DISCORD_WEBHOOK_URL: Optional[str] = None

    MQTT_BROKER: Optional[str] = None
    MQTT_PORT: int = 1883
    MQTT_USER: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None

    REDIS_URL: str = "redis://localhost:6379"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )
