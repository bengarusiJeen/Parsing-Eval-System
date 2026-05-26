"""
backend/app/db/init_db.py
---------------------------
One-shot schema creation. Idempotent; safe to run on every boot.

Called from a FastAPI startup event in main.py. Logs success/failure with
static prefixes only — the connection string is never included in any log line.
"""
from __future__ import annotations

import logging

from backend.app.db.base import Base
from backend.app.db.session import engine

# Importing models registers them on Base.metadata so create_all sees every table.
from backend.app.db.models import (  # noqa: F401
    corpus,
    corpus_file,
    evaluation_result,
    evaluation_run,
)

logger = logging.getLogger(__name__)


def init_db() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(
            "DB schema ready (evaluation_runs, evaluation_results, corpora, corpus_files)"
        )
    except Exception as exc:
        # Static prefix; we surface the class + message but never the URL.
        logger.error("DB init failed: %s: %s", type(exc).__name__, exc)
        raise
