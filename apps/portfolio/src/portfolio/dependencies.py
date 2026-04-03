"""Вспомогательные зависимости приложения."""

import json
import re
from datetime import date
from functools import lru_cache

from fastapi.templating import Jinja2Templates
from portfolio.config import Settings

PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def _replace_placeholders(data: object, values: dict[str, str]) -> object:
    if isinstance(data, str):
        return PLACEHOLDER_RE.sub(
            lambda match: values.get(match.group(1), match.group(0)),
            data,
        )

    if isinstance(data, list):
        return [_replace_placeholders(item, values) for item in data]

    if isinstance(data, dict):
        return {
            key: _replace_placeholders(value, values)
            for key, value in data.items()
        }

    return data


def _build_template_values(settings: Settings) -> dict[str, str]:
    values_path = settings.content_dir / "values.json"
    with values_path.open("r", encoding="utf-8-sig") as file:
        values_payload = json.load(file)

    locale_values = values_payload.get("i18n", {}).get(settings.default_locale, {})
    values: dict[str, str] = {
        key: str(value) for key, value in locale_values.items()
    }

    start_date_str = values.get("EXPERIENCE_START_DATE")
    if start_date_str:
        start_date = date.fromisoformat(start_date_str)
        values["EXPERIENCE_DAYS"] = str((date.today() - start_date).days)

    return values


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
    """Загружает контент сайта из JSON-файлов."""

    settings = get_settings()
    template_values = _build_template_values(settings)
    content_files = {
        "basic": "basic_content.json",
        "main": "main.json",
        "constructor": "constructor.json",
        "planner": "planner.json",
        "developer": "developer.json",
        "technologist": "technologist.json",
        "work_places": "work_places.json",
        "education": "education.json",
        "agreement": "polzovatelskoe_soglashenie.json",
        "privacy": "politika_konfidencialnosti.json",
    }

    content: dict = {}
    for section_name, filename in content_files.items():
        content_path = settings.content_dir / filename
        with content_path.open("r", encoding="utf-8-sig") as file:
            raw_content = json.load(file)
            content[section_name] = _replace_placeholders(
                raw_content, template_values
            )

    return content


@lru_cache
def get_ui_texts() -> dict:
    """Загружает текст интерфейса в соответствии с локалью."""

    settings = get_settings()
    locale_file = settings.i18n_dir / f"ui_{settings.default_locale}.json"
    if not locale_file.exists():
        locale_file = settings.i18n_dir / "ui_en.json"

    with locale_file.open("r", encoding="utf-8") as file:
        return json.load(file)
