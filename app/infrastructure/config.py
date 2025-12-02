from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Visibility Platform"
    DATABASE_URL: str = "sqlite+aiosqlite:///./ai_visibility.db"

    # LLM Configuration (Mock by default)
    LLM_PROVIDER: str = "mock"  # options: mock, openai, gemini, anthropic, auto
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Security
    # Default key for dev only. In production, set this env var!
    ENCRYPTION_KEY: str = "hXuDf7um-27AICHTn63NbZg1Xlx-XgPnSEtq768l05g="

    # Rate Limiting
    MAX_CONCURRENT_REQUESTS: int = 5
    REQUEST_TIMEOUT_SECONDS: int = 30
    RATE_LIMIT_DELAY_SECONDS: float = (
        0.1  # Delay between requests to respect rate limits
    )

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
