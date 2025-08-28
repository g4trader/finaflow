from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:  # pragma: no cover - fallback for pydantic v1
    try:
        from pydantic import BaseSettings  # type: ignore
    except Exception as e:  # pragma: no cover - pydantic v2 without settings
        raise ImportError(
            "Install pydantic-settings for pydantic v2 support"
        ) from e

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

    class Config:
        env_file = ".env"
