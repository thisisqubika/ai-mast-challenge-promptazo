from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:8080"]
    drive_enabled: bool = False
    google_service_account_file: str = ""
    google_drive_folder_id: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    database_url: str = "sqlite:///./fanfest.db"
    media_storage_backend: str = "mock"  # "mock" | "local" | "drive" | "s3"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
