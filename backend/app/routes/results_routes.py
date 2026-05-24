"""
backend/app/routes/results_routes.py
--------------------------------------
GET /api/results — return cached evaluation reports without re-running.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from backend.app.dependencies import get_report_service
from backend.app.service.report_service import ReportService

router = APIRouter()


@router.get("/api/results")
def results(
    svc: ReportService = Depends(get_report_service),
) -> JSONResponse:                                       # inject ReportService via FastAPI Depends
    # Prefer the full last-run snapshot so multi-parser runs restore every
    # parser's reports (needed by the Compare page), not just the last one.
    last_run = svc.load_last_run()
    if last_run:
        if last_run.get("multi_parser"):
            has_results = any(
                (p or {}).get("general") for p in (last_run.get("parsers") or {}).values()
            )
            if has_results:
                return JSONResponse({"status": "ok", **last_run})
        elif last_run.get("general") is not None:
            return JSONResponse({"status": "ok", **last_run})

    reports = svc.load_all_reports()

    if reports["general"] is None and reports["diagnostic"] is None:
        return JSONResponse({"status": "no_results"}, status_code=404)

    return JSONResponse({"status": "ok", **reports})
