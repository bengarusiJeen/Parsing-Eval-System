"""
backend/app/schemas/history.py
--------------------------------
Pydantic response contracts for /api/history/* endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResultRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parser_name: str
    file_name: str
    coverage_checked: int
    coverage_failed: int
    coverage_rate: float
    noise_checked: int
    noise_failed: int
    noise_rate: float
    avg_score: float
    gt_word_count: int
    parser_word_count: int
    diagnostics_json: dict[str, Any] | None = None


class RunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    parsers: list[str] = Field(default_factory=list)
    files_count: int = 0


class RunDetail(RunSummary):
    selected_files: list[str] = Field(default_factory=list)
    results: list[ResultRow] = Field(default_factory=list)


class TimelinePoint(BaseModel):
    run_id: int
    started_at: datetime
    parser_name: str
    coverage: float | None
    noise: float | None
    avg_score: float | None
    doc_count: int
    file_set_changed: bool


class TimelineFilterEcho(BaseModel):
    parser: str
    files: list[str] | None = None


class TimelineResponse(BaseModel):
    points: list[TimelinePoint] = Field(default_factory=list)
    filter_echo: TimelineFilterEcho
