"""
json_reporter.py
----------------
JSON report serialization for the evaluation pipeline.
The only consumer of evaluation results is the backend/frontend — no console output.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from backend.app.models.document_models import BlockResult, DocumentResult


def _ngram_label(n: int) -> str:
    names = {1: "unigrams", 2: "bigrams", 3: "trigrams", 4: "fourgrams",
             5: "fivegrams", 6: "sixgrams", 7: "sevengrams", 8: "eightgrams"}
    return names.get(n, f"{n}-grams")


def save_json_report(results: List[DocumentResult], path: Path, n: int = 3) -> None:

    def _block(br: BlockResult) -> dict:
        return {
            "block_index": br.block_index,
            "coverage": {
                "unique_ngrams_checked_count":       br.coverage_block_score.checked,
                "missing_unique_ngrams_count":       br.coverage_block_score.failed,
                "coverage_rate":                     br.coverage_block_score.rate,
                "total_missing_unique_ngrams_ratio": br.coverage_block_score.fraction,
            },
            f"missing_{_ngram_label(n)}_in_block": br.missing_words,
        }

    def _doc(r: DocumentResult) -> dict:
        return {
            "doc_name": r.doc_name,
            "coverage": {
                "coverage_rate":                     r.coverage_pct,
                "unique_ngrams_checked_count":       r.coverage_score.checked,
                "missing_unique_ngrams_count":       r.coverage_score.failed,
                "total_missing_unique_ngrams_ratio": r.coverage_score.fraction,
            },
            "noise": {
                "unique_parser_words_checked": r.noise_score.checked,
                "noise_words_count":           r.noise_score.failed,
                "noise_words":                 r.extra_words,
                "noise_rate":                  r.noise_pct,
                "noise_ratio":                 r.noise_score.fraction,
            },
            "gt_total_words_non_unique":     r.gt_word_count,
            "parser_total_words_non_unique": r.parser_word_count,
            "block_results":                [_block(br) for br in r.block_results],
        }

    doc_count = len(results)
    summary = {
        "documents_evaluated": doc_count,
        "avg_coverage_rate":   round(sum(r.coverage_pct for r in results) / doc_count, 4),
        "avg_noise_rate":      round(sum(r.noise_pct    for r in results) / doc_count, 4),
    }

    report = {
        "summary":   summary,
        "documents": [_doc(r) for r in results],
    }

    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[✓] JSON report saved to {path}")
