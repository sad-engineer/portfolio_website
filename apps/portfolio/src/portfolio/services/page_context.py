"""Сборка контекста страниц для Jinja2-шаблонов."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import Request
from portfolio.dependencies import get_settings
from portfolio.presentation import get_developer_portfolio_bubbles_layout
from portfolio.services.content import (
    append_lang_query,
    load_values_locale,
    localized_content_block,
    main_locale_with_direction_lang,
    navigation_with_lang_urls,
)
from portfolio.services.html_sanitize import (
    build_bubble_footer_github_html,
    build_feedback_consent_html,
    build_hero_bottom_legal_html,
    sanitize_legal_html,
)
from portfolio.services.portfolio import profession_portfolio_items
from portfolio.services.profession import (
    PROFESSION_KEYS,
    localized_profession_block,
    profession_education_items,
    profession_work_experience_items,
)

LANG_COOKIE_NAME = "portfolio_lang"


def load_robots_txt() -> str:
    settings = get_settings()
    robots_path = settings.content_dir / "robots.txt"
    if robots_path.exists():
        return robots_path.read_text(encoding="utf-8-sig")
    return "User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /*?lang=\n"


def resolve_current_lang(request: Request, site_content: dict) -> str:
    supported_locales = tuple(
        site_content.get("basic", {}).get("site", {}).get("locales", ["ru", "en"])
    )
    default_locale = site_content.get("basic", {}).get("site", {}).get("language", "ru")

    query_lang = request.query_params.get("lang")
    if query_lang in supported_locales:
        return query_lang

    cookie_lang = request.cookies.get(LANG_COOKIE_NAME)
    if cookie_lang in supported_locales:
        return cookie_lang

    if default_locale in supported_locales:
        return default_locale
    return supported_locales[0] if supported_locales else "ru"


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


def is_within_working_hours(values_locale: dict) -> bool:
    timezone_name = str(values_locale.get("WORK_TIMEZONE", "UTC"))
    work_schedule = values_locale.get("WORK_SCHEDULE")

    try:
        tz = ZoneInfo(timezone_name)
        now = datetime.now(tz)
    except Exception:
        known_offsets_hours = {
            "UTC": 0,
            "Asia/Yekaterinburg": 5,
        }
        offset_hours = known_offsets_hours.get(timezone_name)
        if offset_hours is None:
            now = datetime.now()
        else:
            now = (datetime.now(timezone.utc) + timedelta(hours=offset_hours)).replace(
                tzinfo=None
            )
    current_minutes = now.hour * 60 + now.minute
    weekday_key = str(now.isoweekday())

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
    end_minutes = _parse_hhmm_to_minutes(values_locale.get("WORK_HOURS_END", "18:00"))
    if start_minutes is None or end_minutes is None:
        return True
    return start_minutes <= current_minutes < end_minutes


def build_legal_document_view_model(
    legal_doc: dict,
    current_lang: str,
    home_href: str,
) -> dict:
    legal_locale = localized_content_block(legal_doc, current_lang)
    blocks: list[dict[str, str]] = []
    for block in legal_locale.get("blocks", []):
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type", "p"))
        text = str(block.get("text", "")).replace("{{HOME_HREF}}", home_href)
        tag = "h1" if block_type == "h1" else "h2" if block_type == "h2" else "p"
        blocks.append({"tag": tag, "html": sanitize_legal_html(text)})
    return {
        "title": str(legal_locale.get("title", "")),
        "updatedAtText": str(legal_locale.get("updatedAtText", "")),
        "blocks": blocks,
        "info_banner": legal_locale.get("info_banner", {}),
    }


def build_context(request: Request, site_content: dict, ui_texts: dict) -> dict:
    settings = get_settings()
    current_lang = resolve_current_lang(request, site_content)
    values_locale = load_values_locale(current_lang)

    basic_locale = localized_content_block(site_content.get("basic", {}), current_lang)
    main_locale = main_locale_with_direction_lang(
        localized_content_block(site_content.get("main", {}), current_lang),
        current_lang,
    )
    main_nav_locale = navigation_with_lang_urls(
        basic_locale.get("navigation", {}),
        current_lang,
    )

    social_links: list[dict] = []
    show_phone_link = is_within_working_hours(values_locale)
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
        key: localized_profession_block(site_content.get(key, {}), current_lang)
        for key in PROFESSION_KEYS
    }
    work_places_locale = localized_content_block(
        site_content.get("work_places", {}), current_lang
    )
    profession_work_experience = {
        key: profession_work_experience_items(work_places_locale, key)
        for key in PROFESSION_KEYS
    }
    portfolio_projects_locale = localized_content_block(
        site_content.get("portfolio_projects", {}), current_lang
    )
    developer_bubble_layout = get_developer_portfolio_bubbles_layout()
    bubble_animation = developer_bubble_layout.get("animation", {})
    if not isinstance(bubble_animation, dict):
        bubble_animation = {}
    projects_assets_dir = settings.static_dir / "assets" / "projects"
    profession_portfolio_projects = {
        key: profession_portfolio_items(
            portfolio_projects_locale,
            key,
            projects_assets_dir,
            settings.static_dir,
            portfolio_mode="cards",
        )
        for key in PROFESSION_KEYS
    }
    profession_portfolio_bubbles = {
        key: profession_portfolio_items(
            portfolio_projects_locale,
            key,
            projects_assets_dir,
            settings.static_dir,
            developer_bubble_layout,
            portfolio_mode="bubbles",
        )
        for key in PROFESSION_KEYS
    }
    education_locale = localized_content_block(
        site_content.get("education", {}), current_lang
    )
    profession_education = {
        key: profession_education_items(education_locale, key)
        for key in PROFESSION_KEYS
    }

    links = basic_locale.get("links", {})
    agreement_path = str(
        links.get("userAgreement", {}).get("href", "/polzovatelskoe-soglashenie")
    )
    privacy_path = str(
        links.get("privacyPolicy", {}).get("href", "/politika-konfidencialnosti")
    )
    user_agreement_href = append_lang_query(agreement_path, current_lang)
    privacy_policy_href = append_lang_query(privacy_path, current_lang)

    feedback_form = basic_locale.get("feedback", {}).get("form", {})
    consent_text = str(feedback_form.get("consentText", ""))
    consent_privacy_phrase = str(feedback_form.get("consentPrivacyLinkText", ""))
    feedback_consent_html = build_feedback_consent_html(
        consent_text,
        consent_privacy_phrase,
        privacy_policy_href,
    )

    full_name = (
        f"{basic_locale.get('firstName', '')} {basic_locale.get('lastName', '')}"
    ).strip()
    agreement_phrase = str(links.get("userAgreement", {}).get("footerLabel", ""))
    hero_bottom_legal_html = build_hero_bottom_legal_html(
        str(basic_locale.get("hero_bottom_legal", "")),
        full_name,
        append_lang_query("/main", current_lang),
        agreement_phrase,
        user_agreement_href,
    )

    github_href = (
        str(values_locale.get("GITHUB_URL", "")).strip()
        or str(settings.github_url or "").strip()
    )
    bubble_footer = portfolio_projects_locale.get("bubbleFooter", {})
    bubble_footer_github_html = ""
    if isinstance(bubble_footer, dict):
        bubble_footer_github_html = build_bubble_footer_github_html(
            str(bubble_footer.get("githubLineBefore", "")),
            str(bubble_footer.get("githubLinkLabel", "")),
            github_href,
        )

    return {
        "request": request,
        "content": site_content,
        "ui": ui_texts,
        "current_lang": current_lang,
        "github_href": github_href,
        "bubble_footer_github_html": bubble_footer_github_html,
        "basic_locale": basic_locale,
        "main_locale": main_locale,
        "main_nav_locale": main_nav_locale,
        "social_links": social_links,
        "work_hours_refresh": {
            "timezone": str(values_locale.get("WORK_TIMEZONE", "UTC")),
            "schedule": values_locale.get("WORK_SCHEDULE"),
            "work_days": str(values_locale.get("WORK_DAYS", "1,2,3,4,5")),
            "work_hours_start": str(values_locale.get("WORK_HOURS_START", "09:00")),
            "work_hours_end": str(values_locale.get("WORK_HOURS_END", "18:00")),
            "is_within_working_hours": show_phone_link,
        },
        "turnstile_site_key": settings.feedback_turnstile_site_key,
        "profession_locale": profession_locale,
        "work_places_locale": work_places_locale,
        "profession_work_experience": profession_work_experience,
        "portfolio_projects_locale": portfolio_projects_locale,
        "profession_portfolio_projects": profession_portfolio_projects,
        "profession_portfolio_bubbles": profession_portfolio_bubbles,
        "developer_bubble_animation": bubble_animation,
        "education_locale": education_locale,
        "profession_education": profession_education,
        "home_href": append_lang_query("/main", current_lang),
        "user_agreement_href": user_agreement_href,
        "privacy_policy_href": privacy_policy_href,
        "feedback_consent_html": feedback_consent_html,
        "hero_bottom_legal_html": hero_bottom_legal_html,
    }


def build_legal_page_context(
    request: Request,
    site_content: dict,
    ui_texts: dict,
    content_key: str,
) -> dict:
    context = build_context(request, site_content, ui_texts)
    legal_doc = site_content.get(content_key, {})
    if not isinstance(legal_doc, dict):
        legal_doc = {}
    legal_document = build_legal_document_view_model(
        legal_doc,
        context["current_lang"],
        context["home_href"],
    )
    context["legal_document"] = legal_document
    context["page_title"] = legal_document["title"]
    return context
