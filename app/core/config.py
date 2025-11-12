from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = Field(default="development")
    api_docs_url: str | None = "/docs"
    api_redoc_url: str | None = "/redoc"
    backend_cors_origins: List[AnyHttpUrl] | List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"]
    )
    secret_key: str = Field(default="change-me")
    access_token_expire_minutes: int = 60 * 24
    jwt_algorithm: str = "HS256"
    database_url: str = Field(default="sqlite+aiosqlite:///./travel_planner.db")

    llm_provider: str = Field(default="mock", description="mock|dashscope|openai")
    llm_model: str = Field(default="qwen-turbo")
    llm_endpoint: str | None = None
    llm_api_key: str | None = None

    speech_provider: str = Field(default="web", description="web|iflytek")
    iflytek_app_id: str | None = None
    iflytek_api_key: str | None = None
    iflytek_api_secret: str | None = None

    amap_api_key: str | None = None

    static_dir: Path = Field(default=Path("app/static"))
    template_dir: Path = Field(default=Path("app/templates"))
    static_version: str = Field(default="20250206")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def cors_allow_origins(self) -> list[str]:
        return [str(origin) for origin in self.backend_cors_origins]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
