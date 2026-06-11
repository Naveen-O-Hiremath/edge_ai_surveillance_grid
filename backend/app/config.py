from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Sentinel AI Surveillance Platform"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "dev-secret-change-in-production"
    database_url: str = "postgresql+asyncpg://sentinel:sentinel_secret@localhost:5432/sentinel_ai"
    redis_url: str = "redis://localhost:6379/0"
    mqtt_broker: str = "mqtt://localhost:1883"
    edge_ai_url: str = "http://localhost:8001"
    evidence_dir: str = "data/evidence"
    baseline_dir: str = "data/baselines"
    public_base_url: str = ""  # e.g. http://192.168.1.5:3000 for mobile camera demos
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    access_token_expire_minutes: int = 60 * 24

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
