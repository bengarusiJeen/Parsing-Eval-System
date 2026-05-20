"""
config/constants.py
--------------------
All non-secret, stable constants for the application.
Nothing here depends on runtime environment — for secrets and env vars see env.py.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# HTTP / subprocess timeouts (seconds)
# ---------------------------------------------------------------------------
PARSER_HTTP_TIMEOUT        = 1200   # httpx timeout for calls to parser services
PIPELINE_SUBPROCESS_TIMEOUT = 1800  # subprocess.run timeout for the evaluation pipeline

# ---------------------------------------------------------------------------
# CORS origins allowed by the FastAPI app
# ---------------------------------------------------------------------------
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
]
# ========maybe dont need all of them=========
# ---------------------------------------------------------------------------
# Default parser method used when none is specified
# ---------------------------------------------------------------------------
DEFAULT_PARSER_METHOD = "base_text_parser"

# ---------------------------------------------------------------------------
# Python module path for running the evaluation pipeline as a subprocess
# ---------------------------------------------------------------------------
PIPELINE_MODULE = "backend.app.pipeline.main"

# ---------------------------------------------------------------------------
# Ground-truth block delimiter (shared by gt_loader and stream_service)
# ---------------------------------------------------------------------------
GT_BLOCK_DELIMITER = "===="

# ---------------------------------------------------------------------------
# Supported document file extensions
# (files_routes uses this set; .txt excluded from upload scanning)
# ---------------------------------------------------------------------------
SUPPORTED_EXTS = {".pdf", ".docx", ".doc", ".pptx", ".xlsx"}

# ---------------------------------------------------------------------------
# Diagnostic thresholds
# ---------------------------------------------------------------------------
MISSING_BLOCK_THRESHOLD = 0.10  # coverage fraction below which a block is flagged missing
