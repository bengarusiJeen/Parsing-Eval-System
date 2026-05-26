"""Unit tests for counts-based timeline aggregation."""
from __future__ import annotations

from dataclasses import dataclass

from backend.app.service.timeline_service import aggregate_run_score


@dataclass
class FakeRow:
    coverage_checked: int
    coverage_failed: int
    noise_checked: int
    noise_failed: int


def test_aggregate_uses_counts_not_naive_rate_average():
    # Two docs:
    # doc1: 100 ngrams checked, 10 failed -> rate = 0.90
    # doc2: 1000 ngrams checked, 500 failed -> rate = 0.50
    # Naive average of rates = (0.90 + 0.50)/2 = 0.70 (wrong)
    # Counts-based   = 1 - (10+500)/(100+1000) = 1 - 510/1100 ≈ 0.5364 (correct)
    rows = [
        FakeRow(100, 10, 50, 5),
        FakeRow(1000, 500, 500, 200),
    ]
    coverage, noise, avg_score, doc_count = aggregate_run_score(rows)
    assert doc_count == 2
    assert abs(coverage - (1 - 510 / 1100)) < 1e-9
    # naive average would give 0.70 — confirm we did NOT get that
    assert abs(coverage - 0.70) > 0.10
    assert abs(noise - 205 / 550) < 1e-9
    assert avg_score is not None
    assert abs(avg_score - ((coverage + (1 - noise)) / 2)) < 1e-9


def test_aggregate_empty_returns_all_none():
    coverage, noise, avg_score, doc_count = aggregate_run_score([])
    assert coverage is None
    assert noise is None
    assert avg_score is None
    assert doc_count == 0


def test_aggregate_zero_denominator_returns_none_for_that_metric():
    rows = [FakeRow(0, 0, 10, 1)]
    coverage, noise, avg_score, _ = aggregate_run_score(rows)
    assert coverage is None
    assert noise == 0.1
    # avg_score skipped because one side is None
    assert avg_score is None
