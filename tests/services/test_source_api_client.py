import httpx
import pytest

from app.services.source_api_client import (
    SourceApiBlockedError,
    SourceApiClient,
    SourceApiRateLimitError,
    SourceApiValidationError,
)


@pytest.mark.asyncio
async def test_get_files_success(
    monkeypatch,
):
    """Проверяет успешное получение списка файлов из API."""

    async def mock_get(
        self,
        url,
    ):
        return httpx.Response(
            status_code=200,
            json={"file_names": ["000d7d0a-acef-4c95-b92d-1aa496b1858a.txt"]},
            request=httpx.Request(
                "GET",
                url,
            ),
        )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    client = SourceApiClient(
        base_url="http://test",
    )

    result = await client.get_file_names()

    assert result == ["000d7d0a-acef-4c95-b92d-1aa496b1858a.txt"]


@pytest.mark.asyncio
async def test_get_files_retries_after_rate_limit(
    monkeypatch,
):
    """Проверяет повторный запрос после получения ответа с кодом 429."""
    calls = 0

    async def mock_get(
        self,
        url,
    ):
        nonlocal calls

        calls += 1

        if calls == 1:
            return httpx.Response(
                status_code=429,
                headers={"Retry-After": "0"},
            )

        return httpx.Response(
            status_code=200,
            json={"file_names": []},
            request=httpx.Request(
                "GET",
                url,
            ),
        )

    async def mock_sleep(delay):
        return None

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    monkeypatch.setattr(
        "asyncio.sleep",
        mock_sleep,
    )

    client = SourceApiClient(
        base_url="http://test",
        max_retries=1,
    )

    result = await client.get_file_names()

    assert result == []
    assert calls == 2


@pytest.mark.asyncio
async def test_get_files_raises_error_after_retry_limit(
    monkeypatch,
):
    """Проверяет ошибку при превышении допустимого количества повторных запросов."""

    async def mock_get(
        self,
        url,
    ):
        return httpx.Response(
            status_code=429,
        )

    async def mock_sleep(delay):
        return None

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    monkeypatch.setattr(
        "asyncio.sleep",
        mock_sleep,
    )

    client = SourceApiClient(
        base_url="http://test",
        max_retries=0,
    )

    with pytest.raises(SourceApiRateLimitError):
        await client.get_file_names()


@pytest.mark.asyncio
async def test_get_file_names_raises_error_when_client_blocked(
    monkeypatch,
):
    """Проверяет ошибку при временной блокировке клиента внешним API."""

    async def mock_get(
        _self,
        _url,
    ):
        return httpx.Response(
            status_code=403,
        )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    client = SourceApiClient(
        base_url="http://test",
    )

    with pytest.raises(SourceApiBlockedError):
        await client.get_file_names()


@pytest.mark.asyncio
async def test_get_file_names_raises_error_on_validation_failure(
    monkeypatch,
):
    """Проверяет ошибку при отклонении запроса внешним API."""

    async def mock_get(
        _self,
        _url,
    ):
        return httpx.Response(
            status_code=422,
            json={"detail": "Validation Error"},
        )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    client = SourceApiClient(
        base_url="http://test",
    )

    with pytest.raises(SourceApiValidationError):
        await client.get_file_names()
