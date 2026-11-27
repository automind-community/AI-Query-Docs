"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


def _get_str_env(name: str, default: str) -> str:
    """Return a stripped string env var, or default when unset or blank."""
    value = os.getenv(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped or default


def _get_int_env(name: str, default: int) -> int:
    """Return an integer env var, or default when unset or blank."""
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable {name} must be an integer, got {raw_value!r}."
        ) from exc


class Settings:
    """Runtime settings for the AI QueryDocs API."""

    APP_NAME: str = _get_str_env("APP_NAME", "AI QueryDocs")
    APP_ENV: str = _get_str_env("APP_ENV", "development")
    API_HOST: str = _get_str_env("API_HOST", "127.0.0.1")
    API_PORT: int = _get_int_env("API_PORT", 8000)


settings = Settings()
