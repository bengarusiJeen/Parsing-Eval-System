"""
backend/app/routes/comparison_routes.py
-----------------------------------------
GET  /api/comparison        — compare parsers from the last run.
POST /api/comparison/filter — re-slice for a custom subset of parsers/docs.
"""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from backend.app.dependencies import get_comparison_service, get_report_service
from backend.app.schemas.requests import ComparisonFilterRequest
from backend.app.service.comparison_service import ComparisonService
from backend.app.service.report_service import ReportService

router = APIRouter()


@router.get("/api/comparison")
def comparison(
    parsers: str = Query(default=""),
    docs: str = Query(default=""),
    svc: ComparisonService = Depends(get_comparison_service),
    report_svc: ReportService = Depends(get_report_service),
) -> JSONResponse:
    general = report_svc.load_general()
    if not general:
        return JSONResponse(
            {"error": "No results available. Run an evaluation first."},
            status_code=404,
        )

    parsers_list  = [p for p in parsers.split(",") if p] if parsers.strip() else []
    selected_docs = (
        [d for d in docs.split(",") if d]
        if docs.strip()
        else report_svc.all_doc_names(general)
    )

    if not parsers_list:
        return JSONResponse(
            {"error": "Pass ?parsers= with at least one parser id."},
            status_code=400,
        )

    return JSONResponse(asdict(svc.compare(parsers_list, selected_docs)))


@router.post("/api/comparison/filter")
def comparison_filter(
    body: ComparisonFilterRequest,
    svc: ComparisonService = Depends(get_comparison_service),
    report_svc: ReportService = Depends(get_report_service),
) -> JSONResponse:
    parsers        = body.parsers
    docs           = list(body.docs)
    parser_reports = body.parser_reports

    if not parsers:
        return JSONResponse({"error": "Provide at least one parser."}, status_code=400)

    if not parser_reports:
        general = report_svc.load_general()
        if not general:
            return JSONResponse(
                {"error": "No results available. Run an evaluation first."},
                status_code=404,
            )
        if not docs:
            docs = report_svc.all_doc_names(general)

    # Resolve docs from inline reports when still empty
    if not docs:
        reports = svc.build_reports_by_parser(parsers, inline=parser_reports)
        first   = next(iter(reports.values()), {})
        docs    = report_svc.all_doc_names(first.get("general") or {})

    return JSONResponse(asdict(svc.compare(parsers, docs, inline=parser_reports)))
