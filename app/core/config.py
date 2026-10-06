from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # ==========================================================
    # DATABASE
    # ==========================================================
    DATABASE_URL: str = "sqlite:///docuextract.db"

    # ==========================================================
    # AI PROVIDERS
    # ==========================================================
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    VLM_PROVIDER: str = "groq"            # ✅ default groq
    VLM_MODEL: str = "qwen/qwen3.8-27b"

    # ==========================================================
    # STORAGE
    # ==========================================================
    STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE_MB: int = 10

    # ==========================================================
    # QUEUE
    # ==========================================================
    REDIS_URL: str = "redis://localhost:6379/0"

    # ==========================================================
    # APP
    # ==========================================================
    LOG_LEVEL: str = "INFO"
    CONFIDENCE_AUTO_APPROVE: float = 0.85
    CONFIDENCE_REVIEW_THRESHOLD: float = 0.60

    # ==========================================================
    # EMAIL (Gmail SMTP)
    # ✅ Ye naam .env me hone chahiye: SMTP_USER, SMTP_PASS
    # ==========================================================
    SMTP_USER: str = ""                   # e.g. docuextract.ai@gmail.com
    SMTP_PASS: str = ""                   # Gmail App Password (no spaces)

    # ==========================================================
    # GOOGLE OAUTH
    # ==========================================================
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ==========================================================
    # JWT SECURITY
    # ==========================================================
    JWT_SECRET: str = "docuextract-super-secret-jwt-key-2026-change-me"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==========================================================
    # FRONTEND
    # ==========================================================
    FRONTEND_URL: str = "http://127.0.0.1:8000"

    # ==========================================================
    # PYDANTIC CONFIG
    # - env_file: reads from .env automatically
    # - extra: ignore any extra env vars (no crash if .env has more)
    # - case_sensitive: False so SMTP_USER / smtp_user both work
    # ==========================================================
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()