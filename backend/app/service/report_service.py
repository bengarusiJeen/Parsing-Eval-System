"""
backend/app/service/report_service.py
----------------------------------------
ReportService: all reads and writes of JSON report files on disk.
Instantiated once and injected via FastAPI Depends().
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from backend.app.core.paths import (
    DIAG_FILENAME,
    DIAG_JSON,
    DIAG_PP_FILENAME,
    DIAG_PP_JSON,
    GENERAL_FILENAME,
    GENERAL_JSON,
    GENERAL_PP_FILENAME,
    GENERAL_PP_JSON,
    LAST_RUN_JSON,
    PP_REPORT_FILENAMES,
    REPORT_FILENAMES,
    REPORTS_DIR,
    per_parser_reports_dir,
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
        """Delete the flat report files, ignoring missing-file errors.

        The flat report files at ``reports/general_report.json`` etc. are only
        written for single-parser runs (backward-compat). Multi-parser runs
        write only to per-parser subfolders, so this should be called when
        the flat copies might be stale (e.g. before a multi-parser run).
        """
        for p in [GENERAL_JSON, DIAG_JSON, GENERAL_PP_JSON, DIAG_PP_JSON]:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass

    def wipe_for(self, parser_method: str, include_pp: bool = True) -> None:
        """Delete this parser's per-subfolder reports.

        Always wipes the raw report files. When ``include_pp`` is True
        (the default) the PP report files are wiped too — pass False if
        the caller knows the PP files should be preserved.
        """
        parser_dir = per_parser_reports_dir(parser_method)
        names = list(REPORT_FILENAMES)
        if include_pp:
            names += list(PP_REPORT_FILENAMES)
        for name in names:
            try:
                (parser_dir / name).unlink(missing_ok=True)
            except OSError:
                pass

    def copy_per_parser_to_flat(self, parser_method: str) -> None:
        """Copy a parser's subfolder reports out to the flat REPORTS_DIR.

        Single-parser runs use this so the legacy flat filenames at
        ``reports/general_report.json`` etc. stay populated for any external
        consumer (e.g. the comparison service's flat-file fallback) that
        still reads them.
        """
        parser_dir = per_parser_reports_dir(parser_method)
        pairs = (
            (parser_dir / GENERAL_FILENAME,    GENERAL_JSON),
            (parser_dir / DIAG_FILENAME,       DIAG_JSON),
            (parser_dir / GENERAL_PP_FILENAME, GENERAL_PP_JSON),
            (parser_dir / DIAG_PP_FILENAME,    DIAG_PP_JSON),
        )
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        for src, dst in pairs:
            try:
                if src.exists():
                    shutil.copyfile(src, dst)
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
        """Load all four flat report files and return them as a single dict."""
        return {
            "general":       self.load_general(),
            "diagnostic":    self.load_diagnostic(),
            "general_pp":    self.load_general_pp(),
            "diagnostic_pp": self.load_diagnostic_pp(),
        }

    def load_all_reports_for(self, parser_method: str) -> dict:
        """Load this parser's four report files from its subfolder.

        Falls back to the flat path for each missing file so a legacy snapshot
        (pre-Stage-3) or a single-parser run that hasn't been re-routed yet
        still loads correctly.
        """
        parser_dir = per_parser_reports_dir(parser_method)

        def _load(name: str, flat: Path) -> dict | None:
            sub = parser_dir / name
            return self.load_json(sub) if sub.exists() else self.load_json(flat)

        return {
            "general":       _load(GENERAL_FILENAME,    GENERAL_JSON),
            "diagnostic":    _load(DIAG_FILENAME,       DIAG_JSON),
            "general_pp":    _load(GENERAL_PP_FILENAME, GENERAL_PP_JSON),
            "diagnostic_pp": _load(DIAG_PP_FILENAME,    DIAG_PP_JSON),
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
