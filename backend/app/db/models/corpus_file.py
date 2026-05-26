"""
backend/app/db/models/corpus_file.py
--------------------------------------
ORM model for `corpus_files` — assigns an existing evaluation file (folder name
under FILES_DIR) to a corpus. Soft-deletable via is_active.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.db.models.corpus import Corpus


class CorpusFile(Base):
    __tablename__ = "corpus_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    corpus_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("corpora.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    corpus: Mapped["Corpus"] = relationship("Corpus", back_populates="files")

    __table_args__ = (
        UniqueConstraint("corpus_id", "file_name", name="uq_corpus_files_corpus_file"),
        Index("ix_corpus_files_corpus_active", "corpus_id", "is_active"),
    )
