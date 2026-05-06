"""Настройки приложения Portfolio."""

from pathlib import Path

from portfolio._version import get_version
from pydantic import Field
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

    default_locale: str = "ru"
    phone_e164: str = Field(default="", alias="PHONE_E164")
    github_url: str = Field(default="", alias="GITHUB_URL")
    telegram_url: str = Field(default="", alias="TELEGRAM_URL")
    profi_ru_url: str = Field(default="", alias="PROFI_RU_URL")
    hh_ru_url: str = Field(default="", alias="HH_RU_URL")
    freelance_ru_url: str = Field(default="", alias="FREELANCE_RU_URL")

    feedback_smtp_host: str = Field(default="", alias="FEEDBACK_SMTP_HOST")
    feedback_smtp_port: int = Field(default=587, alias="FEEDBACK_SMTP_PORT")
    feedback_smtp_user: str = Field(default="", alias="FEEDBACK_SMTP_USER")
    feedback_smtp_password: str = Field(default="", alias="FEEDBACK_SMTP_PASSWORD")
    feedback_smtp_to: str = Field(default="", alias="FEEDBACK_SMTP_TO")
    feedback_smtp_timeout_seconds: int = Field(
        default=25, alias="FEEDBACK_SMTP_TIMEOUT_SECONDS"
    )
    feedback_smtp_security: str = Field(default="ssl", alias="FEEDBACK_SMTP_SECURITY")
    feedback_turnstile_site_key: str = Field(
        default="", alias="FEEDBACK_TURNSTILE_SITE_KEY"
    )
    feedback_turnstile_secret_key: str = Field(
        default="", alias="FEEDBACK_TURNSTILE_SECRET_KEY"
    )
    feedback_turnstile_timeout_seconds: int = Field(
        default=8, alias="FEEDBACK_TURNSTILE_TIMEOUT_SECONDS"
    )
    feedback_telegram_bot_token: str = Field(
        default="", alias="FEEDBACK_TELEGRAM_BOT_TOKEN"
    )
    feedback_telegram_chat_id: str = Field(
        default="", alias="FEEDBACK_TELEGRAM_CHAT_ID"
    )
    feedback_delivery_retries: int = Field(default=2, alias="FEEDBACK_DELIVERY_RETRIES")
    feedback_delivery_retry_delay_ms: int = Field(
        default=400, alias="FEEDBACK_DELIVERY_RETRY_DELAY_MS"
    )
    feedback_rate_limit_max_requests: int = Field(
        default=30, alias="FEEDBACK_RATE_LIMIT_MAX_REQUESTS"
    )
    feedback_rate_limit_window_seconds: int = Field(
        default=600, alias="FEEDBACK_RATE_LIMIT_WINDOW_SECONDS"
    )
    feedback_rate_limit_min_interval_seconds: int = Field(
        default=120, alias="FEEDBACK_RATE_LIMIT_MIN_INTERVAL_SECONDS"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
