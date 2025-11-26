"""Точка входа FastAPI-приложения портфолио."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from portfolio.dependencies import get_settings
from portfolio.routers import pages_router


def create_app() -> FastAPI:
    """Создаёт и настраивает экземпляр FastAPI."""

    settings = get_settings()

    my_app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    my_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    my_app.mount(
        "/static",
        StaticFiles(directory=str(settings.static_dir)),
        name="static",
    )

    my_app.include_router(pages_router)

    return my_app


app = create_app()
