from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.downloaded_file import DownloadedFile

client = TestClient(app)


def test_get_files_returns_downloaded_files() -> None:
    """Проверяет получение списка скачанных файлов."""

    files = [
        DownloadedFile(
            id=1,
            filename="test.txt",
            path="/tmp/test.txt",
            downloaded_at=datetime.now(
                timezone.utc,
            ),
        ),
    ]

    with patch(
        "app.api.files.DownloadedFileService.get_files",
        new_callable=AsyncMock,
        return_value=(files, 1),
    ):
        response = client.get(
            "/api/files",
        )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["total"] == 1

    assert data["items"][0]["id"] == 1
    assert data["items"][0]["filename"] == "test.txt"


def test_get_files_supports_pagination() -> None:
    """Проверяет передачу параметров пагинации."""

    with patch(
        "app.api.files.DownloadedFileService.get_files",
        new_callable=AsyncMock,
        return_value=([], 25),
    ) as mock_get_files:
        response = client.get(
            "/api/files?page=2&limit=5",
        )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["limit"] == 5
    assert data["total"] == 25

    mock_get_files.assert_awaited_once_with(
        2,
        5,
    )


def test_get_file_ids_returns_ids() -> None:
    """Проверяет получение идентификаторов файлов."""

    with patch(
        "app.api.files.DownloadedFileService.get_all_ids",
        new_callable=AsyncMock,
        return_value=[1, 2, 3],
    ):
        response = client.get(
            "/api/files/ids",
        )

    assert response.status_code == 200

    assert response.json() == {
        "file_ids": [
            1,
            2,
            3,
        ],
    }
