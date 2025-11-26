"""Вспомогательные зависимости приложения."""

import json
from functools import lru_cache

from fastapi.templating import Jinja2Templates
from portfolio.config import Settings


@lru_cache
def get_settings() -> Settings:
    """Возвращает singleton экземпляр настроек."""

    return Settings()


@lru_cache
def get_templates() -> Jinja2Templates:
    """Создаёт и кэширует Jinja2Templates."""

    settings = get_settings()
    return Jinja2Templates(directory=str(settings.templates_dir))


@lru_cache
def get_site_content() -> dict:
    """Загружает контент сайта из JSON."""

    settings = get_settings()
    content_path = settings.content_dir / "site_content.json"
    with content_path.open("r", encoding="utf-8") as file:
        return json.load(file)


@lru_cache
def get_ui_texts() -> dict:
    """Загружает текст интерфейса в соответствии с локалью."""

    settings = get_settings()
    locale_file = settings.i18n_dir / f"ui_{settings.default_locale}.json"
    if not locale_file.exists():
        locale_file = settings.i18n_dir / "ui_en.json"

    with locale_file.open("r", encoding="utf-8") as file:
        return json.load(file)
