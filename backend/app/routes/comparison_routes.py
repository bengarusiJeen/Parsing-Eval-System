"""
backend/app/routes/comparison_routes.py
-----------------------------------------
GET  /api/comparison/info   — parsers + docs available for the Compare UI.
GET  /api/comparison        — compare parsers from the last run (query-param variant).
POST /api/comparison/filter — re-slice for a custom subset of parsers/docs.

The Compare page should call /api/comparison/info to populate its filter UI,
then POST /api/comparison/filter to get ranked scores.  No report data needs to
be sent FROM the frontend — all computation and storage happens here.
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


@router.get("/api/comparison/info")
def comparison_info(
    report_svc: ReportService = Depends(get_report_service),
) -> JSONResponse:
    """Return the parsers and documents available for comparison.

    Reads the last-run snapshot so any frontend can populate its filter UI
    without holding evaluation results in memory or sending them back here.
    Parsers that produced no report (e.g. failed runs) are excluded — they
    would pool to a deceptively perfect score of 1.0.
    """
    last_run = report_svc.load_last_run()
    if not last_run:
        return JSONResponse({"parsers": [], "docs": []})

    if last_run.get("multi_parser"):
        parsers_data = last_run.get("parsers") or {}
        parsers = [
            pid for pid, d in parsers_data.items()
            if (d or {}).get("general")
        ]
        seen: set[str] = set()
        docs: list[str] = []
        for pid in parsers:
            general = (parsers_data.get(pid) or {}).get("general") or {}
            for entry in general.get("documents", []):
                name = entry.get("doc_name", "")
                if name and name not in seen:
                    seen.add(name)
                    docs.append(name)
        return JSONResponse({"parsers": parsers, "docs": docs})

    # Single-parser snapshot — tagged with _parser_id on save
    parser_id = last_run.get("_parser_id")
    general   = last_run.get("general")
    if parser_id and general:
        return JSONResponse({
            "parsers": [parser_id],
            "docs":    report_svc.all_doc_names(general),
        })

    return JSONResponse({"parsers": [], "docs": []})


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
    # parser_reports is optional — the standard frontend does NOT send it.
    # It is retained in the schema so external API clients and tests can
    # supply inline data without needing a prior on-disk snapshot.
    parser_reports = body.parser_reports

    if not parsers:
        return JSONResponse({"error": "Provide at least one parser."}, status_code=400)

    # If docs were not specified, auto-derive them from the stored per-parser reports.
    if not docs:
        reports = svc.build_reports_by_parser(parsers, inline=parser_reports)
        seen: set[str] = set()
        auto_docs: list[str] = []
        for rep in reports.values():
            for name in report_svc.all_doc_names((rep or {}).get("general")):
                if name not in seen:
                    seen.add(name)
                    auto_docs.append(name)
        docs = auto_docs

    if not docs:
        return JSONResponse(
            {"error": "No results available. Run an evaluation first."},
            status_code=404,
        )

    return JSONResponse(asdict(svc.compare(parsers, docs, inline=parser_reports)))
