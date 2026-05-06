"""Точка входа FastAPI-приложения портфолио."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from portfolio.dependencies import get_settings
from portfolio.routers import feedback_router, pages_router
from portfolio.routers.pages import LANG_COOKIE_NAME
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


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

    supported_lang_cookie = frozenset({"ru", "en"})

    class _LocaleCookieMiddleware(BaseHTTPMiddleware):
        """Записывает выбранную локаль в cookie при ?lang=… для последующих переходов без параметра."""

        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            lang = request.query_params.get("lang")
            if lang in supported_lang_cookie:
                response.set_cookie(
                    key=LANG_COOKIE_NAME,
                    value=lang,
                    max_age=365 * 24 * 60 * 60,
                    path="/",
                    httponly=False,
                    samesite="lax",
                )
            return response

    my_app.add_middleware(_LocaleCookieMiddleware)

    my_app.mount(
        "/static",
        StaticFiles(directory=str(settings.static_dir)),
        name="static",
    )

    my_app.include_router(pages_router)
    my_app.include_router(feedback_router)

    return my_app


app = create_app()
