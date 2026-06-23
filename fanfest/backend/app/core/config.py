from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Comma-separated origins, e.g. "http://localhost:8080,http://localhost:3000"
    cors_origins: str = "http://localhost:8080"

    @property
    def cors_origins_list(self) -> list[str]:
        return [s.strip() for s in self.cors_origins.split(",") if s.strip()]
    drive_enabled: bool = False
    google_service_account_file: str = ""
    google_drive_folder_id: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    database_url: str = "sqlite:///./fanfest.db"
    media_storage_backend: str = "mock"  # "mock" | "local" | "drive" | "s3"
    # S3 backend (used when media_storage_backend == "s3")
    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    # Public base URL media is served from (CloudFront domain), e.g.
    # "https://d111111abcdef8.cloudfront.net". Used to build absolute media URLs.
    media_base_url: str = ""
    api_football_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
