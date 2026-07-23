import io
import zipfile

import httpx
import pytest
import respx

from app.services.source_api_client import (
    MAX_DOWNLOAD_BATCH_SIZE,
    SourceApiBlockedError,
    SourceApiClient,
    SourceApiRateLimitError,
    SourceApiValidationError,
)

BASE_URL = "http://source-api.test"


def make_zip_bytes(files: dict[str, str]) -> bytes:
    """Создаёт ZIP-архив в памяти для тестов."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for filename, content in files.items():
            archive.writestr(filename, content)
    return buffer.getvalue()


@pytest.mark.asyncio
@respx.mock
async def test_download_files_returns_parsed_content() -> None:
    """Проверяет успешное скачивание и распаковку ZIP-архива."""
    zip_bytes = make_zip_bytes({"a.txt": "111", "b.txt": "222"})
    route = respx.post(f"{BASE_URL}/api/files/download").mock(
        return_value=httpx.Response(200, content=zip_bytes)
    )

    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
    )
    result = await client.download_files(["a.txt", "b.txt"])

    assert route.called
    assert {p.filename: p.content for p in result} == {"a.txt": "111", "b.txt": "222"}


@pytest.mark.asyncio
async def test_download_files_empty_list_returns_empty_without_request() -> None:
    """Проверяет возврат пустого списка без обращения к API."""
    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
    )

    with respx.mock:
        result = await client.download_files([])

    assert result == []


@pytest.mark.asyncio
async def test_download_files_more_than_limit_raises_value_error_without_request() -> (
    None
):
    """Проверяет ошибку при превышении максимального размера батча."""
    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
    )
    filenames = [f"f{i}.txt" for i in range(MAX_DOWNLOAD_BATCH_SIZE + 1)]

    with respx.mock as mock_router:
        with pytest.raises(ValueError, match=str(MAX_DOWNLOAD_BATCH_SIZE)):
            await client.download_files(filenames)

        assert mock_router.calls.call_count == 0


@pytest.mark.asyncio
@respx.mock
async def test_download_files_403_raises_blocked_error() -> None:
    """Проверяет обработку временной блокировки клиента."""
    respx.post(f"{BASE_URL}/api/files/download").mock(return_value=httpx.Response(403))
    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
    )

    with pytest.raises(SourceApiBlockedError):
        await client.download_files(["a.txt"])


@pytest.mark.asyncio
@respx.mock
async def test_download_files_422_raises_validation_error() -> None:
    """Проверяет обработку ошибки валидации запроса."""
    respx.post(f"{BASE_URL}/api/files/download").mock(return_value=httpx.Response(422))
    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
    )

    with pytest.raises(SourceApiValidationError):
        await client.download_files(["a.txt"])


@pytest.mark.asyncio
@respx.mock
async def test_download_files_429_retries_then_succeeds(mocker) -> None:
    """Проверяет повторный запрос после получения ответа 429."""
    zip_bytes = make_zip_bytes({"a.txt": "111"})
    route = respx.post(f"{BASE_URL}/api/files/download").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "1"}),
            httpx.Response(200, content=zip_bytes),
        ]
    )
    mocker.patch("asyncio.sleep")

    client = SourceApiClient(
        base_url=BASE_URL, candidate_id="test-candidate", max_retries=3
    )
    result = await client.download_files(["a.txt"])

    assert route.call_count == 2
    assert result[0].filename == "a.txt"


@pytest.mark.asyncio
@respx.mock
async def test_download_files_429_exceeds_retries_raises_rate_limit_error(
    mocker,
) -> None:
    """Проверяет ошибку после исчерпания попыток повторного запроса."""
    respx.post(f"{BASE_URL}/api/files/download").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "1"})
    )
    mocker.patch("asyncio.sleep")

    client = SourceApiClient(
        base_url=BASE_URL, candidate_id="test-candidate", max_retries=2
    )

    with pytest.raises(SourceApiRateLimitError):
        await client.download_files(["a.txt"])


@pytest.mark.asyncio
@respx.mock
async def test_download_files_other_http_error_propagates() -> None:
    """Проверяет проброс необработанных HTTP-ошибок."""
    respx.post(f"{BASE_URL}/api/files/download").mock(return_value=httpx.Response(500))
    client = SourceApiClient(
        base_url=BASE_URL,
        candidate_id="test-candidate",
    )

    with pytest.raises(httpx.HTTPStatusError):
        await client.download_files(["a.txt"])
