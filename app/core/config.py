from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    BASE_DIR: str = str(Path(__file__).resolve().parents[2])
    GEMINI_API_KEY: str = ""
    SUPABASE_URL: str = "your_project_url"
    SUPABASE_KEY: str = "your_anon_key"
    SUPABASE_SERVICE_ROLE_KEY: str = "your_service_role_key"
    SUPABASE_JWT_SECRET: str = "your_jwt_secret"
    SUPABASE_JWK: str = "{}"

    class Config:
        env_file = ".env"

settings = Settings()
