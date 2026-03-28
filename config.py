

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class BaseInfraSettings(BaseSettings):
    MAINTENANCE_MODE: bool = False
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///data/infra.db"
    DB_POOL_SIZE: int = 20
    DB_SSL: bool = False
    DB_SSL_CA: Optional[str] = None
    DB_AUTH_TOKEN: Optional[str] = None
    CSRF_SECRET: str = "default_csrf_secret_change_me"
    MASTER_ENCRYPTION_KEY: str = "default_master_encryption_key_32_chars"
    INFRA_ADMIN_KEY: str = "default_admin_key"
    INFRA_CORE_KEY: str = "default_core_key"
    HF_ACCESS_TOKEN: Optional[str] = None
    EXTERNAL_TOKEN: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    DISCORD_WEBHOOK_URL: Optional[str] = None
    MQTT_BROKER: Optional[str] = None
    MQTT_PORT: int = 1883
    MQTT_USER: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    REDIS_URL: str = "redis://127.0.0.1:6379"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

