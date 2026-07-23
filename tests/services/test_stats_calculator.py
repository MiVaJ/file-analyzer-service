from pathlib import Path

from app.models.downloaded_file import DownloadedFile
from app.services.stats_calculator import DigitStatisticsService


def test_calculate_file_statistics() -> None:
    """Проверяет подсчёт количества цифр в одном файле."""

    service = DigitStatisticsService()

    result = service.calculate_file_statistics(
        "0012399",
    )

    assert result == {
        "0": 2,
        "1": 1,
        "2": 1,
        "3": 1,
        "4": 0,
        "5": 0,
        "6": 0,
        "7": 0,
        "8": 0,
        "9": 2,
    }


def test_calculate_file_statistics_returns_zero_for_missing_digits() -> None:
    """Проверяет заполнение отсутствующих цифр нулевыми значениями."""

    service = DigitStatisticsService()

    result = service.calculate_file_statistics(
        "111",
    )

    assert result["1"] == 3

    for digit in "023456789":
        assert result[digit] == 0


def test_calculate_statistics_for_multiple_files(
    tmp_path: Path,
) -> None:
    """Проверяет расчёт общей статистики и статистики по каждому файлу."""

    file_1 = tmp_path / "first.txt"
    file_1.write_text(
        "0011",
        encoding="utf-8",
    )

    file_2 = tmp_path / "second.txt"
    file_2.write_text(
        "229",
        encoding="utf-8",
    )

    downloaded_files = [
        DownloadedFile(
            filename="first.txt",
            path=str(file_1),
        ),
        DownloadedFile(
            filename="second.txt",
            path=str(file_2),
        ),
    ]

    service = DigitStatisticsService()

    total, per_file = service.calculate_statistics(
        downloaded_files,
    )

    assert total == {
        "0": 2,
        "1": 2,
        "2": 2,
        "3": 0,
        "4": 0,
        "5": 0,
        "6": 0,
        "7": 0,
        "8": 0,
        "9": 1,
    }

    assert per_file["first.txt"]["0"] == 2
    assert per_file["first.txt"]["1"] == 2
    assert per_file["second.txt"]["2"] == 2
    assert per_file["second.txt"]["9"] == 1


def test_calculate_statistics_for_empty_file(
    tmp_path: Path,
) -> None:
    """Проверяет расчёт статистики для пустого файла."""

    file = tmp_path / "empty.txt"
    file.write_text(
        "",
        encoding="utf-8",
    )

    downloaded_files = [
        DownloadedFile(
            filename="empty.txt",
            path=str(file),
        ),
    ]

    service = DigitStatisticsService()

    total, per_file = service.calculate_statistics(
        downloaded_files,
    )

    assert all(value == 0 for value in total.values())

    assert all(value == 0 for value in per_file["empty.txt"].values())
