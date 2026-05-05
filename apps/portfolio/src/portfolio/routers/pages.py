"""Обработчики основных страниц сайта."""

import json
import re
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from portfolio.dependencies import (
    get_settings,
    get_site_content,
    get_templates,
    get_ui_texts,
)

router = APIRouter(tags=["pages"])

# Имя cookie для сохранения выбранной локали (совпадает с middleware в main.py).
LANG_COOKIE_NAME = "portfolio_lang"


def _deep_merge_dicts(base: dict, overlay: dict) -> dict:
    merged = deepcopy(base)
    for key, value in overlay.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _localized_content_block(block: dict, current_lang: str) -> dict:
    if not isinstance(block, dict):
        return {}

    base_payload = {
        key: deepcopy(value) for key, value in block.items() if key != "i18n"
    }

    if current_lang == "en":
        en_overlay = block.get("i18n", {}).get("en", {})
        if isinstance(en_overlay, dict):
            return _deep_merge_dicts(base_payload, en_overlay)

    return base_payload


def _apply_label_tags(node: object, tags: dict) -> None:
    """Подставляет переводы по словарю tags для полей label и title (ключ — исходная строка)."""
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
    """Подставляет перевод description по русскому label (до замены tags на EN)."""
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
    """Вложенный формат: tags.labels / tags.descriptions — объекты-словари, не строки."""
    labels = tag_bundle.get("labels")
    descriptions = tag_bundle.get("descriptions")
    return isinstance(labels, dict) or isinstance(descriptions, dict)


def _localized_profession_block(block: dict, current_lang: str) -> dict:
    """Локализует JSON страницы профессии: sections, tags.labels (подписи), tags.descriptions (описания плиток)."""
    if not isinstance(block, dict):
        return {}

    base_payload = {
        key: deepcopy(value) for key, value in block.items() if key != "i18n"
    }

    if current_lang != "en":
        return base_payload

    en_overlay = block.get("i18n", {}).get("en", {})
    if not isinstance(en_overlay, dict):
        return base_payload

    merged = _deep_merge_dicts(base_payload, en_overlay)

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

    return merged


_PROFESSION_KEYS = ("constructor", "planner", "developer", "technologist")
PERIOD_END_RE = re.compile(r"(\d{2})\.(\d{4})\s*$")


def _period_end_sort_key(item: dict) -> tuple[int, int]:
    """Возвращает ключ сортировки по дате окончания периода (месяц, год)."""
    period = str(item.get("period", ""))
    period_parts = period.split("-", 1)
    period_end = (
        period_parts[1].strip() if len(period_parts) > 1 else period.strip()
    )
    match = PERIOD_END_RE.search(period_end)
    if not match:
        return (0, 0)

    month = int(match.group(1))
    year = int(match.group(2))
    if month < 1 or month > 12:
        return (0, 0)
    return (year, month)


def _profession_work_experience_items(
    work_places_locale: dict, profession_key: str
) -> list[dict]:
    """Возвращает места работы, относящиеся к выбранной профессии."""
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

    scoped_items.sort(key=_period_end_sort_key, reverse=True)
    return scoped_items


def _profession_portfolio_items(
    portfolio_locale: dict, profession_key: str
) -> list[dict]:
    """Возвращает проекты портфолио, относящиеся к выбранной профессии."""
    source_items = portfolio_locale.get("items", [])
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

    return scoped_items


def _education_year_sort_key(item: dict) -> int:
    """Возвращает числовой год для сортировки элементов образования (по убыванию)."""
    year_raw = str(item.get("year", "")).strip()
    if not year_raw.isdigit():
        return 0
    return int(year_raw)


def _profession_education_items(
    education_locale: dict, profession_key: str
) -> list[dict]:
    """Возвращает элементы образования, относящиеся к выбранной профессии."""
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

    scoped_items.sort(key=_education_year_sort_key, reverse=True)
    return scoped_items


