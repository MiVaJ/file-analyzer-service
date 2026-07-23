import asyncio
import io
import time
import zipfile
from dataclasses import dataclass

import httpx

MAX_DOWNLOAD_BATCH_SIZE = 3
INITIAL_RETRY_DELAY_SECONDS = 3

MIN_REQUEST_INTERVAL_SECONDS = 0.5
MAX_REQUEST_INTERVAL_SECONDS = 10.0
INTERVAL_INCREASE_FACTOR = 1.5
INTERVAL_DECREASE_STEP_SECONDS = 0.05
SUCCESSES_BEFORE_DECREASE = 5


class SourceApiError(Exception):
    """Базовое исключение клиента внешнего API."""


class SourceApiRateLimitError(SourceApiError):
    """Ошибка превышения ограничения количества запросов."""


class SourceApiBlockedError(SourceApiError):
    """Клиент временно заблокирован внешним API."""


class SourceApiValidationError(SourceApiError):
    """Ошибка валидации запроса внешним API."""


@dataclass
class DownloadedFilePayload:
    """Один файл, распакованный из ZIP-архива."""

    filename: str
    content: str


@dataclass
class MarkDownloadedResult:
    """Результат отметки файлов как скачанных."""

    marked_now: int
    already_marked: int


class SourceApiClient:
    """Клиент для получения данных из File Catalog API."""

    def __init__(
        self,
        base_url: str,
        candidate_id: str,
        files_path: str = "/api/files/names",
        download_path: str = "/api/files/download",
        mark_downloaded_path: str = "/api/files/downloaded",
        timeout: float = 5.0,
        max_retries: int = 3,
    ) -> None:
        self._headers = {
            "X-Candidate-Id": candidate_id,
        }
        self._cooldown_until = 0.0
        self._last_request_time = 0.0

        self._current_interval = MIN_REQUEST_INTERVAL_SECONDS
        self._consecutive_successes = 0

        self.base_url = base_url.rstrip("/")
        self.files_path = files_path
        self.download_path = download_path
        self.mark_downloaded_path = mark_downloaded_path
        self.timeout = timeout
        self.max_retries = max_retries

    async def get_file_names(self) -> list[str]:
        """Получение списка файлов из внешнего API."""

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            for attempt in range(self.max_retries + 1):
                await self._wait_for_cooldown()
                await self._wait_before_request()

                response = await client.get(
                    f"{self.base_url}{self.files_path}",
                    headers=self._headers,
                )

                should_retry = await self._handle_response_errors(
                    response,
                    attempt,
                )

                if should_retry:
                    continue

                response.raise_for_status()
                self._register_success()

                data = response.json()

                return data["file_names"]

            raise SourceApiRateLimitError(
                "Превышено максимальное количество попыток запросов"
            )

    async def download_files(
        self, file_names: list[str]
    ) -> list[DownloadedFilePayload]:
        """Скачивание файлов по именам."""

        if not file_names:
            return []

        if len(file_names) > MAX_DOWNLOAD_BATCH_SIZE:
            raise ValueError(
                f"Нельзя скачать больше {MAX_DOWNLOAD_BATCH_SIZE} файлов за один запрос"
            )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries + 1):
                await self._wait_for_cooldown()
                await self._wait_before_request()

                response = await client.post(
                    f"{self.base_url}{self.download_path}",
                    json={"file_names": file_names},
                    headers=self._headers,
                )

                should_retry = await self._handle_response_errors(
                    response,
                    attempt,
                )

                if should_retry:
                    continue

                response.raise_for_status()
                self._register_success()

                return self._parse_zip_archive(response.content)

            raise SourceApiRateLimitError(
                "Превышено максимальное количество попыток запросов"
            )

    async def mark_files_downloaded(
        self,
        file_names: list[str],
    ) -> MarkDownloadedResult:
        """Отмечает файлы как скачанные во внешнем API."""

        if not file_names:
            return MarkDownloadedResult(
                marked_now=0,
                already_marked=0,
            )

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            for attempt in range(self.max_retries + 1):
                await self._wait_for_cooldown()
                await self._wait_before_request()

                response = await client.post(
                    f"{self.base_url}{self.mark_downloaded_path}",
                    json={
                        "file_names": file_names,
                    },
                    headers=self._headers,
                )

                should_retry = await self._handle_response_errors(
                    response,
                    attempt,
                )

                if should_retry:
                    continue

                response.raise_for_status()
                self._register_success()

                data = response.json()

                return MarkDownloadedResult(
                    marked_now=data["marked_now"],
                    already_marked=data["already_marked"],
                )

        raise SourceApiRateLimitError(
            "Превышено максимальное количество попыток запросов"
        )

    @staticmethod
    def _parse_zip_archive(content: bytes) -> list[DownloadedFilePayload]:
        """Распаковывает ZIP-архив ответа в список файлов с их содержимым."""

        payloads: list[DownloadedFilePayload] = []

        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            for name in archive.namelist():
                file_content = archive.read(name).decode(encoding="utf-8")
                payloads.append(
                    DownloadedFilePayload(filename=name, content=file_content)
                )

        return payloads

    async def _handle_rate_limit(
        self,
        response: httpx.Response,
        attempt: int,
    ) -> None:
        """Обработка превышения лимита запросов API."""
        self._increase_interval()

        if attempt >= self.max_retries:
            raise SourceApiRateLimitError("Превышен лимит запросов")

        retry_after = response.headers.get("Retry-After")

        if retry_after:
            delay = int(retry_after)
        else:
            delay = INITIAL_RETRY_DELAY_SECONDS * (2**attempt)

        self._cooldown_until = time.monotonic() + delay + 5

        await asyncio.sleep(delay)

    async def _handle_response_errors(
        self,
        response: httpx.Response,
        attempt: int,
    ) -> bool:
        """Обрабатывает типовые ошибки ответов внешнего API."""

        if response.status_code == 403:
            raise SourceApiBlockedError("Клиент временно заблокирован внешним API")

        if response.status_code == 429:
            await self._handle_rate_limit(
                response,
                attempt,
            )
            return True

        if response.status_code == 422:
            raise SourceApiValidationError("Ошибка валидации запроса внешним API")

        return False

    async def _wait_for_cooldown(self):
        """Ожидает паузу после ограничения API."""

        delay = self._cooldown_until - time.monotonic()

        if delay > 0:
            await asyncio.sleep(delay)

    async def _wait_before_request(self):
        """Выдерживает текущую адаптивную паузу между запросами."""

        now = time.monotonic()

        delay = self._last_request_time + self._current_interval - now

        if delay > 0:
            await asyncio.sleep(delay)

        self._last_request_time = time.monotonic()

    def _increase_interval(self) -> None:
        """Увеличивает паузу между запросами после 429."""

        self._consecutive_successes = 0
        self._current_interval = min(
            self._current_interval * INTERVAL_INCREASE_FACTOR,
            MAX_REQUEST_INTERVAL_SECONDS,
        )

    def _register_success(self) -> None:
        """Учитывает успешный запрос. После серии успехов слегка ускоряется."""

        self._consecutive_successes += 1

        if self._consecutive_successes >= SUCCESSES_BEFORE_DECREASE:
            self._consecutive_successes = 0
            self._current_interval = max(
                self._current_interval - INTERVAL_DECREASE_STEP_SECONDS,
                MIN_REQUEST_INTERVAL_SECONDS,
            )
