"""
backend/app/routes/stream_routes.py
--------------------------------------
GET /api/stream_data — annotated segment data for the Stream Comparison view.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from backend.app.dependencies import get_stream_service
from backend.app.service.stream_service import StreamService

router = APIRouter()


@router.get("/api/stream_data")
def stream_data(
    doc:    str = Query(default=""),
    parser: str = Query(default=""),
    svc:    StreamService = Depends(get_stream_service),
) -> JSONResponse:
    doc_name = doc.strip()
    if not doc_name:
        return JSONResponse({"error": "Missing ?doc= parameter"}, status_code=400)

    parser_method = parser.strip() or None
    return JSONResponse(svc.build_stream_data(doc_name, parser_method))
