from datetime import datetime, timezone

from redis.asyncio import Redis

from app.schemas.download_progress import DownloadProgress

PROGRESS_KEY_PREFIX = "download:progress:"
PROGRESS_TTL_SECONDS = 86400


class DownloadProgressTracker:
    """Сервис хранения прогресса скачивания в Redis."""

    def __init__(
        self,
        redis: Redis,
    ) -> None:
        self._redis = redis

    async def create(
        self,
        download_id: str,
    ) -> DownloadProgress:
        """Создаёт прогресс новой загрузки."""

        progress = DownloadProgress(
            status="running",
            received_names=0,
            downloaded=0,
            failed=0,
            started_at=datetime.now(
                timezone.utc,
            ),
        )

        await self._save_progress(
            download_id,
            progress,
        )

        return progress

    async def get(
        self,
        download_id: str,
    ) -> DownloadProgress | None:
        """Получает текущий прогресс загрузки."""

        value = await self._redis.get(
            self._get_key(download_id),
        )

        if value is None:
            return None

        return DownloadProgress.model_validate_json(
            value,
        )

    async def add_received_names(
        self,
        download_id: str,
        amount: int,
    ) -> None:
        """Увеличивает количество полученных имён файлов."""

        progress = await self.get(
            download_id,
        )

        if progress is None:
            return

        updated_progress = progress.model_copy(
            update={
                "received_names": (progress.received_names + amount),
            },
        )

        await self._save_progress(
            download_id,
            updated_progress,
        )

    async def increment_downloaded(
        self,
        download_id: str,
        amount: int = 1,
    ) -> None:
        """Увеличивает количество скачанных файлов."""

        progress = await self.get(
            download_id,
        )

        if progress is None:
            return

        updated_progress = progress.model_copy(
            update={
                "downloaded": (progress.downloaded + amount),
            },
        )

        await self._save_progress(
            download_id,
            updated_progress,
        )

    async def increment_failed(
        self,
        download_id: str,
        amount: int = 1,
    ) -> None:
        """Увеличивает количество файлов с ошибками."""

        progress = await self.get(
            download_id,
        )

        if progress is None:
            return

        updated_progress = progress.model_copy(
            update={
                "failed": (progress.failed + amount),
            },
        )

        await self._save_progress(
            download_id,
            updated_progress,
        )

    async def mark_finished(
        self,
        download_id: str,
    ) -> None:
        """Помечает загрузку как завершённую."""

        progress = await self.get(
            download_id,
        )

        if progress is None:
            return

        updated_progress = progress.model_copy(
            update={
                "status": "finished",
            },
        )

        await self._save_progress(
            download_id,
            updated_progress,
        )

    async def _save_progress(
        self,
        download_id: str,
        progress: DownloadProgress,
    ) -> None:
        """Сохраняет прогресс в Redis."""

        await self._redis.set(
            self._get_key(download_id),
            progress.model_dump_json(),
            ex=PROGRESS_TTL_SECONDS,
        )

    @staticmethod
    def _get_key(
        download_id: str,
    ) -> str:
        """Формирует ключ Redis для загрузки."""

        return f"{PROGRESS_KEY_PREFIX}{download_id}"
