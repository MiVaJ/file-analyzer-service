from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.services.downloaded_file import DownloadedFileService

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


@router.get(
    "/files",
    summary="Страница скачанных файлов",
    description=(
        "Отображает список скачанных файлов "
        "с возможностью выбрать файлы для расчёта статистики."
    ),
)
async def files_page(
    request: Request,
    page: int = 1,
    limit: int = 10,
    session: AsyncSession = Depends(
        get_db,
    ),
):
    """Отображает страницу скачанных файлов."""

    service = DownloadedFileService(
        session,
    )

    files, total = await service.get_files(
        page,
        limit,
    )

    return templates.TemplateResponse(
        name="files.html",
        request=request,
        context={
            "request": request,
            "files": files,
            "page": page,
            "limit": limit,
            "total": total,
        },
    )
