"""
backend/app/core/paths.py
--------------------------
Centralised path definitions for the Parsing Eval System backend.
All paths are resolved relative to this file so the backend can be invoked
from any working directory.
"""
from __future__ import annotations

from pathlib import Path

# backend/app/core/paths.py  →  go up 4 levels to reach project root
ROOT = Path(__file__).resolve().parent.parent.parent.parent

FRONTEND_DIR      = ROOT / "frontend"
DATA_DIR          = ROOT / "data"
FILES_DIR         = DATA_DIR / "files_corpus"
PARSING_FILES_DIR = DATA_DIR / "parsing_results"

REPORTS_DIR = ROOT / "reports"

GENERAL_JSON    = REPORTS_DIR / "general_report.json"
DIAG_JSON       = REPORTS_DIR / "diagnostics_report.json"
GENERAL_PP_JSON = REPORTS_DIR / "postprocessing-general_report.json"
DIAG_PP_JSON    = REPORTS_DIR / "postprocessing-diagnostics_report.json"

# Full last-run snapshot (single- or multi-parser) so the Results and Compare
# pages can restore per-parser data after a reload without re-running parsers.
LAST_RUN_JSON   = REPORTS_DIR / "last_run.json"
