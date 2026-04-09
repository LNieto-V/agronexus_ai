from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    BASE_DIR: str = str(Path(__file__).resolve().parents[2])
    GEMINI_API_KEY: str = ""
    GEMINI_API_KEYS: str = "" # Formato: "key1,key2,key3"
    SUPABASE_URL: str = "your_project_url"
    SUPABASE_KEY: str = "your_anon_key"
    SUPABASE_SERVICE_ROLE_KEY: str = "your_service_role_key"
    SUPABASE_JWT_SECRET: str = "your_jwt_secret"
    SUPABASE_JWK: str = "{}"
    
    # AgroNexus API config
    AGRONEXUS_URL: str = "http://localhost:8000"
    AGRONEXUS_WRITE_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
