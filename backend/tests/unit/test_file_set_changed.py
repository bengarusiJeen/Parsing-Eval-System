"""Unit tests for the effective-set comparison used to compute file_set_changed."""
from __future__ import annotations

from backend.app.service.timeline_service import _effective_set


def test_no_filter_uses_full_selected_set():
    s = _effective_set(["a", "b", "c"], None)
    assert s == frozenset({"a", "b", "c"})


def test_filter_intersects_with_requested():
    s = _effective_set(["a", "b", "c", "d"], {"b", "d", "z"})
    assert s == frozenset({"b", "d"})


def test_filter_yields_empty_when_no_overlap():
    s = _effective_set(["a", "b"], {"c"})
    assert s == frozenset()


def test_effective_sets_equal_avoids_false_positive():
    # Two runs with different full selections but identical intersection with the
    # requested filter — the chart was computed over the same docs.
    run_a = ["x", "y", "z"]
    run_b = ["x", "z", "extra"]
    requested = {"x", "z"}
    a = _effective_set(run_a, requested)
    b = _effective_set(run_b, requested)
    assert a == b  # file_set_changed should be False between these two points


def test_effective_sets_differ_when_intersection_actually_changes():
    run_a = ["x", "y"]
    run_b = ["y", "z"]
    requested = {"x", "y", "z"}
    a = _effective_set(run_a, requested)
    b = _effective_set(run_b, requested)
    assert a != b
