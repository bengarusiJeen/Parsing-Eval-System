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

from backend.app.service.report_service import ReportService
from backend.app.service.evaluation_service import EvaluationService
from backend.app.service.stream_service import StreamService
from backend.app.service.comparison_service import ComparisonService


# ── Singleton providers ───────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_report_service() -> ReportService:
    return ReportService()


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    return EvaluationService(report_service=get_report_service())


@lru_cache(maxsize=1)
def get_stream_service() -> StreamService:
    return StreamService(report_service=get_report_service())


@lru_cache(maxsize=1)
def get_comparison_service() -> ComparisonService:
    return ComparisonService(report_service=get_report_service())
