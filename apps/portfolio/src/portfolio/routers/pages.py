"""Обработчики основных страниц сайта."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from portfolio.dependencies import (
    get_site_content,
    get_templates,
    get_ui_texts,
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

    context = {"request": request, "content": site_content, "ui": ui_texts}
    return templates.TemplateResponse("index.html", context)