def _append_lang_query(href: str, lang: str) -> str:
    """Добавляет lang= к внутренним путям, чтобы навигация не сбрасывала локаль."""
    if (
        not isinstance(href, str)
        or not href.startswith("/")
        or href.startswith("//")
    ):
        return href
    if "lang=" in href:
        return href
    joiner = "&" if "?" in href else "?"
    return f"{href}{joiner}lang={lang}"


def _navigation_with_lang_urls(nav: dict, lang: str) -> dict:
    patched = deepcopy(nav)
    for item in patched.get("items", []):
        h = item.get("href")
        if isinstance(h, str):
            item["href"] = _append_lang_query(h, lang)
    return patched


def _main_locale_with_direction_lang(main_locale: dict, lang: str) -> dict:
    """Карточки направлений на главной: url с текущей локалью."""
    out = deepcopy(main_locale)
    direction = out.get("direction")
    if isinstance(direction, dict):
        for card in direction.get("cards", []):
            if isinstance(card, dict):
                u = card.get("url")
                if isinstance(u, str):
                    card["url"] = _append_lang_query(u, lang)
    return out


def _load_values_locale(current_lang: str) -> dict:
    """Читает values.json и возвращает словарь значений для текущей локали."""
    settings = get_settings()
    values_path = settings.content_dir / "values.json"
    with values_path.open("r", encoding="utf-8-sig") as file:
        values_payload = json.load(file)

    if not isinstance(values_payload, dict):
        return {}

    # Базовые значения + локализованный overlay в i18n.<lang>
    base_values = {
        key: deepcopy(value)
        for key, value in values_payload.items()
        if key != "i18n"
    }
    i18n_values = values_payload.get("i18n", {})
    if not isinstance(i18n_values, dict):
        return base_values

    locale_values = i18n_values.get(current_lang)
    if isinstance(locale_values, dict):
        return _deep_merge_dicts(base_values, locale_values)

    fallback_values = i18n_values.get("ru")
    if isinstance(fallback_values, dict):
        return _deep_merge_dicts(base_values, fallback_values)

    return base_values


def _parse_hhmm_to_minutes(value: object) -> Optional[int]:
    if not isinstance(value, str):
        return None
    parts = value.split(":", 1)
    if len(parts) != 2:
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return None
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    return hour * 60 + minute


def _is_within_working_hours(values_locale: dict) -> bool:
    """Проверяет, попадает ли текущее время в рабочий график для показа телефонной иконки."""
    timezone_name = str(values_locale.get("WORK_TIMEZONE", "UTC"))
    work_schedule = values_locale.get("WORK_SCHEDULE")

    try:
        tz = ZoneInfo(timezone_name)
        now = datetime.now(tz)
    except Exception:
        # На Windows без tzdata ZoneInfo может быть недоступен.
        # В этом случае используем фиксированный offset для известных рабочих зон.
        known_offsets_hours = {
            "UTC": 0,
            "Asia/Yekaterinburg": 5,
        }
        offset_hours = known_offsets_hours.get(timezone_name)
        if offset_hours is None:
            now = datetime.now()
        else:
            now = (
                datetime.now(timezone.utc) + timedelta(hours=offset_hours)
            ).replace(tzinfo=None)
    current_minutes = now.hour * 60 + now.minute
    weekday_key = str(now.isoweekday())

    # Новый формат: WORK_SCHEDULE = {"1":[{"start":"09:00","end":"18:00"}], ..., "7":[]}
    if isinstance(work_schedule, dict):
        day_ranges = work_schedule.get(weekday_key, [])
        if not isinstance(day_ranges, list):
            return True
        for day_range in day_ranges:
            if not isinstance(day_range, dict):
                continue
            start_minutes = _parse_hhmm_to_minutes(day_range.get("start"))
            end_minutes = _parse_hhmm_to_minutes(day_range.get("end"))
            if start_minutes is None or end_minutes is None:
                continue
            if start_minutes <= current_minutes < end_minutes:
                return True
        return False

    # Legacy-формат (для обратной совместимости).
    raw_days = str(values_locale.get("WORK_DAYS", "1,2,3,4,5"))
    day_items = [item.strip() for item in raw_days.split(",") if item.strip()]
    try:
        allowed_weekdays = {int(day) for day in day_items}
    except ValueError:
        return True
    if now.isoweekday() not in allowed_weekdays:
        return False
    start_minutes = _parse_hhmm_to_minutes(
        values_locale.get("WORK_HOURS_START", "09:00")
    )
    end_minutes = _parse_hhmm_to_minutes(
        values_locale.get("WORK_HOURS_END", "18:00")
    )
    if start_minutes is None or end_minutes is None:
        return True
    return start_minutes <= current_minutes < end_minutes


