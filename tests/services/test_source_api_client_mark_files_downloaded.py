import httpx
import pytest
import respx

from app.services.source_api_client import (
    SourceApiBlockedError,
    SourceApiClient,
    SourceApiRateLimitError,
    SourceApiValidationError,
)

BASE_URL = "http://source-api.test"


@pytest.mark.asyncio
@respx.mock
async def test_mark_files_downloaded_returns_result() -> None:
    """Проверяет успешную отметку файлов как скачанных."""

    route = respx.post(
        f"{BASE_URL}/api/files/downloaded",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "marked_now": 2,
                "already_marked": 1,
            },
        ),
    )

    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
    )

    result = await client.mark_files_downloaded(
        [
            "a.txt",
            "b.txt",
        ]
    )

    assert route.called
    assert result.marked_now == 2
    assert result.already_marked == 1


@pytest.mark.asyncio
async def test_mark_files_downloaded_empty_list_returns_empty_result() -> None:
    """Проверяет возврат пустого результата без обращения к API."""

    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
    )

    with respx.mock:
        result = await client.mark_files_downloaded([])

    assert result.marked_now == 0
    assert result.already_marked == 0


@pytest.mark.asyncio
@respx.mock
async def test_mark_files_downloaded_403_raises_blocked_error() -> None:
    """Проверяет обработку временной блокировки клиента."""

    respx.post(
        f"{BASE_URL}/api/files/downloaded",
    ).mock(
        return_value=httpx.Response(403),
    )

    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
    )

    with pytest.raises(SourceApiBlockedError):
        await client.mark_files_downloaded(["a.txt"])


@pytest.mark.asyncio
@respx.mock
async def test_mark_files_downloaded_422_raises_validation_error() -> None:
    """Проверяет обработку ошибки валидации запроса."""

    respx.post(
        f"{BASE_URL}/api/files/downloaded",
    ).mock(
        return_value=httpx.Response(422),
    )

    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
    )

    with pytest.raises(SourceApiValidationError):
        await client.mark_files_downloaded(["a.txt"])


@pytest.mark.asyncio
@respx.mock
async def test_mark_files_downloaded_429_retries_then_succeeds(
    mocker,
) -> None:
    """Проверяет повторный запрос после получения ответа 429."""

    route = respx.post(
        f"{BASE_URL}/api/files/downloaded",
    ).mock(
        side_effect=[
            httpx.Response(
                429,
                headers={
                    "Retry-After": "1",
                },
            ),
            httpx.Response(
                200,
                json={
                    "marked_now": 1,
                    "already_marked": 0,
                },
            ),
        ],
    )

    mocker.patch("asyncio.sleep")

    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
        max_retries=3,
    )

    result = await client.mark_files_downloaded(
        ["a.txt"],
    )

    assert route.call_count == 2
    assert result.marked_now == 1


@pytest.mark.asyncio
@respx.mock
async def test_mark_files_downloaded_429_exceeds_retries_raises_rate_limit_error(
    mocker,
) -> None:
    """Проверяет ошибку после исчерпания попыток повторного запроса."""

    respx.post(
        f"{BASE_URL}/api/files/downloaded",
    ).mock(
        return_value=httpx.Response(
            429,
            headers={
                "Retry-After": "1",
            },
        ),
    )

    mocker.patch("asyncio.sleep")

    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
        max_retries=2,
    )

    with pytest.raises(SourceApiRateLimitError):
        await client.mark_files_downloaded(["a.txt"])


@pytest.mark.asyncio
@respx.mock
async def test_mark_files_downloaded_other_http_error_propagates() -> None:
    """Проверяет проброс необработанных HTTP-ошибок."""

    respx.post(
        f"{BASE_URL}/api/files/downloaded",
    ).mock(
        return_value=httpx.Response(500),
    )

    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
    )

    with pytest.raises(httpx.HTTPStatusError):
        await client.mark_files_downloaded(["a.txt"])
