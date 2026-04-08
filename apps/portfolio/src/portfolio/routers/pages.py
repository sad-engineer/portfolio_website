"""Обработчики основных страниц сайта."""

from copy import deepcopy

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from portfolio.dependencies import (get_site_content, get_templates,
                                    get_ui_texts)

router = APIRouter(tags=["pages"])


def _deep_merge_dicts(base: dict, overlay: dict) -> dict:
    merged = deepcopy(base)
    for key, value in overlay.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
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


def _resolve_current_lang(request: Request, site_content: dict) -> str:
    supported_locales = (
        site_content.get("basic", {}).get("site", {}).get("locales", ["ru", "en"])
    )
    default_locale = site_content.get("basic", {}).get("site", {}).get("language", "ru")

    requested_locale = request.query_params.get("lang", default_locale)
    if requested_locale in supported_locales:
        return requested_locale
    return default_locale


def _build_context(request: Request, site_content: dict, ui_texts: dict) -> dict:
    current_lang = _resolve_current_lang(request, site_content)

    basic_locale = _localized_content_block(site_content.get("basic", {}), current_lang)
    main_locale = _localized_content_block(site_content.get("main", {}), current_lang)
    main_nav_locale = basic_locale.get("navigation", {})

    social_links: list[dict] = []
    for item in main_locale.get("social", []):
        icon = str(item.get("icon", ""))
        icon_lc = icon.lower()
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
                "url": item.get("url", ""),
                "is_asset_icon": is_asset_icon,
            }
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
