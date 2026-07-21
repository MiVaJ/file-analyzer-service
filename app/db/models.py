import datetime as dt

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DownloadedFile(Base):
    """Метаданные файла, скачанного из внешнего каталога.

    Само содержимое файла хранится на диске в `settings.download_dir`,
    а не в базе данных (app/services/file_storage.py).
    """

    __tablename__ = "downloaded_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    downloaded_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
