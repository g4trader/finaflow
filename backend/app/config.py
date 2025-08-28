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

    class Config:
        env_file = ".env"
