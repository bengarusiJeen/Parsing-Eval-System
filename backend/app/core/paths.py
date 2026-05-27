"""
backend/app/core/paths.py
--------------------------
Centralised path definitions for the Parsing Eval System backend.
All paths are resolved relative to this file so the backend can be invoked
from any working directory.
"""
from __future__ import annotations

import re
from pathlib import Path

# backend/app/core/paths.py  →  go up 4 levels to reach project root
ROOT = Path(__file__).resolve().parent.parent.parent.parent

FRONTEND_DIR      = ROOT / "frontend"
DATA_DIR          = ROOT / "data"
FILES_DIR         = DATA_DIR / "files_corpus"
PARSING_FILES_DIR = DATA_DIR / "parsing_results"

REPORTS_DIR = ROOT / "reports"

# Flat report filenames. Stage 3 of the perf refactor moved each parser's
# reports into a per-parser subfolder, but these flat copies are still
# written for single-parser runs (backward-compat for any external consumer
# that reads them directly).
GENERAL_JSON    = REPORTS_DIR / "general_report.json"
DIAG_JSON       = REPORTS_DIR / "diagnostics_report.json"
GENERAL_PP_JSON = REPORTS_DIR / "postprocessing-general_report.json"
DIAG_PP_JSON    = REPORTS_DIR / "postprocessing-diagnostics_report.json"

# Full last-run snapshot (single- or multi-parser) so the Results and Compare
# pages can restore per-parser data after a reload without re-running parsers.
LAST_RUN_JSON   = REPORTS_DIR / "last_run.json"

# Report file basenames (used in both the flat and per-parser layouts).
GENERAL_FILENAME    = "general_report.json"
DIAG_FILENAME       = "diagnostics_report.json"
GENERAL_PP_FILENAME = "postprocessing-general_report.json"
DIAG_PP_FILENAME    = "postprocessing-diagnostics_report.json"

REPORT_FILENAMES    = (GENERAL_FILENAME, DIAG_FILENAME)
PP_REPORT_FILENAMES = (GENERAL_PP_FILENAME, DIAG_PP_FILENAME)


_PARSER_SEGMENT_RE = re.compile(r"[^A-Za-z0-9_.-]")


def sanitize_parser_segment(parser_method: str) -> str:
    """Sanitize a parser_method string for use as a filesystem path segment.

    Parser methods are usually ASCII identifiers (e.g. ``document_intelligence``),
    but we sanitize defensively so an unexpected string can never escape its
    intended subfolder or break Windows path handling.
    """
    cleaned = _PARSER_SEGMENT_RE.sub("_", parser_method or "").strip("._")
    return cleaned or "_"


def per_parser_reports_dir(parser_method: str) -> Path:
    """``reports/<parser_method>/`` for this parser's JSON reports."""
    return REPORTS_DIR / sanitize_parser_segment(parser_method)


def per_parser_parsing_dir(parser_method: str) -> Path:
    """``data/parsing_results/<parser_method>/`` for this parser's raw + PP text."""
    return PARSING_FILES_DIR / sanitize_parser_segment(parser_method)
