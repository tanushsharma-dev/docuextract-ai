from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/docuextract"
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = ""
    STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE_MB: int = 10
    LOG_LEVEL: str = "INFO"
    VLM_MODEL: str = "gpt-4o"
    CONFIDENCE_AUTO_APPROVE: float = 0.85
    CONFIDENCE_REVIEW_THRESHOLD: float = 0.60

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()