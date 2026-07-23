from pydantic import BaseModel


class StatsRequest(BaseModel):
    """Запрос на вычисление статистики."""

    file_ids: list[int]


class FileDigitStats(BaseModel):
    """Статистика по одному файлу."""

    filename: str
    digits: dict[str, int]


class StatsResponse(BaseModel):
    """Результат вычисления статистики."""

    total: dict[str, int]
    files: list[FileDigitStats]
