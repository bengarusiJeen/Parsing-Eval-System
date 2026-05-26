"""Unit tests for the normalize+warn weighting policy used by the overall timeline."""
from __future__ import annotations

from backend.app.service.timeline_service import weighted_overall


def test_ratios_sum_to_one_no_warning():
    # Three corpora, ratios sum exactly to 1.0, all contribute.
    overall, ratios_sum, normalized, warning = weighted_overall(
        corpus_scores=[(0.5, 0.80), (0.3, 0.60), (0.2, 0.40)],
        all_active_ratios=[0.5, 0.3, 0.2],
    )
    # 0.5*0.80 + 0.3*0.60 + 0.2*0.40 = 0.40 + 0.18 + 0.08 = 0.66
    assert abs(overall - 0.66) < 1e-9
    assert abs(ratios_sum - 1.0) < 1e-9
    assert normalized is True
    assert warning is None


def test_ratios_drift_triggers_warning_but_score_still_in_range():
    # Ratios sum to 1.5; score must be normalized so the headline stays in [0,1].
    overall, ratios_sum, normalized, warning = weighted_overall(
        corpus_scores=[(0.75, 1.0), (0.75, 0.0)],
        all_active_ratios=[0.75, 0.75],
    )
    # contributing_sum = 1.5; weighted = (0.75/1.5)*1.0 + (0.75/1.5)*0.0 = 0.5
    assert abs(overall - 0.5) < 1e-9
    assert abs(ratios_sum - 1.5) < 1e-9
    assert normalized is True
    assert warning is not None
    assert "1.5000" in warning


def test_missing_corpus_drops_out_and_normalization_uses_only_contributors():
    # Corpus B has no data this run → exclude it; normalize using A + C only.
    overall, ratios_sum, normalized, warning = weighted_overall(
        corpus_scores=[(0.5, 0.90), (0.3, None), (0.2, 0.50)],
        all_active_ratios=[0.5, 0.3, 0.2],
    )
    # contributing_sum = 0.5 + 0.2 = 0.7
    # weighted = (0.5/0.7)*0.90 + (0.2/0.7)*0.50
    expected = (0.5 / 0.7) * 0.90 + (0.2 / 0.7) * 0.50
    assert abs(overall - expected) < 1e-9
    # ratios_sum is over ALL active corpora, not just contributors
    assert abs(ratios_sum - 1.0) < 1e-9
    assert normalized is True
    assert warning is None


def test_no_contributors_returns_none():
    overall, ratios_sum, normalized, warning = weighted_overall(
        corpus_scores=[(0.5, None), (0.5, None)],
        all_active_ratios=[0.5, 0.5],
    )
    assert overall is None
    assert ratios_sum == 1.0
    assert normalized is False
    assert warning is None


def test_drift_within_tolerance_no_warning():
    overall, ratios_sum, normalized, warning = weighted_overall(
        corpus_scores=[(0.495, 0.8), (0.505, 0.6)],
        all_active_ratios=[0.495, 0.505],
    )
    assert abs(ratios_sum - 1.0) <= 0.01
    assert warning is None
    assert overall is not None
