from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/alana"
    
    @property
    def db_url(self) -> str:
        """Return database URL with correct driver."""
        url = self.database_url
        # Railway uses postgres:// but SQLAlchemy needs postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    # App
    app_name: str = "Alana"
    debug: bool = False

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
