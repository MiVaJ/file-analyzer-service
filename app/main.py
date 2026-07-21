from fastapi import FastAPI

from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Downloads a remote catalog of text files via a rate-limited API "
            "and computes digit-frequency statistics."
        ),
        version="0.1.0",
    )

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
