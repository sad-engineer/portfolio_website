"""Настройки приложения Portfolio."""

from pathlib import Path

from portfolio._version import get_version
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Базовые настройки приложения."""

    app_name: str = "Portfolio"
    app_version: str = get_version()
    debug: bool = False

    base_dir: Path = Path(__file__).resolve().parents[2]
    app_dir: Path = base_dir / "src" / "portfolio"
    static_dir: Path = app_dir / "static"
    templates_dir: Path = app_dir / "templates"
    content_dir: Path = base_dir / "content"
    i18n_dir: Path = base_dir / "i18n"

    default_locale: str = "ru"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
