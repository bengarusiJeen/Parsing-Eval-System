"""
types.py
--------
Lightweight result types for the in-process pipeline runner.

Stage 4 of the perf refactor: the runner returns one ``ParserResult`` per
parser_method. The service layer reshapes these into the existing
``/api/evaluate`` response dict so the frontend contract stays unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ParserResult:
    """One parser's outputs from a single ``run_pipeline`` call.

    The four ``general``/``diagnostic``/``general_pp``/``diagnostic_pp`` fields
    are exactly the JSON shapes the frontend already consumes (or ``None`` when
    that report wasn't produced — e.g. PP is null when ``include_postprocessing``
    is False, or when every doc failed to parse).

    ``stdout`` / ``stderr`` capture what the pipeline wrote during this parser's
    execution (when the caller asked the runner to capture output). They mirror
    the subprocess fields the service used to read off ``proc.stdout`` /
    ``proc.stderr`` so the response shape is unchanged.

    ``error`` is set only on a whole-parser fatal: the run produced no general
    report (every document failed), or a top-level exception escaped the runner.
    Per-document failures are visible via the missing entries in ``general``
    and via the warning lines in ``stderr``.
    """
    parser_method: str
    general:       dict | None = None
    diagnostic:    dict | None = None
    general_pp:    dict | None = None
    diagnostic_pp: dict | None = None
    stdout:        str = ""
    stderr:        str = ""
    error:         str | None = None
