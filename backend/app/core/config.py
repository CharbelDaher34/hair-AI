from pydantic_settings import BaseSettings
from typing import List, Union, Any, Optional
from pydantic import field_validator, Field, model_validator, PostgresDsn
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Debug mode
    DEBUG_MODE: bool = Field(True)

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    # Optional aliases / extras coming from .env
    POSTGRES_HOST: Optional[str] = None  # Some env files use POSTGRES_HOST
    POSTGRES_HOST_AUTH_METHOD: Optional[str] = None  # Not used in code but allow to avoid validation failure

    DATABASE_URL: Optional[PostgresDsn] = None

    ADMIN_USER: str
    ADMIN_PASSWORD: str
    ADMIN_DATABASE_URL: Optional[PostgresDsn] = None

    ODBC_DSN: Optional[str] = None
    ODBC_USER: Optional[str] = None
    ODBC_PASSWORD: Optional[str] = None
    API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None  # Accept GEMINI key directly
    LOGFIRE_TOKEN: Optional[str] = None   # Observability token (optional)
    MAX_LONG_DATA: Optional[int] = None

    @model_validator(mode="before")
    def assemble_db_urls(cls, v: Any) -> Any:
        if isinstance(v, dict):
            # Support POSTGRES_HOST as an alias for POSTGRES_SERVER if provided
            if not v.get("POSTGRES_SERVER") and v.get("POSTGRES_HOST"):
                v["POSTGRES_SERVER"] = v.get("POSTGRES_HOST")
            port = v.get("POSTGRES_PORT")
            if port is not None:
                port = int(port)

            db_name = v.get("POSTGRES_DB") or ""

            # Regular user connection
            v["DATABASE_URL"] = str(
                PostgresDsn.build(
                    scheme="postgresql",
                    username=v.get("POSTGRES_USER"),
                    password=v.get("POSTGRES_PASSWORD"),
                    host=v.get("POSTGRES_SERVER"),
                    port=port,
                    path=f"{db_name}",
                )
            )

            # Admin user connection
            v["ADMIN_DATABASE_URL"] = str(
                PostgresDsn.build(
                    scheme="postgresql",
                    username=v.get("ADMIN_USER"),
                    password=v.get("ADMIN_PASSWORD"),
                    host=v.get("POSTGRES_SERVER"),
                    port=port,
                    path=f"{db_name}",
                )
            )
        return v

    # JWT settings
    SECRET_KEY: str = "your_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 18000

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # File storage settings
    RESUME_STORAGE_DIR: str = "resumes"

    # Email settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""

    # OTP settings
    OTP_EXPIRE_MINUTES: int = 10
    OTP_LENGTH: int = 6

    # Batch job scheduler settings
    ENABLE_BATCH_SCHEDULER: bool = True
    RESUME_PARSER_INTERVAL_MINUTES: int = 1
    APPLICATION_MATCHER_INTERVAL_MINUTES: int = 1

    # CORS settings
    CORS_ALLOWED_ORIGINS: List[str] = ["*"]

    ADMIN_USER: str = "charbel"
    ADMIN_PASSWORD: str = "charbel"

    # AI service settings
    AI_URL: str = "http://ai:8011"
    AI_PORT: int = 8011

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Any) -> Union[List[str], str]:
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        # Default to allow all if not set or invalid type
        return ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# ---------------------------------------------------------------------------
# Backward-compatibility constants
# ---------------------------------------------------------------------------
# NOTE: These aliases expose the values from the `settings` object at module
# level so that existing code written as `from core.config import XYZ` keeps
# working after the refactor to a Pydantic `Settings` instance.
# They should be considered deprecated – prefer importing `settings` instead.
DATABASE_URL: str = str(settings.DATABASE_URL) if settings.DATABASE_URL else ""
ADMIN_DATABASE_URL: str = (
    str(settings.ADMIN_DATABASE_URL) if settings.ADMIN_DATABASE_URL else ""
)
DEBUG_MODE: bool = settings.DEBUG_MODE

# JWT
SECRET_KEY: str = settings.SECRET_KEY
ALGORITHM: str = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# File storage
RESUME_STORAGE_DIR: str = settings.RESUME_STORAGE_DIR

# Email
SMTP_HOST: str = settings.SMTP_HOST
SMTP_PORT: int = settings.SMTP_PORT
SMTP_USERNAME: str = settings.SMTP_USERNAME
SMTP_PASSWORD: str = settings.SMTP_PASSWORD
FROM_EMAIL: str = settings.FROM_EMAIL

# OTP
OTP_EXPIRE_MINUTES: int = settings.OTP_EXPIRE_MINUTES
OTP_LENGTH: int = settings.OTP_LENGTH

# CORS
CORS_ALLOWED_ORIGINS: list[str] = settings.CORS_ALLOWED_ORIGINS

# Google OAuth
GOOGLE_CLIENT_ID: Optional[str] = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET: Optional[str] = settings.GOOGLE_CLIENT_SECRET
