from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    SUPABASE_URL: str = "your_project_url"
    SUPABASE_KEY: str = "your_anon_key"

    class Config:
        env_file = ".env"

settings = Settings()
