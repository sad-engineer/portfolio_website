"""Реестр PET-проектов и диспетчеризация интеграции по app_slug."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import FastAPI
from portfolio.config import Settings
from portfolio.services.apps.tic_tac_toe import integration as tic_tac_toe_integration

PET_DEMO_REGISTRY: dict[str, dict[str, str]] = {
    "308": {
        "app_slug": "tic_tac_toe",
        "api_prefix": "/api/projects/tic-tac-toe",
        "static_prefix": "/static/projects/tic-tac-toe",
        "pet_template_partial": "partials/game_demo.html",
        "portfolio_template": "apps/tic_tac_toe/embed.html",
        "portfolio_css": "css/components/apps/tic_tac_toe/embed.css",
    },
}

_EMBED_BUILDERS: dict[str, Callable[..., dict[str, Any]]] = {
    "tic_tac_toe": tic_tac_toe_integration.build_embed_context,
}

_ROUTE_MOUNTS: dict[str, Callable[[FastAPI, Settings, dict[str, str]], None]] = {
    "tic_tac_toe": tic_tac_toe_integration.mount_routes,
}


def resolve_pet_demo(project_id: str) -> Optional[dict[str, str]]:
    entry = PET_DEMO_REGISTRY.get(str(project_id).strip())
    if not isinstance(entry, dict):
        return None
    return entry


def project_page_url(project_id: str) -> str:
    return f"/projects/{str(project_id).strip()}"


def pet_app_root(settings: Settings, app_slug: str) -> Path:
    return settings.apps_dir / app_slug


def mount_pet_routes(app: FastAPI, settings: Settings) -> None:
    mounted_slugs: set[str] = set()
    for entry in PET_DEMO_REGISTRY.values():
        app_slug = str(entry.get("app_slug", "")).strip()
        if not app_slug or app_slug in mounted_slugs:
            continue
        mount_handler = _ROUTE_MOUNTS.get(app_slug)
        if mount_handler and pet_app_root(settings, app_slug).is_dir():
            mount_handler(app, settings, entry)
        mounted_slugs.add(app_slug)


def build_pet_embed_context(
    project_id: str,
    current_lang: str,
    settings: Settings,
) -> dict[str, Any]:
    entry = resolve_pet_demo(project_id)
    if not entry:
        return {}

    app_slug = str(entry.get("app_slug", "")).strip()
    builder = _EMBED_BUILDERS.get(app_slug)
    if not builder or not pet_app_root(settings, app_slug).is_dir():
        return {}

    return builder(project_id, current_lang, settings, entry)


def pet_template_dirs(settings: Settings) -> list[Path]:
    dirs: list[Path] = []
    seen: set[str] = set()
    for entry in PET_DEMO_REGISTRY.values():
        app_slug = str(entry.get("app_slug", "")).strip()
        if not app_slug or app_slug in seen:
            continue
        templates_dir = pet_app_root(settings, app_slug) / "app" / "frontend" / "templates"
        if templates_dir.is_dir():
            dirs.append(templates_dir)
        seen.add(app_slug)
    return dirs
