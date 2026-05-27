"""
backend/app/schemas/requests.py
--------------------------------
Pydantic request models for the Parsing Eval System API.
"""
from __future__ import annotations

from pydantic import BaseModel, model_validator

from backend.app.config.constants import DEFAULT_PARSER_METHOD


class EvaluateRequest(BaseModel):
    selected: list[str] = []
    parser: str | None = None
    parsers: list[str] | None = None
    include_postprocessing: bool = False

    @model_validator(mode="after")
    def resolve_parsers(self) -> "EvaluateRequest":
        if not self.parsers:
            self.parsers = [self.parser] if self.parser else [DEFAULT_PARSER_METHOD]
        return self


class ComparisonFilterRequest(BaseModel):
    parsers: list[str]
    docs: list[str] = []
    parser_reports: dict | None = None
