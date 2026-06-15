"""Конфигурация представления (как показывать), отдельно от content/."""

import json
from functools import lru_cache

from portfolio.config import Settings
from portfolio.dependencies import get_settings


@lru_cache
def get_developer_portfolio_bubbles_layout() -> dict:
    """Диаметры и физика пузырьков IT-портфолио по id проекта."""
    settings = get_settings()
    return _read_presentation_json(
        settings, "developer_portfolio_bubbles.json"
    )


def _read_presentation_json(settings: Settings, filename: str) -> dict:
    layout_path = settings.app_dir / "layout" / filename
    with layout_path.open("r", encoding="utf-8-sig") as file:
        payload = json.load(file)
    return payload if isinstance(payload, dict) else {}
