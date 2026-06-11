from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    backend_url: str = "http://localhost:8000"
    mqtt_broker: str = "mqtt://localhost:1883"
    model_cache: str = "/app/models"
    confidence_threshold: float = 75.0
    unknown_threshold: float = 70.0
    motion_sensitivity: float = 0.02
    frame_skip: int = 3

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
