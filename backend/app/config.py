"""Application configuration from environment variables."""

from __future__ import annotations

import os


class Settings:
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Claude API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Rate limits
    MAX_EXTRACTIONS_PER_DAY: int = 50

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./careeros_backend.db")


settings = Settings()