def _resolve_current_lang(request: Request, site_content: dict) -> str:
    supported_locales = tuple(
        site_content.get("basic", {})
        .get("site", {})
        .get("locales", ["ru", "en"])
    )
    default_locale = (
        site_content.get("basic", {}).get("site", {}).get("language", "ru")
    )

    query_lang = request.query_params.get("lang")
    if query_lang in supported_locales:
        return query_lang

    cookie_lang = request.cookies.get(LANG_COOKIE_NAME)
    if cookie_lang in supported_locales:
        return cookie_lang

    if default_locale in supported_locales:
        return default_locale
    return supported_locales[0] if supported_locales else "ru"


def _build_context(
    request: Request, site_content: dict, ui_texts: dict
) -> dict:
    current_lang = _resolve_current_lang(request, site_content)
    values_locale = _load_values_locale(current_lang)

    basic_locale = _localized_content_block(
        site_content.get("basic", {}), current_lang
    )
    main_locale = _main_locale_with_direction_lang(
        _localized_content_block(site_content.get("main", {}), current_lang),
        current_lang,
    )
    main_nav_locale = _navigation_with_lang_urls(
        basic_locale.get("navigation", {}),
        current_lang,
    )

    social_links: list[dict] = []
    show_phone_link = _is_within_working_hours(values_locale)
    for item in main_locale.get("social", []):
        link_url = str(item.get("url", ""))
        icon = str(item.get("icon", ""))
        icon_lc = icon.lower()
        is_phone_entry = link_url.startswith("tel:") or "phone" in icon_lc
        if is_phone_entry and not show_phone_link:
            continue
        is_asset_icon = (
            "/" in icon
            or icon_lc.endswith(".svg")
            or icon_lc.endswith(".png")
            or icon_lc.endswith(".jpg")
            or icon_lc.endswith(".jpeg")
            or icon_lc.endswith(".webp")
            or icon_lc.endswith(".gif")
        )
        social_links.append(
            {
                "icon": icon,
                "url": link_url,
                "is_asset_icon": is_asset_icon,
            }
        )

    profession_locale = {
        key: _localized_profession_block(
            site_content.get(key, {}), current_lang
        )
        for key in _PROFESSION_KEYS
    }
    work_places_locale = _localized_content_block(
        site_content.get("work_places", {}), current_lang
    )
    profession_work_experience = {
        key: _profession_work_experience_items(work_places_locale, key)
        for key in _PROFESSION_KEYS
    }
    portfolio_projects_locale = _localized_content_block(
        site_content.get("portfolio_projects", {}), current_lang
    )
    profession_portfolio_projects = {
        key: _profession_portfolio_items(portfolio_projects_locale, key)
        for key in _PROFESSION_KEYS
    }
    education_locale = _localized_content_block(
        site_content.get("education", {}), current_lang
    )
    profession_education = {
        key: _profession_education_items(education_locale, key)
        for key in _PROFESSION_KEYS
    }

    links = basic_locale.get("links", {})
    agreement_path = str(
        links.get("userAgreement", {}).get(
            "href", "/polzovatelskoe-soglashenie"
        )
    )
    privacy_path = str(
        links.get("privacyPolicy", {}).get(
            "href", "/politika-konfidencialnosti"
        )
    )

    return {
        "request": request,
        "content": site_content,
        "ui": ui_texts,
        "current_lang": current_lang,
        "basic_locale": basic_locale,
        "main_locale": main_locale,
        "main_nav_locale": main_nav_locale,
        "social_links": social_links,
        "work_hours_refresh": {
            "timezone": str(values_locale.get("WORK_TIMEZONE", "UTC")),
            "schedule": values_locale.get("WORK_SCHEDULE"),
            "work_days": str(values_locale.get("WORK_DAYS", "1,2,3,4,5")),
            "work_hours_start": str(
                values_locale.get("WORK_HOURS_START", "09:00")
            ),
            "work_hours_end": str(
                values_locale.get("WORK_HOURS_END", "18:00")
            ),
            "is_within_working_hours": show_phone_link,
        },
        "profession_locale": profession_locale,
        "work_places_locale": work_places_locale,
        "profession_work_experience": profession_work_experience,
        "portfolio_projects_locale": portfolio_projects_locale,
        "profession_portfolio_projects": profession_portfolio_projects,
        "education_locale": education_locale,
        "profession_education": profession_education,
        "home_href": _append_lang_query("/main", current_lang),
        "user_agreement_href": _append_lang_query(
            agreement_path, current_lang
        ),
        "privacy_policy_href": _append_lang_query(privacy_path, current_lang),
    }


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Главная страница портфолио."""
    return templates.TemplateResponse(
        "main.html", _build_context(request, site_content, ui_texts)
    )


@router.get("/main", response_class=HTMLResponse)
async def main_page(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Главная страница портфолио."""
    return templates.TemplateResponse(
        "main.html", _build_context(request, site_content, ui_texts)
    )


