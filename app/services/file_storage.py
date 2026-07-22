from pathlib import Path

from app.services.source_api_client import DownloadedFilePayload


class FileStorage:
    """Сервис сохранения файлов на диск."""

    def __init__(
        self,
        directory: str,
    ) -> None:
        self._directory = Path(directory)

        self._directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        file: DownloadedFilePayload,
    ) -> str:
        """Сохраняет файл и возвращает путь."""

        file_path = self._directory / file.filename

        file_path.write_text(
            file.content,
            encoding="utf-8",
        )

        return str(file_path)
