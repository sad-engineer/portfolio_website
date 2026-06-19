"""Маршрутизаторы приложения."""

from .apps import pet_projects_router
from .feedback import router as feedback_router
from .pages import router as pages_router

__all__ = ["pages_router", "pet_projects_router", "feedback_router"]
