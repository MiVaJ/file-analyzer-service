from uuid import UUID

from fastapi.testclient import TestClient

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


def test_get_download_progress_returns_progress() -> None:
    """Проверяет получение прогресса скачивания."""

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
