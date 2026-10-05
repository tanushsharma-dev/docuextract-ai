from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///docuextract.db"

    # AI Providers
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    VLM_PROVIDER: str = "gemini"
    VLM_MODEL: str = "gemini-3.5-flash"

    # Storage
    STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE_MB: int = 10

    # Queue
    REDIS_URL: str = "redis://localhost:6379/0"

    # App
    LOG_LEVEL: str = "INFO"
    CONFIDENCE_AUTO_APPROVE: float = 0.85
    CONFIDENCE_REVIEW_THRESHOLD: float = 0.60

    # Email (Gmail SMTP)
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # JWT Security
    JWT_SECRET: str = "docuextract-super-secret-jwt-key-2026"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Frontend
    FRONTEND_URL: str = "http://127.0.0.1:8000"

    class Config:
        env_file = ".env"


settings = Settings()