from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(
    tags=["Страницы"],
)

templates = Jinja2Templates(
    directory="app/templates",
)


@router.get(
    "/",
    summary="Страница скачивания файлов",
    description=(
        "Отображает страницу запуска скачивания каталога файлов. "
        "Позволяет запустить процесс загрузки и отслеживать его прогресс."
    ),
)
async def download_page(
    request: Request,
):
    """Отображает страницу скачивания файлов."""

    return templates.TemplateResponse(
        name="download.html",
        request=request,
        context={
            "request": request,
        },
    )
