"""Unit tests for the report extractor — pure function, no DB."""
from __future__ import annotations

from backend.app.service.evaluation_report_extractor import (
    extract_parser_document_results,
)


def _make_general(docs):
    return {"summary": {}, "documents": docs}


def _doc(name, cov_checked, cov_failed, cov_rate, n_checked, n_failed, n_rate,
         gt_words=100, parser_words=120):
    return {
        "doc_name": name,
        "coverage": {
            "unique_ngrams_checked_count": cov_checked,
            "missing_unique_ngrams_count": cov_failed,
            "coverage_rate": cov_rate,
            "total_missing_unique_ngrams_ratio": f"{cov_failed}/{cov_checked}",
        },
        "noise": {
            "unique_parser_words_checked": n_checked,
            "noise_words_count": n_failed,
            "noise_rate": n_rate,
        },
        "gt_total_words_non_unique": gt_words,
        "parser_total_words_non_unique": parser_words,
    }


def test_extract_basic_two_docs():
    general = _make_general([
        _doc("doc-a", 100, 20, 0.8, 50, 5, 0.10),
        _doc("doc-b", 200, 60, 0.7, 80, 16, 0.20),
    ])
    rows = extract_parser_document_results(general, None, "base_text_parser")

    assert len(rows) == 2
    a = rows[0]
    assert a.parser_name == "base_text_parser"
    assert a.file_name == "doc-a"
    assert a.coverage_checked == 100
    assert a.coverage_failed == 20
    assert a.coverage_rate == 0.8
    assert a.noise_checked == 50
    assert a.noise_failed == 5
    assert a.noise_rate == 0.10
    # avg_score = (0.8 + (1 - 0.10)) / 2 = 0.85
    assert abs(a.avg_score - 0.85) < 1e-9
    assert a.diagnostics_json is None


def test_extract_attaches_diagnostics_by_doc_name():
    general = _make_general([
        _doc("doc-a", 100, 20, 0.8, 50, 5, 0.10),
        _doc("doc-b", 200, 60, 0.7, 80, 16, 0.20),
    ])
    diagnostics = {
        "documents": [
            {"doc_name": "doc-b", "detected_problems": {"OCR_SPLIT": {"count": 2}}},
        ]
    }
    rows = extract_parser_document_results(general, diagnostics, "p")
    by_name = {r.file_name: r for r in rows}
    assert by_name["doc-a"].diagnostics_json is None
    assert by_name["doc-b"].diagnostics_json == {"OCR_SPLIT": {"count": 2}}


def test_extract_skips_docs_with_missing_fields():
    general = _make_general([
        _doc("good", 100, 20, 0.8, 50, 5, 0.10),
        {"doc_name": "bad", "coverage": {}, "noise": {}},  # missing required keys
    ])
    rows = extract_parser_document_results(general, None, "p")
    assert [r.file_name for r in rows] == ["good"]


def test_extract_returns_empty_for_missing_general():
    assert extract_parser_document_results(None, None, "p") == []
    assert extract_parser_document_results({}, None, "p") == []
    assert extract_parser_document_results({"documents": []}, None, "p") == []
