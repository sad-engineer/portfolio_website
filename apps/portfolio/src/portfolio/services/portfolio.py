"""Обогащение проектов портфолио путями к ассетам и layout пузырьков."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Optional

from portfolio.services.apps.registry import project_page_url, resolve_pet_demo

_DOCUMENT_DRAWING_PROFILES = frozenset({"planner-drawing", "technologist-drawing"})
_DEVELOPER_BUBBLE_PROFILE = "developer-bubble"
_STANDARD_PROFILE = "standard"
_DEFAULT_PREVIEW_REL = "PNG/preview.png"
_PDF_DIR = "PDF"


def static_relative_path(static_dir: Path, asset_path: Path) -> str:
    return str(asset_path.relative_to(static_dir)).replace("\\", "/")


def normalize_asset_profile(raw_profile: object) -> str:
    profile = str(raw_profile or "").strip()
    return profile or _STANDARD_PROFILE


def preview_relative_path(item: dict) -> str:
    preview = str(item.get("preview", "")).strip()
    return preview or _DEFAULT_PREVIEW_REL


def resolve_project_preview(
    projects_dir: Path, static_dir: Path, asset_folder: str, preview_rel: str
) -> Optional[str]:
    preview_file = projects_dir / asset_folder / Path(preview_rel.replace("\\", "/"))
    if not preview_file.is_file():
        return None
    return static_relative_path(static_dir, preview_file)


def resolve_document_drawing_pdf(
    projects_dir: Path, static_dir: Path, asset_folder: str
) -> Optional[str]:
    pdf_dir = projects_dir / asset_folder / _PDF_DIR
    if not pdf_dir.is_dir():
        return None
    pdf_files = sorted(pdf_dir.glob("*.pdf"), key=lambda path: path.name.lower())
    if not pdf_files:
        return None
    return static_relative_path(static_dir, pdf_files[0])


def bubble_layout_entry(item_id: str, bubble_layout: dict) -> Optional[dict]:
    bubbles = bubble_layout.get("bubbles", {})
    if not isinstance(bubbles, dict):
        return None

    raw_entry = bubbles.get(str(item_id).strip())
    if not isinstance(raw_entry, dict):
        return None

    try:
        entry = {
            "bubbleX": float(raw_entry["x"]),
            "bubbleY": float(raw_entry["y"]),
            "bubbleDiameter": float(raw_entry["diameter"]),
        }
        grow_speed = raw_entry.get("growSpeed")
        if grow_speed is not None:
            entry["bubbleGrowSpeed"] = max(0.01, min(1.0, float(grow_speed)))
        return entry
    except (KeyError, TypeError, ValueError):
        return None


def enrich_portfolio_item(
    item: dict,
    projects_dir: Path,
    static_dir: Path,
    bubble_layout: Optional[dict] = None,
) -> dict:
    enriched = deepcopy(item)
    asset_folder = str(item.get("assetFolder", "")).strip()
    if not asset_folder or not (projects_dir / asset_folder).is_dir():
        return enriched

    asset_profile = normalize_asset_profile(item.get("assetProfile"))
    preview_path = resolve_project_preview(
        projects_dir, static_dir, asset_folder, preview_relative_path(item)
    )
    if preview_path:
        enriched["previewPath"] = preview_path

    if asset_profile in _DOCUMENT_DRAWING_PROFILES | {_DEVELOPER_BUBBLE_PROFILE}:
        document_path = resolve_document_drawing_pdf(
            projects_dir, static_dir, asset_folder
        )
        if document_path:
            enriched["documentPath"] = document_path

    if asset_profile == _DEVELOPER_BUBBLE_PROFILE:
        layout = bubble_layout if isinstance(bubble_layout, dict) else {}
        layout_entry = bubble_layout_entry(str(item.get("id", "")).strip(), layout)
        if layout_entry:
            enriched.update(layout_entry)
        project_id = str(item.get("id", "")).strip()
        if resolve_pet_demo(project_id):
            enriched["pageUrl"] = project_page_url(project_id)

    return enriched


def profession_portfolio_items(
    portfolio_locale: dict,
    profession_key: str,
    projects_dir: Path,
    static_dir: Path,
    bubble_layout: Optional[dict] = None,
    *,
    portfolio_mode: str = "cards",
) -> list[dict]:
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

        asset_profile = normalize_asset_profile(item.get("assetProfile"))
        is_bubble = asset_profile == _DEVELOPER_BUBBLE_PROFILE
        if portfolio_mode == "cards" and is_bubble:
            continue
        if portfolio_mode == "bubbles" and not is_bubble:
            continue

        enriched = enrich_portfolio_item(
            item, projects_dir, static_dir, bubble_layout=bubble_layout
        )
        asset_folder = str(item.get("assetFolder", "")).strip()
        if not asset_folder or not (projects_dir / asset_folder).is_dir():
            continue

        if is_bubble:
            if not enriched.get("bubbleDiameter") or "bubbleX" not in enriched:
                continue
            scoped_items.append(enriched)
            continue

        if not enriched.get("previewPath"):
            continue
        scoped_items.append(enriched)

    for index, item in enumerate(scoped_items, start=1):
        item["cardNumber"] = f"{index:02d}"

    return scoped_items
