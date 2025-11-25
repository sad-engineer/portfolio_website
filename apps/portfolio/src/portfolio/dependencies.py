"""Вспомогательные зависимости приложения."""

from functools import lru_cache

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

