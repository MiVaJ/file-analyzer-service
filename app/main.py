from contextlib import asynccontextmanager

from fastapi import FastAPI

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

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
