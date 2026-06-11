"""Прикладные сервисы портфолио (Application Layer)."""

from portfolio.services.page_context import (
    LANG_COOKIE_NAME,
    build_context,
    build_legal_page_context,
)

__all__ = [
    "LANG_COOKIE_NAME",
    "build_context",
    "build_legal_page_context",
]
