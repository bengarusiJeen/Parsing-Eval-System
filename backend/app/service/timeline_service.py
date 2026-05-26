"""
backend/app/service/timeline_service.py
-----------------------------------------
Builds parser quality timelines from persisted evaluation_results.

Aggregation is counts-based — coverage = 1 - sum(failed)/sum(checked) — never
a naive average of per-document rates. The shared aggregator is reused by the
parser, corpus, and overall (weighted) timelines so the math is not duplicated.

Overall-timeline ratio policy: NORMALIZE + WARN. Per timeline point we divide
each contributing corpus's configured ratio by the sum of contributing ratios,
keeping the headline score in [0,1] and comparable across configurations.
A `warning` field surfaces ratio drift > 0.01.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable

from sqlalchemy.orm import Session

from backend.app.db.models.evaluation_result import EvaluationResult
from backend.app.db.models.evaluation_run import EvaluationRun
from backend.app.repositories.corpus_repository import CorpusRepository
from backend.app.repositories.evaluation_history_repository import (
    EvaluationHistoryRepository,
)
from backend.app.schemas.corpus import (
    OverallTimelinePoint,
    OverallTimelineResponse,
)
from backend.app.schemas.history import (
    TimelineFilterEcho,
    TimelinePoint,
    TimelineResponse,
)

RATIO_DRIFT_TOLERANCE = 0.01


# ── pure aggregation helpers (testable without DB) ─────────────────────────────

def aggregate_run_score(
    rows: list[EvaluationResult],
) -> tuple[float | None, float | None, float | None, int]:
    """Return (coverage, noise, avg_score, doc_count) for a slice of rows.

    Counts-based: sums checked/failed across rows. Returns None for the rate
    when its denominator is 0; avg_score is None if either rate is None.
    """
    if not rows:
        return None, None, None, 0

    sum_cov_checked = sum(r.coverage_checked for r in rows)
    sum_cov_failed = sum(r.coverage_failed for r in rows)
    sum_noise_checked = sum(r.noise_checked for r in rows)
    sum_noise_failed = sum(r.noise_failed for r in rows)

    coverage = (
        1.0 - (sum_cov_failed / sum_cov_checked)
        if sum_cov_checked > 0
        else None
    )
    noise = (
        sum_noise_failed / sum_noise_checked
        if sum_noise_checked > 0
        else None
    )
    avg_score = (
        (coverage + (1.0 - noise)) / 2.0
        if coverage is not None and noise is not None
        else None
    )
    return coverage, noise, avg_score, len(rows)


def _effective_set(
    run_selected: list[str],
    requested_filter: set[str] | None,
) -> frozenset[str]:
    """Compute the effective file set for one timeline point.

    - No filter         → set(run_selected)
    - Files filter      → set(run_selected) ∩ requested_filter
    - Corpus filter     → set(run_selected) ∩ active_corpus_files (same logic)
    """
    base = set(run_selected or [])
    if requested_filter is None:
        return frozenset(base)
    return frozenset(base & requested_filter)


def weighted_overall(
    corpus_scores: list[tuple[float, float | None]],
    all_active_ratios: list[float],
) -> tuple[float | None, float, bool, str | None]:
    """Combine per-corpus scores with normalize-and-warn ratio handling.

    Args:
        corpus_scores: list of (ratio, score) — score is None if a corpus had
            no aggregable data for this run; only entries with a non-None score
            actually contribute.
        all_active_ratios: ratios of every active corpus in the configuration
            (regardless of whether it contributed). Used to compute the
            ratios_sum that drives the warning.

    Returns: (overall_score, ratios_sum, normalization_applied, warning).
    overall_score is None if no corpus contributed.
    """
    contributing = [(ratio, score) for ratio, score in corpus_scores if score is not None]
    ratios_sum = sum(all_active_ratios)

    warning: str | None = None
    if abs(ratios_sum - 1.0) > RATIO_DRIFT_TOLERANCE:
        warning = (
            f"Configured corpus overall_ratio values sum to {ratios_sum:.4f}, "
            "not 1.0; scores have been normalized so the chart stays comparable."
        )

    if not contributing:
        return None, ratios_sum, False, warning

    contributing_sum = sum(ratio for ratio, _ in contributing)
    if contributing_sum <= 0:
        # All contributing corpora have ratio 0 → can't weight; return None.
        return None, ratios_sum, False, warning

    overall = sum((ratio / contributing_sum) * score for ratio, score in contributing)
    return overall, ratios_sum, True, warning


# ── service ───────────────────────────────────────────────────────────────────

class TimelineService:
    def __init__(
        self,
        repository: EvaluationHistoryRepository,
        corpus_repository: CorpusRepository,
        session_factory: Callable[[], Session],
    ) -> None:
        self._repo = repository
        self._corpus_repo = corpus_repository
        self._session_factory = session_factory

    # ── parser timeline (Stage 1) ────────────────────────────────────────────

    def get_parser_timeline(
        self,
        parser_name: str,
        file_names: list[str] | None,
        limit: int,
    ) -> TimelineResponse:
        files_set: set[str] | None = set(file_names) if file_names else None

        db = self._session_factory()
        try:
            run_ids = self._repo.get_recent_run_ids_with_results(
                db, parser_name=parser_name, file_names=files_set, limit=limit,
            )
            if not run_ids:
                return TimelineResponse(
                    points=[],
                    filter_echo=TimelineFilterEcho(
                        parser=parser_name,
                        files=file_names if file_names else None,
                    ),
                )
            runs = self._repo.get_runs_by_ids(db, run_ids)
            rows = self._repo.get_results_for_runs(
                db, parser_name=parser_name, file_names=files_set, run_ids=run_ids,
            )
        finally:
            db.close()

        points = self._build_timeline_points(
            parser_name=parser_name,
            run_ids=run_ids,
            runs=runs,
            rows=rows,
            effective_filter=files_set,
        )
        return TimelineResponse(
            points=points,
            filter_echo=TimelineFilterEcho(
                parser=parser_name,
                files=file_names if file_names else None,
            ),
        )

    # ── corpus timeline (Stage 2) ────────────────────────────────────────────

    def get_corpus_timeline(
        self,
        parser_name: str,
        corpus_id: int,
        limit: int,
    ) -> TimelineResponse | None:
        """Same shape as the parser timeline but the file filter comes from
        the corpus's active file list. Returns None if the corpus doesn't exist."""
        db = self._session_factory()
        try:
            corpus = self._corpus_repo.get_corpus(db, corpus_id)
            if corpus is None:
                return None
            active_files = self._corpus_repo.get_active_file_names(db, corpus_id)
            files_set: set[str] | None = set(active_files) if active_files else set()

            # If the corpus has no active files, there can't be any matching
            # results — return an empty timeline rather than running a JOIN.
            if not files_set:
                return TimelineResponse(
                    points=[],
                    filter_echo=TimelineFilterEcho(
                        parser=parser_name,
                        files=sorted(active_files),
                    ),
                )

            run_ids = self._repo.get_recent_run_ids_with_results(
                db, parser_name=parser_name, file_names=files_set, limit=limit,
            )
            if not run_ids:
                return TimelineResponse(
                    points=[],
                    filter_echo=TimelineFilterEcho(
                        parser=parser_name,
                        files=sorted(active_files),
                    ),
                )
            runs = self._repo.get_runs_by_ids(db, run_ids)
            rows = self._repo.get_results_for_runs(
                db, parser_name=parser_name, file_names=files_set, run_ids=run_ids,
            )
        finally:
            db.close()

        points = self._build_timeline_points(
            parser_name=parser_name,
            run_ids=run_ids,
            runs=runs,
            rows=rows,
            effective_filter=files_set,
        )
        return TimelineResponse(
            points=points,
            filter_echo=TimelineFilterEcho(
                parser=parser_name,
                files=sorted(active_files),
            ),
        )

    # ── overall weighted timeline (Stage 2) ──────────────────────────────────

    def get_overall_timeline(
        self,
        parser_name: str,
        limit: int,
    ) -> OverallTimelineResponse:
        """Per-run weighted score across every active corpus.

        Picks runs that have results for the parser on the union of all active
        corpus files, then per-run aggregates each corpus separately and
        combines with normalize+warn weighting.
        """
        db = self._session_factory()
        try:
            corpora = self._corpus_repo.list_active_corpora_with_files(db)
            # Build per-corpus active-file sets and the union for the run query.
            corpus_file_sets: list[tuple[str, float, set[str]]] = []
            union: set[str] = set()
            for c in corpora:
                files = {f.file_name for f in c.files if f.is_active}
                if not files:
                    continue
                corpus_file_sets.append((c.name, c.overall_ratio, files))
                union |= files

            if not corpus_file_sets or not union:
                return OverallTimelineResponse(points=[], parser=parser_name)

            run_ids = self._repo.get_recent_run_ids_with_results(
                db, parser_name=parser_name, file_names=union, limit=limit,
            )
            if not run_ids:
                return OverallTimelineResponse(points=[], parser=parser_name)
            runs = self._repo.get_runs_by_ids(db, run_ids)
            rows = self._repo.get_results_for_runs(
                db, parser_name=parser_name, file_names=union, run_ids=run_ids,
            )
        finally:
            db.close()

        runs_by_id: dict[int, EvaluationRun] = {r.id: r for r in runs}
        rows_by_run: dict[int, list[EvaluationResult]] = defaultdict(list)
        for row in rows:
            rows_by_run[row.run_id].append(row)

        ordered_ids = sorted(
            run_ids,
            key=lambda rid: (runs_by_id[rid].created_at, rid),
        )

        all_active_ratios = [ratio for _, ratio, _ in corpus_file_sets]

        points: list[OverallTimelinePoint] = []
        for rid in ordered_ids:
            run = runs_by_id.get(rid)
            if run is None:
                continue
            slice_rows = rows_by_run.get(rid, [])
            rows_by_file: dict[str, list[EvaluationResult]] = defaultdict(list)
            for r in slice_rows:
                rows_by_file[r.file_name].append(r)

            per_corpus: dict[str, float | None] = {}
            corpus_scores: list[tuple[float, float | None]] = []
            contributing = 0
            for name, ratio, files in corpus_file_sets:
                corpus_rows = [
                    r for fname in files for r in rows_by_file.get(fname, [])
                ]
                _, _, score, _ = aggregate_run_score(corpus_rows)
                per_corpus[name] = score
                corpus_scores.append((ratio, score))
                if score is not None:
                    contributing += 1

            overall, ratios_sum, normalized, warning = weighted_overall(
                corpus_scores, all_active_ratios
            )

            points.append(
                OverallTimelinePoint(
                    run_id=rid,
                    started_at=run.started_at,
                    overall_score=overall,
                    contributing_corpora=contributing,
                    ratios_sum=ratios_sum,
                    normalization_applied=normalized,
                    warning=warning,
                    per_corpus=per_corpus,
                )
            )

        return OverallTimelineResponse(points=points, parser=parser_name)

    # ── shared point builder ─────────────────────────────────────────────────

    def _build_timeline_points(
        self,
        *,
        parser_name: str,
        run_ids: list[int],
        runs: list[EvaluationRun],
        rows: list[EvaluationResult],
        effective_filter: set[str] | None,
    ) -> list[TimelinePoint]:
        runs_by_id: dict[int, EvaluationRun] = {r.id: r for r in runs}
        rows_by_run: dict[int, list[EvaluationResult]] = defaultdict(list)
        for row in rows:
            rows_by_run[row.run_id].append(row)

        ordered_ids = sorted(
            run_ids,
            key=lambda rid: (runs_by_id[rid].created_at, rid),
        )

        points: list[TimelinePoint] = []
        prev_effective: frozenset[str] | None = None
        for rid in ordered_ids:
            run = runs_by_id.get(rid)
            if run is None:
                continue
            slice_rows = rows_by_run.get(rid, [])
            coverage, noise, avg_score, doc_count = aggregate_run_score(slice_rows)

            effective = _effective_set(run.selected_files_json or [], effective_filter)
            changed = False if prev_effective is None else (effective != prev_effective)
            prev_effective = effective

            points.append(
                TimelinePoint(
                    run_id=rid,
                    started_at=run.started_at,
                    parser_name=parser_name,
                    coverage=coverage,
                    noise=noise,
                    avg_score=avg_score,
                    doc_count=doc_count,
                    file_set_changed=changed,
                )
            )
        return points
