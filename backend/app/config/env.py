"""
config/env.py
--------------
Secrets and runtime environment variables.
All values here are read from the environment (or .env file via python-dotenv).
Nothing here should be hardcoded — for stable constants see constants.py.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Parser services
# ---------------------------------------------------------------------------
PARSER_URL: str         = os.getenv("PARSER_URL", "http://localhost:4004/api/v1/parser/parse")
PYMUPDF_PARSER_URL: str = os.getenv("PYMUPDF_PARSER_URL", "http://localhost:8001/parse")

# ---------------------------------------------------------------------------
# Azure OCR
# ---------------------------------------------------------------------------
AZURE_OCR_KEY: str      = os.getenv("AZURE_OCR_KEY", "")
AZURE_OCR_ENDPOINT: str = os.getenv("AZURE_OCR_ENDPOINT", "")
