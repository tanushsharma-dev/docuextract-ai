from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///docuextract.db"

    # AI Providers
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    VLM_PROVIDER: str = "gemini"
    VLM_MODEL: str = "gemini-3.8-flash"

    # Storage
    STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE_MB: int = 10

    # Queue
    REDIS_URL: str = "redis://localhost:6379/0"

    # App
    LOG_LEVEL: str = "INFO"
    CONFIDENCE_AUTO_APPROVE: float = 0.85
    CONFIDENCE_REVIEW_THRESHOLD: float = 0.60

    class Config:
        env_file = ".env"


settings = Settings()