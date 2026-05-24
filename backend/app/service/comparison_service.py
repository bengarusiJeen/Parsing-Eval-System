"""
backend/app/service/comparison_service.py
--------------------------------------------
ComparisonService: builds reports_by_parser and runs compare_parsers().
Receives a ReportService instance via constructor injection.
"""
from __future__ import annotations

from backend.app.models.comparison_models import ComparisonResult
from backend.app.core.comparison_engine import compare_parsers
from backend.app.service.report_service import ReportService


class ComparisonService:
    def __init__(self, report_service: ReportService) -> None:
        self._reports = report_service

    def build_reports_by_parser(
        self,
        parsers: list[str],
        inline: dict | None = None,
    ) -> dict[str, dict]:
        """
        Build the reports_by_parser dict for compare_parsers().

        If *inline* is provided (frontend passes per-parser report data),
        use that directly. Otherwise fall back to the last on-disk reports.
        """
        if inline:
            return {
                p: {
                    "general":    inline.get(p, {}).get("general"),
                    "general_pp": inline.get(p, {}).get("general_pp"),
                }
                for p in parsers
            }

        # No inline data: pull each parser's own reports from the last-run
        # snapshot so multi-parser comparisons survive a reload.
        last_run = self._reports.load_last_run()
        if last_run and last_run.get("multi_parser"):
            saved = last_run.get("parsers") or {}
            return {
                p: {
                    "general":    (saved.get(p) or {}).get("general"),
                    "general_pp": (saved.get(p) or {}).get("general_pp"),
                }
                for p in parsers
            }

        # Single-parser run (or legacy flat files): same report for each parser.
        general    = self._reports.load_general()
        general_pp = self._reports.load_general_pp()
        return {p: {"general": general, "general_pp": general_pp} for p in parsers}

    def compare(
        self,
        parsers: list[str],
        selected_docs: list[str],
        inline: dict | None = None,
    ) -> ComparisonResult:
        """Build reports and run compare_parsers() in one call."""
        reports = self.build_reports_by_parser(parsers, inline=inline)
        return compare_parsers(reports, selected_docs)
