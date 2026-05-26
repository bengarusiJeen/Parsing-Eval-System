"""
backend/app/repositories/evaluation_history_repository.py
------------------------------------------------------------
All DB access for the evaluation_runs and evaluation_results tables.

Stateless — methods accept a Session argument; services own session lifetime.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from sqlalchemy import insert, select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models.evaluation_result import EvaluationResult
from backend.app.db.models.evaluation_run import EvaluationRun


class EvaluationHistoryRepository:
    # ── writes ───────────────────────────────────────────────────────────────

    def create_run(
        self,
        db: Session,
        *,
        run_type: str,
        status: str,
        started_at: datetime,
        selected_parsers: list[str],
        selected_files: list[str],
    ) -> EvaluationRun:
        run = EvaluationRun(
            run_type=run_type,
            status=status,
            started_at=started_at,
            # sort selected_files on write so set comparisons across runs are stable
            selected_parsers_json=list(selected_parsers),
            selected_files_json=sorted(selected_files),
        )
        db.add(run)
        db.flush()
        return run

    def finish_run(
        self,
        db: Session,
        run: EvaluationRun,
        *,
        status: str,
        finished_at: datetime,
    ) -> None:
        run.status = status
        run.finished_at = finished_at
        db.flush()

    def bulk_insert_results(
        self,
        db: Session,
        run_id: int,
        rows: list[dict[str, Any]],
    ) -> None:
        if not rows:
            return
        payload = [dict(r, run_id=run_id) for r in rows]
        db.execute(insert(EvaluationResult), payload)

    # ── reads ────────────────────────────────────────────────────────────────

    def get_recent_runs(self, db: Session, limit: int) -> list[EvaluationRun]:
        stmt = (
            select(EvaluationRun)
            .order_by(EvaluationRun.created_at.desc(), EvaluationRun.id.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    def get_run(self, db: Session, run_id: int) -> EvaluationRun | None:
        stmt = (
            select(EvaluationRun)
            .options(selectinload(EvaluationRun.results))
            .where(EvaluationRun.id == run_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    def get_recent_run_ids_with_results(
        self,
        db: Session,
        *,
        parser_name: str,
        file_names: set[str] | None,
        limit: int,
    ) -> list[int]:
        """Latest N run ids that actually contain results matching the filter.

        Critical: we do NOT take the latest N global runs and then filter — that
        would silently return fewer points than requested when newer runs don't
        include this parser/file. We filter first, then take the newest N.
        """
        stmt = (
            select(EvaluationRun.id)
            .join(EvaluationResult, EvaluationResult.run_id == EvaluationRun.id)
            .where(EvaluationResult.parser_name == parser_name)
        )
        if file_names:
            stmt = stmt.where(EvaluationResult.file_name.in_(file_names))
        stmt = (
            stmt.group_by(EvaluationRun.id, EvaluationRun.created_at)
            .order_by(EvaluationRun.created_at.desc(), EvaluationRun.id.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    def get_runs_by_ids(
        self, db: Session, run_ids: Iterable[int]
    ) -> list[EvaluationRun]:
        ids = list(run_ids)
        if not ids:
            return []
        stmt = select(EvaluationRun).where(EvaluationRun.id.in_(ids))
        return list(db.execute(stmt).scalars().all())

    def get_results_for_runs(
        self,
        db: Session,
        *,
        parser_name: str,
        file_names: set[str] | None,
        run_ids: Iterable[int],
    ) -> list[EvaluationResult]:
        ids = list(run_ids)
        if not ids:
            return []
        stmt = (
            select(EvaluationResult)
            .where(
                EvaluationResult.parser_name == parser_name,
                EvaluationResult.run_id.in_(ids),
            )
        )
        if file_names:
            stmt = stmt.where(EvaluationResult.file_name.in_(file_names))
        return list(db.execute(stmt).scalars().all())
