"""Подготовка данных страниц профессий и плиток технологий."""

from __future__ import annotations

import re
from copy import deepcopy

from portfolio.services.content import deep_merge_dicts
from portfolio.services.html_sanitize import static_asset_url

PROFESSION_KEYS = ("constructor", "planner", "developer", "technologist")

_RASTER_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".gif")
_RASTER_FILL_ICON_SUFFIXES = ("vertikal.jpg", "vertikal.png")
_MULTICOLOR_SVG_ICON_SUFFIX = "flowvision.svg"

PERIOD_END_RE = re.compile(r"(\d{2})\.(\d{4})\s*$")


def _apply_label_tags(node: object, tags: dict) -> None:
    if isinstance(node, dict):
        for field in ("label", "title"):
            text = node.get(field)
            if isinstance(text, str) and text in tags:
                node[field] = tags[text]
        for value in node.values():
            _apply_label_tags(value, tags)
    elif isinstance(node, list):
        for item in node:
            _apply_label_tags(item, tags)


def _apply_descriptions_by_label(node: object, descriptions: dict) -> None:
    if isinstance(node, dict):
        label = node.get("label")
        if (
            isinstance(label, str)
            and label in descriptions
            and "description" in node
            and isinstance(node.get("description"), str)
        ):
            node["description"] = descriptions[label]
        for value in node.values():
            _apply_descriptions_by_label(value, descriptions)
    elif isinstance(node, list):
        for item in node:
            _apply_descriptions_by_label(item, descriptions)


def _tag_bundle_is_nested(tag_bundle: dict) -> bool:
    labels = tag_bundle.get("labels")
    descriptions = tag_bundle.get("descriptions")
    return isinstance(labels, dict) or isinstance(descriptions, dict)


def _build_tech_tile_class(item: dict) -> str:
    classes = ["tech-tile"]
    if item.get("isSvg"):
        classes.append("tech-tile--svg")
        if item.get("isMulticolorSvg"):
            classes.append("tech-tile--svg-multicolor")
    elif item.get("isRaster"):
        classes.append("tech-tile--raster")
        if item.get("isRasterFill"):
            classes.append("tech-tile--raster-fill")
    return " ".join(classes)


def _build_tech_tile_render_mode(item: dict) -> str:
    if item.get("isSvg") and item.get("isMulticolorSvg"):
        return "multicolor_svg"
    if item.get("isRaster"):
        return "raster"
    if item.get("isSvg"):
        return "mono_svg"
    if item.get("icon"):
        return "font_icon"
    return "empty"


def enrich_tech_tile_item(item: dict) -> None:
    """Добавляет view-model поля плитки технологии для шаблона без логики в Jinja2."""
    icon_lc = str(item.get("icon", "")).strip().lower()
    item["isSvg"] = icon_lc.endswith(".svg")
    item["isRaster"] = icon_lc.endswith(_RASTER_IMAGE_SUFFIXES)
    item["isRasterFill"] = any(
        icon_lc.endswith(suffix) for suffix in _RASTER_FILL_ICON_SUFFIXES
    )
    item["isMulticolorSvg"] = icon_lc.endswith(_MULTICOLOR_SVG_ICON_SUFFIX)

    item["tileClass"] = _build_tech_tile_class(item)
    item["renderMode"] = _build_tech_tile_render_mode(item)
    item["hasDescription"] = bool(item.get("description"))
    item["rasterWidth"] = 60 if item.get("isRasterFill") else 43
    item["rasterHeight"] = 60 if item.get("isRasterFill") else 43

    icon_path = str(item.get("icon", "")).strip()
    if item.get("isSvg") and not item.get("isMulticolorSvg") and icon_path:
        item["tileStyle"] = (
            f"--tech-icon: url('{static_asset_url(icon_path)}');"
        )
    else:
        item["tileStyle"] = ""


def enrich_profession_tech_tiles(node: object) -> dict:
    """Обходит дерево профессии и обогащает объекты с icon+label."""
    if isinstance(node, dict):
        if "icon" in node and "label" in node:
            enrich_tech_tile_item(node)
        for value in node.values():
            if isinstance(value, (dict, list)):
                enrich_profession_tech_tiles(value)
    elif isinstance(node, list):
        for entry in node:
            if isinstance(entry, (dict, list)):
                enrich_profession_tech_tiles(entry)
    return node if isinstance(node, dict) else {}


def localized_profession_block(block: dict, current_lang: str) -> dict:
    """Локализует JSON страницы профессии и обогащает плитки технологий."""
    if not isinstance(block, dict):
        return {}

    base_payload = {
        key: deepcopy(value) for key, value in block.items() if key != "i18n"
    }

    if current_lang != "en":
        return enrich_profession_tech_tiles(base_payload)

    en_overlay = block.get("i18n", {}).get("en", {})
    if not isinstance(en_overlay, dict):
        return enrich_profession_tech_tiles(base_payload)

    merged = deep_merge_dicts(base_payload, en_overlay)

    sections = merged.pop("sections", None)
    if isinstance(sections, dict):
        for key, title in sections.items():
            section = merged.get(key)
            if isinstance(section, dict) and isinstance(title, str):
                section["title"] = title

    legacy_descriptions = merged.pop("descriptions", None)

    tag_bundle = merged.pop("tags", None)
    if isinstance(tag_bundle, dict) and _tag_bundle_is_nested(tag_bundle):
        nested_desc = tag_bundle.get("descriptions")
        if isinstance(nested_desc, dict):
            _apply_descriptions_by_label(merged, nested_desc)
        label_map = tag_bundle.get("labels")
        if isinstance(label_map, dict):
            _apply_label_tags(merged, label_map)
    elif isinstance(tag_bundle, dict):
        if isinstance(legacy_descriptions, dict):
            _apply_descriptions_by_label(merged, legacy_descriptions)
        _apply_label_tags(merged, tag_bundle)

    return enrich_profession_tech_tiles(merged)


def period_end_sort_key(item: dict) -> tuple[int, int]:
    period = str(item.get("period", ""))
    period_parts = period.split("-", 1)
    period_end = period_parts[1].strip() if len(period_parts) > 1 else period.strip()
    match = PERIOD_END_RE.search(period_end)
    if not match:
        return (0, 0)

    month = int(match.group(1))
    year = int(match.group(2))
    if month < 1 or month > 12:
        return (0, 0)
    return (year, month)


def profession_work_experience_items(
    work_places_locale: dict, profession_key: str
) -> list[dict]:
    source_items = work_places_locale.get("items", [])
    if not isinstance(source_items, list):
        return []

    scoped_items: list[dict] = []
    for item in source_items:
        if not isinstance(item, dict):
            continue
        role_tags = item.get("roleTags", [])
        if not isinstance(role_tags, list):
            continue
        if profession_key not in role_tags:
            continue
        scoped_items.append(item)

    scoped_items.sort(key=period_end_sort_key, reverse=True)
    return scoped_items


def education_year_sort_key(item: dict) -> int:
    year_raw = str(item.get("year", "")).strip()
    if not year_raw.isdigit():
        return 0
    return int(year_raw)


def profession_education_items(
    education_locale: dict, profession_key: str
) -> list[dict]:
    source_items = education_locale.get("items", [])
    if not isinstance(source_items, list):
        return []

    scoped_items: list[dict] = []
    for item in source_items:
        if not isinstance(item, dict):
            continue
        role_tags = item.get("roleTags", [])
        if not isinstance(role_tags, list):
            continue
        if profession_key not in role_tags:
            continue
        scoped_items.append(item)

    scoped_items.sort(key=education_year_sort_key, reverse=True)
    return scoped_items
