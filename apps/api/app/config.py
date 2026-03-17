from pydantic import BaseModel
import os

class Settings(BaseModel):
    app_name: str = "SafeFlow API"
    env: str = os.getenv("SAFEFLOW_ENV", "dev")
    api_version: str = "v1"

    database_url: str = os.getenv(
        "SAFEFLOW_DB_URL",
        "postgresql+psycopg://safeflow:safeflow@localhost:5432/safeflow",
    )

def get_settings() -> Settings:
    return Settings()