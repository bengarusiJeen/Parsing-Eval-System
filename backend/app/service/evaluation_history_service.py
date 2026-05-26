"""
backend/app/service/evaluation_history_service.py
---------------------------------------------------
Application/business logic for evaluation history persistence and reads.

Owns its own DB session lifetime (best-effort, transaction per call).
EvaluationService calls `persist_evaluation` once after each run completes;
history routes call the read methods.

Security: no log line in this module includes the connection string.
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from backend.app.db.models.evaluation_run import EvaluationRun
from backend.app.repositories.evaluation_history_repository import (
    EvaluationHistoryRepository,
)
from backend.app.schemas.requests import EvaluateRequest
from backend.app.service.evaluation_report_extractor import (
    ParserDocumentResult,
    extract_parser_document_results,
)

logger = logging.getLogger(__name__)


def _split_payloads(request: EvaluateRequest, result: dict) -> dict[str, dict]:
    """Return a {parser_name: payload_dict} map for both single & multi flows.

    For single-parser runs we use request.parsers[0] as the authoritative name
    (not result['_parser_id'], which only exists on that branch).
    """
    if result.get("multi_parser"):
        parsers_block = result.get("parsers") or {}
        return {str(name): payload for name, payload in parsers_block.items()}
    if request.parsers:
        return {request.parsers[0]: result}
    return {}


def _row_dict(r: ParserDocumentResult) -> dict[str, Any]:
    d = asdict(r)
    d.pop("parser_name", None)
    return {
        "parser_name": r.parser_name,
        **{k: v for k, v in d.items()},
    }


class EvaluationHistoryService:
    def __init__(
        self,
        repository: EvaluationHistoryRepository,
        session_factory: Callable[[], Session],
    ) -> None:
        self._repo = repository
        self._session_factory = session_factory

    # ── write ────────────────────────────────────────────────────────────────

    def persist_evaluation(
        self, request: EvaluateRequest, result: dict
    ) -> int | None:
        """Persist a completed evaluation. Best-effort: returns None on failure."""
        started_at = datetime.now(timezone.utc)
        payloads = _split_payloads(request, result)
        if not payloads:
            logger.warning("persist_evaluation: no parser payloads in result, skipping")
            return None

        per_parser_rows: dict[str, list[ParserDocumentResult]] = {}
        succeeded = 0
        failed = 0
        for parser_name, payload in payloads.items():
            if payload.get("status") != "ok" or not payload.get("general"):
                failed += 1
                continue
            rows = extract_parser_document_results(
                payload.get("general"),
                payload.get("diagnostic"),
                parser_name,
            )
            per_parser_rows[parser_name] = rows
            succeeded += 1

        if succeeded == 0:
            run_status = "failed"
        elif failed == 0:
            run_status = "completed"
        else:
            run_status = "partial"

        finished_at = datetime.now(timezone.utc)

        db = self._session_factory()
        try:
            run = self._repo.create_run(
                db,
                run_type="manual",
                status="running",
                started_at=started_at,
                selected_parsers=list(request.parsers or []),
                selected_files=list(request.selected or []),
            )
            all_rows: list[dict[str, Any]] = []
            for rows in per_parser_rows.values():
                all_rows.extend(_row_dict(r) for r in rows)

            self._repo.bulk_insert_results(db, run.id, all_rows)
            self._repo.finish_run(
                db, run, status=run_status, finished_at=finished_at
            )
            db.commit()
            logger.info(
                "Persisted evaluation run id=%s status=%s parsers=%s rows=%s",
                run.id, run_status, len(payloads), len(all_rows),
            )
            return run.id
        except Exception:
            db.rollback()
            logger.exception("persist_evaluation failed; run not saved")
            return None
        finally:
            db.close()

    # ── reads ────────────────────────────────────────────────────────────────

    def get_recent_runs(self, limit: int) -> list[EvaluationRun]:
        db = self._session_factory()
        try:
            return self._repo.get_recent_runs(db, limit)
        finally:
            db.close()

    def get_run(self, run_id: int) -> EvaluationRun | None:
        db = self._session_factory()
        try:
            return self._repo.get_run(db, run_id)
        finally:
            db.close()
