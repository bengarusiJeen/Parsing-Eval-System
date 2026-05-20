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
    reports = svc.load_all_reports()

    if reports["general"] is None and reports["diagnostic"] is None:
        return JSONResponse({"status": "no_results"}, status_code=404)

    return JSONResponse({"status": "ok", **reports})
