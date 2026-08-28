import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables or .env file.
    Uses Pydantic BaseSettings for strong typing and validation.
    """
    PROJECT_NAME: str = "SkillSetu AI Competency Gap Learning Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = ""
    
    # MongoDB configuration
    MONGO_URI: str = "mongodb://localhost:27017/skillsetu_db"
    DATABASE_NAME: str = "skillsetu_db"
    
    # Security / Auth
    JWT_SECRET: str = "default_fallback_jwt_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # AI Service Key
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached instance of application settings.
    @lru_cache prevents re-reading environment variables on every request.
    """
    return Settings()
