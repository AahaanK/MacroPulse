from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for MacroPulse."""

    APP_NAME: str = "MacroPulse"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Environment and modes
    ENV: str = "development"
    FRED_API_KEY: str | None = None

    # Database: SQLite for zero-config local dev, PostgreSQL for production
    DATABASE_URL: str = "sqlite:///./macropulse.db"

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"

    # Ingestion settings
    HTTP_TIMEOUT_SECONDS: float = 20.0
    FRED_MAX_RETRIES: int = 4
    FRED_RATE_LIMIT_DELAY: float = 0.5  # Seconds between requests to be polite

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
