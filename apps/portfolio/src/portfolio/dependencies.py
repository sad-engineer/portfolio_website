"""Вспомогательные зависимости приложения."""

import json
import re
from datetime import date
from functools import lru_cache

from fastapi.templating import Jinja2Templates

from portfolio.config import Settings

PLACEHOLDER_RE = re.compile(r"\{\{([A-Za-z0-9_]+)\}\}")
PERIOD_START_RE = re.compile(r"^\s*(\d{2})\.(\d{4})\s*")


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

    if not isinstance(values_payload, dict):
        values_payload = {}
    base_values = {
        key: value for key, value in values_payload.items() if key != "i18n"
    }
    i18n_values = values_payload.get("i18n", {})
    locale_overlay: dict = {}
    if isinstance(i18n_values, dict):
        raw_overlay = i18n_values.get(settings.default_locale, {})
        if isinstance(raw_overlay, dict):
            locale_overlay = raw_overlay
    merged_values = {**base_values, **locale_overlay}
    values: dict[str, str] = {
        key: str(value) for key, value in merged_values.items()
    }

    # Дополнительно экспортируем значения локалей как KEY_<LOCALE>, например ADDRESS_EN.
    # Это нужно для плейсхолдеров в переводах юридических документов.
    if isinstance(i18n_values, dict):
        for locale, overlay in i18n_values.items():
            if not isinstance(locale, str) or not isinstance(overlay, dict):
                continue
            locale_suffix = locale.upper()
            for key, value in overlay.items():
                if not isinstance(key, str):
                    continue
                values[f"{key}_{locale_suffix}"] = str(value)

    # Обратная совместимость для шаблонов с суффиксами RU/EN.
    if "ADDRESS" in values and "ADDRESS_RU" not in values:
        values["ADDRESS_RU"] = values["ADDRESS"]

    work_places_path = settings.content_dir / "work_places.json"
    with work_places_path.open("r", encoding="utf-8-sig") as file:
        work_places_payload = json.load(file)

    start_dates: list[date] = []
    for item in work_places_payload.get("items", []):
        period = str(item.get("period", ""))
        period_start = period.split("-", 1)[0].strip()
        period_start_match = PERIOD_START_RE.match(period_start)
        if not period_start_match:
            continue

        month = int(period_start_match.group(1))
        year = int(period_start_match.group(2))
        if month < 1 or month > 12:
            continue

        start_dates.append(date(year, month, 1))

    if start_dates:
        earliest_start_date = min(start_dates)
        values["EXPERIENCE_DAYS"] = str(
            (date.today() - earliest_start_date).days
        )
    else:
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
        "portfolio_projects": "portfolio_projects.json",
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
    """UI-тексты вынесены в content/*.json, отдельный i18n-каталог больше не используется."""
    return {}
