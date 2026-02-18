"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ParcelData API configuration.

    All values can be overridden via environment variables.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_name: str = "ParcelData"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = (
        "postgresql+asyncpg://parceldata:parceldata@localhost:5432/parceldata"
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    api_key_header: str = "X-API-Key"
    auth_header: str = "Authorization"

    # Rate Limiting
    rate_limit_free_per_second: int = 1
    rate_limit_free_per_day: int = 100
    rate_limit_pro_per_second: int = 10
    rate_limit_pro_per_day: int = 10000
    rate_limit_business_per_second: int = 50
    rate_limit_business_per_day: int = 500000

    # External Services (placeholders)
    regrid_api_key: str = ""
    attom_api_key: str = ""


settings = Settings()
