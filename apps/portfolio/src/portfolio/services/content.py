"""Локализация и слияние контентных JSON-блоков."""

from __future__ import annotations

import json
from copy import deepcopy

from portfolio.dependencies import get_settings


def deep_merge_dicts(base: dict, overlay: dict) -> dict:
    merged = deepcopy(base)
    for key, value in overlay.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge_dicts(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def localized_content_block(block: dict, current_lang: str) -> dict:
    if not isinstance(block, dict):
        return {}

    base_payload = {
        key: deepcopy(value) for key, value in block.items() if key != "i18n"
    }

    if current_lang == "en":
        en_overlay = block.get("i18n", {}).get("en", {})
        if isinstance(en_overlay, dict):
            merge_overlay = {
                key: value
                for key, value in en_overlay.items()
                if key != "itemTitles"
            }
            merged = deep_merge_dicts(base_payload, merge_overlay)
            item_titles = en_overlay.get("itemTitles")
            if isinstance(item_titles, dict):
                items = merged.get("items", [])
                if isinstance(items, list):
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        item_id = str(item.get("id", "")).strip()
                        translated = item_titles.get(item_id)
                        if isinstance(translated, str):
                            item["title"] = translated
            return merged

    return base_payload


def load_values_locale(current_lang: str) -> dict:
    """Читает values.json и возвращает словарь значений для текущей локали."""
    settings = get_settings()
    values_path = settings.content_dir / "values.json"
    with values_path.open("r", encoding="utf-8-sig") as file:
        values_payload = json.load(file)

    if not isinstance(values_payload, dict):
        return {}

    base_values = {
        key: deepcopy(value) for key, value in values_payload.items() if key != "i18n"
    }
    i18n_values = values_payload.get("i18n", {})
    if not isinstance(i18n_values, dict):
        return base_values

    locale_values = i18n_values.get(current_lang)
    if isinstance(locale_values, dict):
        return deep_merge_dicts(base_values, locale_values)

    fallback_values = i18n_values.get("ru")
    if isinstance(fallback_values, dict):
        return deep_merge_dicts(base_values, fallback_values)

    return base_values


def append_lang_query(href: str, lang: str) -> str:
    """Добавляет lang= к внутренним путям, чтобы навигация не сбрасывала локаль."""
    if not isinstance(href, str) or not href.startswith("/") or href.startswith("//"):
        return href
    if "lang=" in href:
        return href
    joiner = "&" if "?" in href else "?"
    return f"{href}{joiner}lang={lang}"


def navigation_with_lang_urls(nav: dict, lang: str) -> dict:
    patched = deepcopy(nav)
    for item in patched.get("items", []):
        href = item.get("href")
        if isinstance(href, str):
            item["href"] = append_lang_query(href, lang)
    return patched


def main_locale_with_direction_lang(main_locale: dict, lang: str) -> dict:
    """Карточки направлений на главной: url с текущей локалью."""
    out = deepcopy(main_locale)
    direction = out.get("direction")
    if isinstance(direction, dict):
        for card in direction.get("cards", []):
            if isinstance(card, dict):
                url = card.get("url")
                if isinstance(url, str):
                    card["url"] = append_lang_query(url, lang)
    return out
