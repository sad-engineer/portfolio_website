"""Маршрутизаторы приложения."""

from .feedback import router as feedback_router
from .pages import router as pages_router

__all__ = ["pages_router", "feedback_router"]
