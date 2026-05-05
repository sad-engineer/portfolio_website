"""Настройки приложения Portfolio."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from portfolio._version import get_version


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

    default_locale: str = "ru"
    feedback_smtp_host: str = Field(default="", alias="FEEDBACK_SMTP_HOST")
    feedback_smtp_port: int = Field(default=587, alias="FEEDBACK_SMTP_PORT")
    feedback_smtp_user: str = Field(default="", alias="FEEDBACK_SMTP_USER")
    feedback_smtp_password: str = Field(
        default="", alias="FEEDBACK_SMTP_PASSWORD"
    )
    feedback_smtp_to: str = Field(default="", alias="FEEDBACK_SMTP_TO")
    feedback_telegram_bot_token: str = Field(
        default="", alias="FEEDBACK_TELEGRAM_BOT_TOKEN"
    )
    feedback_telegram_chat_id: str = Field(
        default="", alias="FEEDBACK_TELEGRAM_CHAT_ID"
    )
    feedback_delivery_retries: int = Field(
        default=2, alias="FEEDBACK_DELIVERY_RETRIES"
    )
    feedback_delivery_retry_delay_ms: int = Field(
        default=400, alias="FEEDBACK_DELIVERY_RETRY_DELAY_MS"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )
