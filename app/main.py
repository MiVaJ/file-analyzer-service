from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.download import router as download_router
from app.api.files import router as files_router
from app.api.pages import router as pages_router
from app.core.config import settings
from app.core.redis import close_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()

    try:
        yield

    finally:
        await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Downloads a remote catalog of text files via a rate-limited API "
            "and computes digit-frequency statistics."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.mount(
        "/static",
        StaticFiles(directory="app/static"),
        name="static",
    )

    app.include_router(
        download_router,
    )

    app.include_router(
        pages_router,
    )

    app.include_router(
        files_router,
    )

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
