"""Вспомогательные зависимости приложения."""

import json
from functools import lru_cache
from pathlib import Path

from fastapi.templating import Jinja2Templates

from .config import Settings


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
    content_path = Path(settings.base_dir).parent.parent / "content" / "site_content.json"
    with content_path.open("r", encoding="utf-8") as file:
        return json.load(file)

