import asyncio

import httpx


class SourceApiError(Exception):
    """Базовое исключение клиента внешнего API."""


class SourceApiRateLimitError(SourceApiError):
    """Ошибка превышения ограничения количества запросов."""


class SourceApiBlockedError(SourceApiError):
    """Клиент временно заблокирован внешним API."""


class SourceApiValidationError(SourceApiError):
    """Ошибка валидации запроса внешним API."""


class SourceApiClient:
    """Клиент для получения данных из File Catalog API."""

    def __init__(
        self,
        base_url: str,
        files_path: str = "/api/files/names",
        timeout: float = 5.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.files_path = files_path
        self.timeout = timeout
        self.max_retries = max_retries

    async def get_file_names(self) -> list[str]:
        """Получение списка файлов из внешнего API."""

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            for attempt in range(self.max_retries + 1):
                response = await client.get(
                    f"{self.base_url}{self.files_path}",
                )

                if response.status_code == 403:
                    raise SourceApiBlockedError(
                        "Клиент временно заблокирован внешним API"
                    )

                if response.status_code == 429:
                    await self._handle_rate_limit(
                        response,
                        attempt,
                    )
                    continue

                if response.status_code == 422:
                    raise SourceApiValidationError(
                        "Ошибка валидации запроса внешним API"
                    )

                response.raise_for_status()

                data = response.json()

                return data["file_names"]

            raise SourceApiRateLimitError(
                "Превышено максимальное количество попыток запросов"
            )

    async def _handle_rate_limit(
        self,
        response: httpx.Response,
        attempt: int,
    ) -> None:
        """Обработка превышения лимита запросов API."""

        if attempt >= self.max_retries:
            raise SourceApiRateLimitError("Превышен лимит запросов")

        retry_after = response.headers.get("Retry-After")

        if retry_after:
            delay = int(retry_after)
        else:
            delay = 2**attempt

        await asyncio.sleep(delay)
