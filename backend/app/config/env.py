"""
config/env.py
--------------
Secrets and runtime environment variables.
All values here are read from the environment (or .env file via python-dotenv).
Nothing here should be hardcoded — for stable constants see constants.py.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env explicitly so the variables resolve regardless of the
# current working directory the process was launched from.
_BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_BACKEND_ENV if _BACKEND_ENV.exists() else None)

# ---------------------------------------------------------------------------
# Parser service (single Jeen endpoint; parser variant chosen via parser_method)
# ---------------------------------------------------------------------------
PARSER_URL: str = os.getenv("PARSER_URL", "http://localhost:4004/api/v1/parser/parse")

# ---------------------------------------------------------------------------
# Azure OCR
# ---------------------------------------------------------------------------
AZURE_OCR_KEY: str      = os.getenv("AZURE_OCR_KEY", "")
AZURE_OCR_ENDPOINT: str = os.getenv("AZURE_OCR_ENDPOINT", "")

# ---------------------------------------------------------------------------
# Database (required for the evaluation-history feature)
# ---------------------------------------------------------------------------
# Read once at import time. The value is not logged anywhere — error messages
# must never include the URL or any part of it.
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set — required for the history feature. "
        "Add it to backend/.env (see backend/.env.example for the expected format)."
    )
