from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vakansiyalar REST API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://job_user:change_me@localhost:5432/job_portal"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("jwt_secret_key")
    @classmethod
    def secret_must_be_long(cls, value: str) -> str:
        if len(value.encode()) < 32:
            raise ValueError("JWT_SECRET_KEY kamida 32 bayt bo'lishi kerak")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

settings = Settings()
