from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = Field(default="HotelManager Pro Codex")
    api_prefix: str = Field(default="/api/v1")
    database_url: str = Field(default="sqlite:///./storage/app.db")
    storage_dir: str = Field(default="storage")

    class Config:
        env_prefix = "HOTELMANAGER_"
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
