"""
backend/app/routes/history_routes.py
--------------------------------------
GET endpoints for the evaluation-history feature.

Routes validate inputs and delegate to services. No DB or aggregation logic.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.db.models.evaluation_run import EvaluationRun
from backend.app.dependencies import (
    get_evaluation_history_service,
    get_timeline_service,
)
from backend.app.schemas.corpus import OverallTimelineResponse
from backend.app.schemas.history import (
    ResultRow,
    RunDetail,
    RunSummary,
    TimelineResponse,
)
from backend.app.service.evaluation_history_service import EvaluationHistoryService
from backend.app.service.timeline_service import TimelineService

router = APIRouter(prefix="/api/history")


def _to_summary(run: EvaluationRun) -> RunSummary:
    parsers = list(run.selected_parsers_json or [])
    files = list(run.selected_files_json or [])
    return RunSummary(
        id=run.id,
        run_type=run.run_type,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        parsers=parsers,
        files_count=len(files),
    )


@router.get("/runs", response_model=list[RunSummary])
def list_runs(
    limit: int = Query(7, ge=1, le=200),
    svc: EvaluationHistoryService = Depends(get_evaluation_history_service),
) -> list[RunSummary]:
    runs = svc.get_recent_runs(limit)
    return [_to_summary(r) for r in runs]


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run_detail(
    run_id: int,
    include_diagnostics: bool = Query(False),
    svc: EvaluationHistoryService = Depends(get_evaluation_history_service),
) -> RunDetail:
    run = svc.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")

    summary = _to_summary(run)
    rows = [
        ResultRow(
            parser_name=r.parser_name,
            file_name=r.file_name,
            coverage_checked=r.coverage_checked,
            coverage_failed=r.coverage_failed,
            coverage_rate=r.coverage_rate,
            noise_checked=r.noise_checked,
            noise_failed=r.noise_failed,
            noise_rate=r.noise_rate,
            avg_score=r.avg_score,
            gt_word_count=r.gt_word_count,
            parser_word_count=r.parser_word_count,
            diagnostics_json=(r.diagnostics_json if include_diagnostics else None),
        )
        for r in (run.results or [])
    ]
    return RunDetail(
        **summary.model_dump(),
        selected_files=list(run.selected_files_json or []),
        results=rows,
    )


@router.get("/timeline", response_model=TimelineResponse)
def get_timeline(
    parser: str = Query(..., min_length=1),
    files: str | None = Query(None, description="Optional CSV of file names"),
    corpus_id: int | None = Query(
        None,
        description=(
            "Optional corpus id. When set, the active file list of the corpus "
            "is used as the file filter and the `files` query param is ignored."
        ),
    ),
    limit: int = Query(7, ge=1, le=200),
    svc: TimelineService = Depends(get_timeline_service),
) -> TimelineResponse:
    if corpus_id is not None:
        result = svc.get_corpus_timeline(parser, corpus_id, limit)
        if result is None:
            raise HTTPException(status_code=404, detail=f"corpus {corpus_id} not found")
        return result

    file_names: list[str] | None = None
    if files:
        file_names = [f.strip() for f in files.split(",") if f.strip()]
        if not file_names:
            file_names = None
    return svc.get_parser_timeline(parser, file_names, limit)


@router.get("/timeline/overall", response_model=OverallTimelineResponse)
def get_overall_timeline(
    parser: str = Query(..., min_length=1),
    limit: int = Query(7, ge=1, le=200),
    svc: TimelineService = Depends(get_timeline_service),
) -> OverallTimelineResponse:
    return svc.get_overall_timeline(parser, limit)
