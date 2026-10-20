from functools import lru_cache
from typing import Literal
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

_DEV_SECRET = "dev-only-insecure-secret-do-not-use-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Aplicación
    app_name: str = "Dental Backend"
    app_version: str = "0.1.0"
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    timezone: str = "America/Lima"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool = True
    cors_origins: list[str] = []

    # Seguridad
    secret_key: SecretStr = SecretStr(_DEV_SECRET)
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 14

    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "dental"
    db_user: str = "dental_app"
    db_password: SecretStr = SecretStr("")
    db_pool_size: int = 10
    db_max_overflow: int = 10
    db_echo: bool = False

    # Redis / Celery
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: SecretStr = SecretStr("")
    celery_broker_db: int = 1
    celery_result_backend_enabled: bool = False
    celery_task_soft_time_limit: int = 60
    celery_task_time_limit: int = 90

    @field_validator("timezone")
    @classmethod
    def _valid_timezone(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Zona horaria desconocida: {v}") from exc
        return v

    @model_validator(mode="after")
    def _production_guards(self) -> "Settings":
        if self.environment == "production":
            secret = self.secret_key.get_secret_value()
            if secret == _DEV_SECRET or len(secret) < 32:
                raise ValueError("SECRET_KEY debe definirse con al menos 32 caracteres en producción")
            if not self.db_password.get_secret_value():
                raise ValueError("DB_PASSWORD es obligatorio en producción")
            if self.debug:
                raise ValueError("DEBUG debe estar desactivado en producción")
        return self

    @property
    def database_url(self) -> str:
        """URL SQLAlchemy (psycopg 3). URL.create escapa caracteres especiales."""
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value() or None,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        ).render_as_string(hide_password=False)

    def _redis_url(self, db: int) -> str:
        pwd = self.redis_password.get_secret_value()
        auth = f":{quote(pwd, safe='')}@" if pwd else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{db}"

    @property
    def redis_url(self) -> str:
        return self._redis_url(self.redis_db)

    @property
    def celery_broker_url(self) -> str:
        return self._redis_url(self.celery_broker_db)

    @property
    def celery_result_backend(self) -> str | None:
        return self.redis_url if self.celery_result_backend_enabled else None


@lru_cache
def get_settings() -> Settings:
    return Settings()
