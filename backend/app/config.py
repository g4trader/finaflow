try:
    from pydantic_settings import BaseSettings
except ImportError:  # pragma: no cover - fallback for pydantic v1
    from pydantic import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
