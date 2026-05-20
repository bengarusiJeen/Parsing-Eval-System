"""
backend/app/routes/evaluation_routes.py
-----------------------------------------
POST /api/evaluate — run the evaluation pipeline.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from backend.app.dependencies import get_evaluation_service
from backend.app.schemas.requests import EvaluateRequest
from backend.app.service.evaluation_service import EvaluationService

router = APIRouter()


@router.post("/api/evaluate")
def evaluate(
    request: EvaluateRequest,
    svc: EvaluationService = Depends(get_evaluation_service),
) -> JSONResponse:
    return JSONResponse(svc.run_evaluation(request))
