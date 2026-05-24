"""
backend/app/service/report_service.py
----------------------------------------
ReportService: all reads and writes of JSON report files on disk.
Instantiated once and injected via FastAPI Depends().
"""
from __future__ import annotations

import json
from pathlib import Path

from backend.app.core.paths import (
    DIAG_JSON,
    DIAG_PP_JSON,
    GENERAL_JSON,
    GENERAL_PP_JSON,
    LAST_RUN_JSON,
    REPORTS_DIR,
)


class ReportService:
    """Owns all JSON report I/O for the evaluation pipeline."""

    # ── low-level helpers ────────────────────────────────────────────────────

    def load_json(self, path: Path) -> dict | None:
        """Read a JSON file; return None if missing or malformed."""
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError):
            return None

    def wipe_report_files(self) -> None:
        """Delete all known report files, ignoring missing-file errors."""
        for p in [GENERAL_JSON, DIAG_JSON, GENERAL_PP_JSON, DIAG_PP_JSON]:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass

    # ── named report loaders ─────────────────────────────────────────────────

    def load_general(self) -> dict | None:
        return self.load_json(GENERAL_JSON)

    def load_diagnostic(self) -> dict | None:
        return self.load_json(DIAG_JSON)

    def load_general_pp(self) -> dict | None:
        return self.load_json(GENERAL_PP_JSON)

    def load_diagnostic_pp(self) -> dict | None:
        return self.load_json(DIAG_PP_JSON)

    def load_all_reports(self) -> dict:
        """Load all four report files and return them as a single dict."""
        return {
            "general":       self.load_general(),
            "diagnostic":    self.load_diagnostic(),
            "general_pp":    self.load_general_pp(),
            "diagnostic_pp": self.load_diagnostic_pp(),
        }

    # ── full-run snapshot ─────────────────────────────────────────────────────

    def save_last_run(self, data: dict) -> None:
        """Persist the full run result (single- or multi-parser) for later reload.

        Strips bulky subprocess logs (stdout/stderr) so the snapshot stays small;
        the report payloads themselves are what the UI needs to restore.
        """
        try:
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            LAST_RUN_JSON.write_text(
                json.dumps(self._strip_logs(data)), encoding="utf-8"
            )
        except OSError:
            pass

    def load_last_run(self) -> dict | None:
        """Read the full last-run snapshot, or None if absent/malformed."""
        return self.load_json(LAST_RUN_JSON)

    @staticmethod
    def _strip_logs(data: dict) -> dict:
        """Return a copy of a run result without stdout/stderr fields."""
        def clean(d: dict) -> dict:
            return {k: v for k, v in d.items() if k not in ("stdout", "stderr")}

        if data.get("multi_parser"):
            return {
                "multi_parser": True,
                "parsers": {
                    pid: clean(res) for pid, res in (data.get("parsers") or {}).items()
                },
            }
        return clean(data)

    # ── document helpers ─────────────────────────────────────────────────────

    def find_doc(self, data: dict | None, doc_name: str) -> dict | None:
        """Find a document entry by doc_name inside a report dict."""
        if not data:
            return None
        return next(
            (d for d in data.get("documents", []) if d.get("doc_name") == doc_name),
            None,
        )

    def all_doc_names(self, general: dict | None) -> list[str]:
        """Return all non-empty doc_name values from a general report."""
        if not general:
            return []
        return [
            d.get("doc_name", "")
            for d in general.get("documents", [])
            if d.get("doc_name")
        ]
