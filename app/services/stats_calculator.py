from collections import Counter

from app.exceptions.stats import FileStatisticsCalculationError
from app.models.downloaded_file import DownloadedFile


class DigitStatisticsService:
    """Сервис расчёта статистики по цифрам."""

    @staticmethod
    def calculate_file_statistics(
        content: str,
    ) -> dict[str, int]:
        """Подсчитывает количество каждой цифры в содержимом файла."""

        counts = Counter(content)

        return {
            str(digit): counts.get(
                str(digit),
                0,
            )
            for digit in range(10)
        }

    def calculate_statistics(
        self,
        files: list[DownloadedFile],
    ) -> tuple[
        dict[str, int],
        dict[str, dict[str, int]],
    ]:
        """Подсчитывает общую статистику и статистику по каждому файлу."""

        total_counts: Counter[str] = Counter()

        per_file_statistics: dict[
            str,
            dict[str, int],
        ] = {}

        for file in files:
            try:
                with open(
                    file.path,
                    encoding="utf-8",
                ) as source:
                    content = source.read()

            except (OSError, UnicodeDecodeError) as exc:
                raise FileStatisticsCalculationError(
                    file.filename,
                ) from exc

            file_statistics = self.calculate_file_statistics(
                content,
            )

            per_file_statistics[file.filename] = file_statistics

            total_counts.update(
                content,
            )

        total_statistics = {
            str(digit): total_counts.get(
                str(digit),
                0,
            )
            for digit in range(10)
        }

        return (
            total_statistics,
            per_file_statistics,
        )
