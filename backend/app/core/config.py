from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 저장소 루트의 .env 하나를 docker compose, 백엔드, 프론트엔드가 함께 쓴다.
ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_ENV, extra="ignore")

    data_go_kr_service_key: str = ""
    kakao_rest_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "claude-haiku-5-5"

    database_url: str = "postgresql+asyncpg://roundy:roundy@localhost:5432/roundy"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = ""
    jwt_expire_minutes: int = 60

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
