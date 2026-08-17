from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        protected_namespaces=('settings_',),
    )

    app_env: str = 'development'
    database_url: str = 'postgresql+psycopg://tinycompany:tinycompany@localhost:5432/tinycompany'
    model_provider: str = 'fake'
    model_api_key: str | None = None


settings = Settings()
