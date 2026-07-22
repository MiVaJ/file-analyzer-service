from redis.asyncio import Redis

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.catalog_downloader import CatalogDownloader
from app.services.download_progress import DownloadProgressTracker
from app.services.downloaded_file import DownloadedFileService
from app.services.file_storage import FileStorage
from app.services.source_api_client import SourceApiClient


@celery_app.task
def download_catalog(download_id: str) -> None:
    """Запускает скачивание полного каталога."""

    import asyncio

    asyncio.run(
        _download_catalog(
            download_id,
        )
    )


async def _download_catalog(
    download_id: str,
) -> None:
    """Скачивает каталог, сохраняет файлы и обновляет прогресс загрузки."""

    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    try:
        tracker = DownloadProgressTracker(
            redis=redis,
        )

        storage = FileStorage(
            settings.download_dir,
        )

        client = SourceApiClient(
            base_url=settings.source_api_url,
        )

        downloader = CatalogDownloader(
            client=client,
        )

        await tracker.create(
            download_id,
        )

        async with AsyncSessionLocal() as session:
            file_service = DownloadedFileService(
                session=session,
            )

            while True:
                files = await downloader.download_next_batch()

                if not files:
                    break

                file_names = [payload.filename for payload in files]

                await tracker.add_received_names(
                    download_id,
                    len(file_names),
                )

                for payload in files:
                    path = storage.save(
                        payload,
                    )

                    await file_service.create(
                        filename=payload.filename,
                        path=str(path),
                    )

                await session.commit()

                await client.mark_files_downloaded(
                    file_names,
                )

                await tracker.increment_downloaded(
                    download_id,
                    len(files),
                )

        await tracker.mark_finished(
            download_id,
        )

    finally:
        await redis.close()
