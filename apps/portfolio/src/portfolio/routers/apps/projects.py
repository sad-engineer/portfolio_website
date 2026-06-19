"""Демо-страницы PET-проектов на сайте портфолио."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from portfolio.dependencies import get_settings, get_site_content, get_templates, get_ui_texts
from portfolio.services.apps.registry import build_pet_embed_context, resolve_pet_demo
from portfolio.services.content import localized_content_block
from portfolio.services.page_context import build_context

router = APIRouter(tags=["pet-projects"])


def _portfolio_project_title(site_content: dict, project_id: str, current_lang: str) -> str:
    portfolio_locale = localized_content_block(
        site_content.get("portfolio_projects", {}), current_lang
    )
    for item in portfolio_locale.get("items", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("id", "")).strip() == project_id:
            return str(item.get("title", "")).replace("\n", " ").strip()
    return ""


@router.get("/projects/{project_id}", response_class=HTMLResponse)
async def pet_app_page(
    project_id: str,
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    site_content: dict = Depends(get_site_content),
    ui_texts: dict = Depends(get_ui_texts),
) -> HTMLResponse:
    """Демо-страница PET-проекта в оболочке портфолио."""
    normalized_id = str(project_id).strip()
    if not resolve_pet_demo(normalized_id):
        raise HTTPException(status_code=404, detail="Project not found")

    settings = get_settings()
    context = build_context(request, site_content, ui_texts)
    pet_context = build_pet_embed_context(
        normalized_id, context["current_lang"], settings
    )
    if not pet_context:
        raise HTTPException(status_code=404, detail="Project demo unavailable")

    context.update(pet_context)
    context["page_id"] = "page-pet-project"
    context["page_title"] = _portfolio_project_title(
        site_content, normalized_id, context["current_lang"]
    ) or str(pet_context.get("ui", {}).get("title", "Project"))

    template_name = str(pet_context.get("portfolio_template", "")).strip()
    if not template_name:
        raise HTTPException(status_code=404, detail="Project template not configured")

    return templates.TemplateResponse(template_name, context)
