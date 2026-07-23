from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.downloaded_file import DownloadedFile

client = TestClient(app)


@pytest.mark.asyncio
async def test_compute_statistics(
    tmp_path: Path,
) -> None:
    """Проверяет расчёт статистики через API."""

    file = tmp_path / "test.txt"
    file.write_text(
        "001122",
        encoding="utf-8",
    )

    downloaded_file = DownloadedFile(
        id=1,
        filename="test.txt",
        path=str(file),
        downloaded_at=datetime.now(),
    )

    with patch(
        "app.api.stats.DownloadedFileService.get_by_ids",
        new_callable=AsyncMock,
        return_value=[downloaded_file],
    ):
        response = client.post(
            "/api/stats/compute",
            json={
                "file_ids": [1],
            },
        )

    assert response.status_code == 200

    assert response.json()["total"]["0"] == 2
    assert response.json()["total"]["1"] == 2
    assert response.json()["total"]["2"] == 2
