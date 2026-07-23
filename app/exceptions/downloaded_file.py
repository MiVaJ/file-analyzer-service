class DownloadedFilesNotFoundError(Exception):
    """Некоторые скачанные файлы не найдены."""

    def __init__(
        self,
        file_ids: list[int],
    ) -> None:
        self.file_ids = file_ids

        super().__init__(
            f"Files not found: {file_ids}",
        )
