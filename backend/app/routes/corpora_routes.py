"""
backend/app/routes/corpora_routes.py
--------------------------------------
CRUD for corpora and corpus_files. No DB or aggregation logic here — routes
validate inputs and delegate to CorpusService.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.dependencies import get_corpus_service
from backend.app.schemas.corpus import (
    CorpusCreate,
    CorpusFileAssign,
    CorpusFileRead,
    CorpusFileUpdate,
    CorpusRead,
    CorpusUpdate,
)
from backend.app.service.corpus_service import (
    CorpusConflictError,
    CorpusService,
    CorpusValidationError,
)

router = APIRouter(prefix="/api/corpora")


# ── corpora ──────────────────────────────────────────────────────────────────

@router.get("", response_model=list[CorpusRead])
def list_corpora(
    include_inactive: bool = Query(False),
    svc: CorpusService = Depends(get_corpus_service),
) -> list[CorpusRead]:
    return [
        CorpusRead.model_validate(c)
        for c in svc.list_corpora(include_inactive=include_inactive)
    ]


@router.post("", response_model=CorpusRead, status_code=201)
def create_corpus(
    body: CorpusCreate,
    svc: CorpusService = Depends(get_corpus_service),
) -> CorpusRead:
    try:
        corpus = svc.create_corpus(
            name=body.name,
            description=body.description,
            overall_ratio=body.overall_ratio,
            is_active=body.is_active,
        )
    except CorpusConflictError as exc:
        raise HTTPException(status_code=409, detail=exc.detail)
    return CorpusRead.model_validate(corpus)


@router.patch("/{corpus_id}", response_model=CorpusRead)
def update_corpus(
    corpus_id: int,
    body: CorpusUpdate,
    svc: CorpusService = Depends(get_corpus_service),
) -> CorpusRead:
    try:
        corpus = svc.update_corpus(
            corpus_id,
            name=body.name,
            description=body.description,
            overall_ratio=body.overall_ratio,
            is_active=body.is_active,
        )
    except CorpusConflictError as exc:
        raise HTTPException(status_code=409, detail=exc.detail)
    if corpus is None:
        raise HTTPException(status_code=404, detail=f"corpus {corpus_id} not found")
    return CorpusRead.model_validate(corpus)


# ── corpus files ─────────────────────────────────────────────────────────────

@router.get("/{corpus_id}/files", response_model=list[CorpusFileRead])
def list_corpus_files(
    corpus_id: int,
    include_inactive: bool = Query(False),
    svc: CorpusService = Depends(get_corpus_service),
) -> list[CorpusFileRead]:
    files = svc.list_files(corpus_id, include_inactive=include_inactive)
    if files is None:
        raise HTTPException(status_code=404, detail=f"corpus {corpus_id} not found")
    return [CorpusFileRead.model_validate(f) for f in files]


@router.post("/{corpus_id}/files", response_model=CorpusFileRead, status_code=201)
def assign_corpus_file(
    corpus_id: int,
    body: CorpusFileAssign,
    svc: CorpusService = Depends(get_corpus_service),
) -> CorpusFileRead:
    try:
        cf = svc.assign_file(corpus_id, body.file_name)
    except CorpusValidationError as exc:
        status = 404 if exc.code in ("corpus_not_found", "file_not_found") else 400
        raise HTTPException(status_code=status, detail={"code": exc.code, "message": exc.detail})
    except CorpusConflictError as exc:
        raise HTTPException(status_code=409, detail=exc.detail)
    return CorpusFileRead.model_validate(cf)


@router.patch(
    "/{corpus_id}/files/{file_name:path}",
    response_model=CorpusFileRead,
)
def update_corpus_file(
    corpus_id: int,
    file_name: str,
    body: CorpusFileUpdate,
    svc: CorpusService = Depends(get_corpus_service),
) -> CorpusFileRead:
    cf = svc.update_file(corpus_id, file_name, is_active=body.is_active)
    if cf is None:
        raise HTTPException(
            status_code=404,
            detail=f"file {file_name!r} not assigned to corpus {corpus_id}",
        )
    return CorpusFileRead.model_validate(cf)
