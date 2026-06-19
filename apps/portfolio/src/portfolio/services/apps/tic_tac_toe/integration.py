"""Интеграция PET tic_tac_toe в портфолио."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from portfolio.config import Settings

_APP_SLUG = "tic_tac_toe"
_IMPORTED = False


def ensure_importable(root: Path) -> None:
    global _IMPORTED
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    _IMPORTED = True


def mount_routes(app: FastAPI, settings: Settings, entry: dict[str, str]) -> None:
    root = settings.apps_dir / _APP_SLUG
    if not root.is_dir():
        return

    ensure_importable(root)
    from routers.game_api import router as api_router

    api_prefix = str(entry.get("api_prefix", "")).strip()
    if api_prefix:
        app.include_router(
            api_router,
            prefix=api_prefix,
            tags=["pet-tic-tac-toe"],
        )

    static_prefix = str(entry.get("static_prefix", "")).strip()
    static_dir = root / "app" / "frontend" / "static"
    if static_prefix and static_dir.is_dir():
        app.mount(
            static_prefix,
            StaticFiles(directory=str(static_dir)),
            name="pet_tic_tac_toe_static",
        )


def build_embed_context(
    project_id: str,
    current_lang: str,
    settings: Settings,
    entry: dict[str, str],
) -> dict[str, Any]:
    root = settings.apps_dir / _APP_SLUG
    if not root.is_dir():
        return {}

    ensure_importable(root)
    from services.content import localized_ui, normalize_locale

    locale = normalize_locale(current_lang)
    api_prefix = str(entry.get("api_prefix", "")).rstrip("/")
    static_prefix = str(entry.get("static_prefix", "")).rstrip("/")
    client_config = {
        "apiBaseUrl": api_prefix,
        "staticBaseUrl": static_prefix,
        "locale": locale,
        "localeControl": "external",
        "showLocaleSelector": False,
    }

    return {
        "pet_project_id": project_id,
        "pet_app_slug": _APP_SLUG,
        "pet_demo_partial": str(entry.get("pet_template_partial", "")),
        "portfolio_template": str(entry.get("portfolio_template", "")).strip(),
        "pet_portfolio_css": str(entry.get("portfolio_css", "")).strip(),
        "pet_static_base": static_prefix,
        "ui": localized_ui(locale),
        "locale_control": "external",
        "show_locale_selector": False,
        "api_base_url": api_prefix,
        "static_base_url": static_prefix,
        "current_lang": locale,
        "client_config_json": json.dumps(client_config, ensure_ascii=False),
    }