@router.get("/constructor", response_class=HTMLResponse)
async def constructor_page(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Страница конструктора."""
    return templates.TemplateResponse(
        "constructor.html", _build_context(request, site_content, ui_texts)
    )


@router.get("/planner", response_class=HTMLResponse)
async def planner_page(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Страница проектировщика."""
    return templates.TemplateResponse(
        "planner.html", _build_context(request, site_content, ui_texts)
    )


@router.get("/developer", response_class=HTMLResponse)
async def developer_page(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Страница разработчика."""
    return templates.TemplateResponse(
        "developer.html", _build_context(request, site_content, ui_texts)
    )


@router.get("/technologist", response_class=HTMLResponse)
async def technologist_page(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Страница технолога."""
    return templates.TemplateResponse(
        "technologist.html", _build_context(request, site_content, ui_texts)
    )


@router.get("/polzovatelskoe_soglashenie", response_class=HTMLResponse)
@router.get("/polzovatelskoe-soglashenie", response_class=HTMLResponse)
async def soglashenie(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Страница соглашения."""
    return templates.TemplateResponse(
        "polzovatelskoe_soglashenie.html",
        _build_context(request, site_content, ui_texts),
    )


@router.get("/politika_konfidencialnosti", response_class=HTMLResponse)
@router.get("/politika-konfidencialnosti", response_class=HTMLResponse)
async def politika_konfidencialnosti(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Страница политики конфиденциальности."""
    return templates.TemplateResponse(
        "politika_konfidencialnosti.html",
        _build_context(request, site_content, ui_texts),
    )


@router.get("/work_places", response_class=HTMLResponse)
async def work_places(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Страница мест работы."""
    return templates.TemplateResponse(
        "work_places.html", _build_context(request, site_content, ui_texts)
    )


@router.get("/education", response_class=HTMLResponse)
async def education_page(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Страница образования."""
    return templates.TemplateResponse(
        "education.html", _build_context(request, site_content, ui_texts)
    )
