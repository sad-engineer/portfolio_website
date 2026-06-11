"""Обработчики основных страниц сайта."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from portfolio.dependencies import get_site_content, get_templates, get_ui_texts
from portfolio.services.page_context import (
    build_context,
    build_legal_page_context,
    load_robots_txt,
)

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Главная страница портфолио."""
    return templates.TemplateResponse(
        "main.html", build_context(request, site_content, ui_texts)
    )


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt() -> PlainTextResponse:
    """Файл robots.txt для поисковых роботов."""
    return PlainTextResponse(load_robots_txt(), media_type="text/plain")


@router.get("/main", response_class=HTMLResponse)
async def main_page(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Главная страница портфолио."""
    return templates.TemplateResponse(
        "main.html", build_context(request, site_content, ui_texts)
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
        "constructor.html", build_context(request, site_content, ui_texts)
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
        "planner.html", build_context(request, site_content, ui_texts)
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
        "developer.html", build_context(request, site_content, ui_texts)
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
        "technologist.html", build_context(request, site_content, ui_texts)
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
        build_legal_page_context(request, site_content, ui_texts, "agreement"),
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
        build_legal_page_context(request, site_content, ui_texts, "privacy"),
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
        "work_places.html", build_context(request, site_content, ui_texts)
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
        "education.html", build_context(request, site_content, ui_texts)
    )
