"""
backend/app/db/models/evaluation_result.py
--------------------------------------------
ORM model for evaluation_results — one row per (run, parser, file) result.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.db.models.evaluation_run import EvaluationRun


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parser_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)

    coverage_checked: Mapped[int] = mapped_column(Integer, nullable=False)
    coverage_failed: Mapped[int] = mapped_column(Integer, nullable=False)
    coverage_rate: Mapped[float] = mapped_column(Float, nullable=False)
    noise_checked: Mapped[int] = mapped_column(Integer, nullable=False)
    noise_failed: Mapped[int] = mapped_column(Integer, nullable=False)
    noise_rate: Mapped[float] = mapped_column(Float, nullable=False)
    avg_score: Mapped[float] = mapped_column(Float, nullable=False)
    gt_word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    parser_word_count: Mapped[int] = mapped_column(Integer, nullable=False)

    diagnostics_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    run: Mapped["EvaluationRun"] = relationship("EvaluationRun", back_populates="results")

    __table_args__ = (
        Index("ix_eval_results_run_parser", "run_id", "parser_name"),
        Index("ix_eval_results_parser_file", "parser_name", "file_name"),
        UniqueConstraint(
            "run_id", "parser_name", "file_name",
            name="uq_eval_results_run_parser_file",
        ),
    )
