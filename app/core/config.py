from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "File Analyzer Service"
    app_host: str
    app_port: int

    source_api_url: str
    source_api_candidate_id: str | None = None

    database_url: str
    async_database_url: str

    redis_url: str
    rabbitmq_url: str

    download_dir: str
    timezone: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
