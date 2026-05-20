"""
backend/app/routes/files_routes.py
-------------------------------------
GET /api/files — list available document folders.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.config.constants import SUPPORTED_EXTS
from backend.app.core.paths import FILES_DIR

router = APIRouter()


@router.get("/api/files")
def list_files() -> JSONResponse:
    if not FILES_DIR.exists():
        return JSONResponse({"files": []})

    result = []
    for d in sorted(FILES_DIR.iterdir()):
        if not d.is_dir():
            continue
        ext = ""
        for f in d.iterdir():
            if f.suffix.lower() in SUPPORTED_EXTS:
                ext = f.suffix.lower().lstrip(".")
                break
        result.append({"name": d.name, "ext": ext})

    return JSONResponse({"files": result})
