from uuid import UUID

from fastapi.testclient import TestClient

from app.core.redis import get_redis
from app.main import app

client = TestClient(app)


def test_start_download_returns_download_id(
    mocker,
) -> None:
    """Проверяет запуск скачивания и создание идентификатора."""

    mocker.patch(
        "app.api.download.download_catalog.delay",
    )

    response = client.post(
        "/api/download/start",
    )

    assert response.status_code == 200

    data = response.json()

    assert "download_id" in data
    assert data["status"] == "started"

    UUID(data["download_id"])


def test_get_download_progress_returns_progress(
    mocker,
) -> None:
    """Проверяет получение прогресса скачивания."""

    mock_redis = mocker.AsyncMock()

    app.dependency_overrides[get_redis] = lambda: mock_redis

    mock_redis.get.return_value = b"""
        {
            "status": "running",
            "received_names": 0,
            "downloaded": 0,
            "failed": 0,
            "started_at": "2026-07-23T12:00:00"
        }
        """

    response = client.get(
        "/api/download/progress/download-1",
    )

    assert response.status_code == 200

    data = response.json()

    assert "progress" in data

    assert data["progress"]["status"] == "running"
    assert data["progress"]["received_names"] == 0
    assert data["progress"]["downloaded"] == 0
    assert data["progress"]["failed"] == 0

    app.dependency_overrides.clear()
