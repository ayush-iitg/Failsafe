"""
config.py — Application Configuration
======================================
Uses pydantic-settings to read environment variables from a .env file.

WHY THIS PATTERN?
  - Never hardcode secrets (DB passwords, JWT keys) in source code.
  - pydantic-settings validates types at startup — if DATABASE_URL is missing,
    the app crashes immediately with a clear error rather than failing silently later.
  - In interviews: "I used the 12-factor app principle — config from environment."

HOW IT WORKS:
  Settings() reads from environment variables OR a .env file (via env_file = ".env").
  We create a single `settings` instance and import it everywhere — singleton pattern.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    # Format: postgresql://user:password@host:port/dbname
    DATABASE_URL: str = "postgresql://failsafe_user:failsafe_pass@localhost:5432/failsafe_db"

    # ── JWT Authentication ────────────────────────────────────────────────────
    # SECRET_KEY: used to sign JWT tokens. In production, use a long random string.
    # Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "changeme-use-a-long-random-secret-in-production"
    ALGORITHM: str = "HS256"                # JWT signing algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours — typical for a workday session

    # ── ML Artifacts ──────────────────────────────────────────────────────────
    # Paths to saved model and preprocessor (relative to backend/)
    MODEL_PATH: str = "../ml/models/xgboost_model.pkl"
    PREPROCESSOR_PATH: str = "../ml/models/preprocessor.pkl"

    # ── App metadata ──────────────────────────────────────────────────────────
    APP_NAME: str = "FAILSAFE API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True  # Set to False in production

    class Config:
        env_file = ".env"          # Read from .env file if it exists
        env_file_encoding = "utf-8"
        case_sensitive = True      # DATABASE_URL ≠ database_url


@lru_cache()  # Cache the settings object — only read .env once
def get_settings() -> Settings:
    return Settings()


# Single shared instance — import this everywhere
settings = get_settings()
