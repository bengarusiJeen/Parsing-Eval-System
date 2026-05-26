"""
backend/app/service/evaluation_report_extractor.py
----------------------------------------------------
Pure helpers that turn the two report JSON dicts (general + diagnostics)
written by the pipeline into persistence-ready rows for `evaluation_results`.

No DB access, no I/O — easy to unit-test against the on-disk report fixtures.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParserDocumentResult:
    """One row's worth of metrics for (parser, file) inside a run."""
    parser_name: str
    file_name: str
    coverage_checked: int
    coverage_failed: int
    coverage_rate: float
    noise_checked: int
    noise_failed: int
    noise_rate: float
    avg_score: float
    gt_word_count: int
    parser_word_count: int
    diagnostics_json: dict[str, Any] | None


def _build_diagnostics_lookup(diagnostics: dict | None) -> dict[str, dict]:
    """Build {doc_name: detected_problems} so we can attach diagnostics in O(1)."""
    if not diagnostics:
        return {}
    docs = diagnostics.get("documents") or []
    lookup: dict[str, dict] = {}
    for d in docs:
        name = d.get("doc_name")
        if not name:
            continue
        problems = d.get("detected_problems")
        if problems is not None:
            lookup[name] = problems
    return lookup


def extract_parser_document_results(
    general: dict | None,
    diagnostics: dict | None,
    parser_name: str,
) -> list[ParserDocumentResult]:
    """Iterate the general report and produce one row per evaluated document.

    Docs missing the required coverage/noise fields are skipped with a warning;
    the rest are returned. Returns an empty list if `general` is missing or has
    no `documents` key.
    """
    if not general:
        return []

    docs = general.get("documents") or []
    diag_lookup = _build_diagnostics_lookup(diagnostics)

    rows: list[ParserDocumentResult] = []
    for doc in docs:
        try:
            file_name = doc["doc_name"]
            coverage = doc["coverage"]
            noise = doc["noise"]

            coverage_checked = int(coverage["unique_ngrams_checked_count"])
            coverage_failed = int(coverage["missing_unique_ngrams_count"])
            coverage_rate = float(coverage["coverage_rate"])
            noise_checked = int(noise["unique_parser_words_checked"])
            noise_failed = int(noise["noise_words_count"])
            noise_rate = float(noise["noise_rate"])
            gt_word_count = int(doc["gt_total_words_non_unique"])
            parser_word_count = int(doc["parser_total_words_non_unique"])
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning(
                "Skipping document in parser=%s: missing/invalid field (%s)",
                parser_name, exc,
            )
            continue

        avg_score = (coverage_rate + (1.0 - noise_rate)) / 2.0

        rows.append(
            ParserDocumentResult(
                parser_name=parser_name,
                file_name=file_name,
                coverage_checked=coverage_checked,
                coverage_failed=coverage_failed,
                coverage_rate=coverage_rate,
                noise_checked=noise_checked,
                noise_failed=noise_failed,
                noise_rate=noise_rate,
                avg_score=avg_score,
                gt_word_count=gt_word_count,
                parser_word_count=parser_word_count,
                diagnostics_json=diag_lookup.get(file_name),
            )
        )

    return rows
