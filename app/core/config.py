from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./docuextract.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Gemini (FREE VLM)
    GEMINI_API_KEY: str = ""
    VLM_MODEL: str = "gemini-2.0-flash"

    # Optional - ab zaroori nahi
    OPENAI_API_KEY: str = ""

    STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE_MB: int = 10
    LOG_LEVEL: str = "INFO"
    CONFIDENCE_AUTO_APPROVE: float = 0.85
    CONFIDENCE_REVIEW_THRESHOLD: float = 0.60

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()