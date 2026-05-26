"""
backend/app/dependencies.py
-----------------------------
FastAPI dependency providers — the single place where all service instances
are created and wired together.

Usage in route handlers:
    from fastapi import Depends
    from backend.app.dependencies import get_evaluation_service

    @router.post("/api/evaluate")
    def evaluate(
        request: EvaluateRequest,
        svc: EvaluationService = Depends(get_evaluation_service),
    ): ...

To swap an implementation (e.g. for testing), override the provider here.
"""
from __future__ import annotations

from functools import lru_cache

from backend.app.db.session import SessionLocal
from backend.app.repositories.corpus_repository import CorpusRepository
from backend.app.repositories.evaluation_history_repository import (
    EvaluationHistoryRepository,
)
from backend.app.service.comparison_service import ComparisonService
from backend.app.service.corpus_service import CorpusService
from backend.app.service.evaluation_history_service import EvaluationHistoryService
from backend.app.service.evaluation_service import EvaluationService
from backend.app.service.report_service import ReportService
from backend.app.service.stream_service import StreamService
from backend.app.service.timeline_service import TimelineService


# ── DB session (per-request) ──────────────────────────────────────────────────

def get_db():
    """FastAPI dependency: yield a SQLAlchemy session and close it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Singleton providers ───────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_report_service() -> ReportService:
    return ReportService()


@lru_cache(maxsize=1)
def get_evaluation_history_repository() -> EvaluationHistoryRepository:
    return EvaluationHistoryRepository()


@lru_cache(maxsize=1)
def get_corpus_repository() -> CorpusRepository:
    return CorpusRepository()


@lru_cache(maxsize=1)
def get_evaluation_history_service() -> EvaluationHistoryService:
    return EvaluationHistoryService(
        repository=get_evaluation_history_repository(),
        session_factory=SessionLocal,
    )


@lru_cache(maxsize=1)
def get_corpus_service() -> CorpusService:
    return CorpusService(
        repository=get_corpus_repository(),
        session_factory=SessionLocal,
    )


@lru_cache(maxsize=1)
def get_timeline_service() -> TimelineService:
    return TimelineService(
        repository=get_evaluation_history_repository(),
        corpus_repository=get_corpus_repository(),
        session_factory=SessionLocal,
    )


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    return EvaluationService(
        report_service=get_report_service(),
        history_service=get_evaluation_history_service(),
    )


@lru_cache(maxsize=1)
def get_stream_service() -> StreamService:
    return StreamService(report_service=get_report_service())


@lru_cache(maxsize=1)
def get_comparison_service() -> ComparisonService:
    return ComparisonService(report_service=get_report_service())
