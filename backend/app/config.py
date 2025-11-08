from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    PROJECT_ID: Optional[str] = None
    DATASET: Optional[str] = None
    
    # Configurações da API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # Configurações de Email (opcional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    BIGQUERY_DATASET: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_prefix="",
        case_sensitive=False,
    )
