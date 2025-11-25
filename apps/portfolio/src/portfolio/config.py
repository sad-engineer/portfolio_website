"""Настройки приложения Portfolio."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Базовые настройки приложения."""

    app_name: str = "Portfolio"
    app_version: str = "0.1.0"
    debug: bool = False

    base_dir: Path = Path(__file__).resolve().parent
    static_dir: Path = Path(__file__).resolve().parent / "static"
    templates_dir: Path = Path(__file__).resolve().parent / "templates"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

