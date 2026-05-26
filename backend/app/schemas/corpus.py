"""
backend/app/schemas/corpus.py
-------------------------------
Pydantic contracts for /api/corpora/* endpoints and the overall-timeline
response.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.history import TimelinePoint


class CorpusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    overall_ratio: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CorpusCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    overall_ratio: float = Field(default=0.0, ge=0.0)
    is_active: bool = True


class CorpusUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    overall_ratio: float | None = Field(default=None, ge=0.0)
    is_active: bool | None = None


class CorpusFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    corpus_id: int
    file_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CorpusFileAssign(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=512)


class CorpusFileUpdate(BaseModel):
    is_active: bool | None = None


class OverallTimelinePoint(BaseModel):
    run_id: int
    started_at: datetime
    overall_score: float | None
    contributing_corpora: int
    ratios_sum: float
    normalization_applied: bool
    warning: str | None = None
    per_corpus: dict[str, float | None] = Field(default_factory=dict)


class OverallTimelineResponse(BaseModel):
    points: list[OverallTimelinePoint] = Field(default_factory=list)
    parser: str


__all__ = [
    "CorpusRead",
    "CorpusCreate",
    "CorpusUpdate",
    "CorpusFileRead",
    "CorpusFileAssign",
    "CorpusFileUpdate",
    "OverallTimelinePoint",
    "OverallTimelineResponse",
    "TimelinePoint",
]
