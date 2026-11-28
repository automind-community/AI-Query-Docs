"""Typed API configuration. Process variables take precedence over the project .env."""

import json
import os
from pathlib import Path
from typing import ClassVar

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    APP_NAME: str = Field(default="AI QueryDocs", min_length=1)
    APP_VERSION: str = Field(default="0.2.0", min_length=1)
    APP_ENV: str = Field(default="development", min_length=1)
    API_HOST: str = Field(default="127.0.0.1", min_length=1)
    API_PORT: int = Field(default=8000, ge=1, le=65535)
    CORS_ORIGINS: tuple[str, ...] = ("http://localhost:8501", "http://127.0.0.1:8501")
    MAX_FILE_SIZE_MB: int = Field(default=10, gt=0)
    ALLOWED_EXTENSIONS: ClassVar[tuple[str, ...]] = (".pdf", ".txt")

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        """Accept either a JSON array or comma-separated origins in .env."""
        if isinstance(value, str):
            return json.loads(value) if value.lstrip().startswith("[") else value.split(",")
        return value

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_origins(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        origins = []
        for value in values:
            url = HttpUrl(value)
            if url.username or url.password or url.path != "/" or url.query or url.fragment:
                raise ValueError("A CORS origin must contain only the scheme, host and optional port.")
            origins.append(str(url).removesuffix("/"))
        return tuple(origins)

    @classmethod
    def from_env(cls, env_file: Path = Path(__file__).resolve().parents[1] / ".env") -> "Settings":
        file_values = dotenv_values(env_file)
        values = {}
        for name in cls.model_fields:
            value = os.environ.get(name, file_values.get(name))
            if value is not None and value.strip():
                values[name] = value
        return cls.model_validate(values)
