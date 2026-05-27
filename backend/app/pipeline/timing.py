"""
timing.py
---------
Minimal timing instrumentation for the evaluation pipeline.

Each ``phase()`` block emits one structured line to stderr when it exits:

    [timing] {"phase": "...", "ms": 12.3, "parser": "...", "doc": "..."}

The ``[timing]`` prefix lets EvaluationService strip these lines from the
``stderr`` field of the API response so they don't pollute the user-facing
log pane. Aggregate the lines manually (or with a small script) to see
where wall time goes.

Stage 1 of the perf refactor. No behavior change.
"""
from __future__ import annotations

import json
import sys
import time
from contextlib import contextmanager
from typing import Any, Iterator


TIMING_PREFIX = "[timing]"


@contextmanager
def phase(name: str, **labels: Any) -> Iterator[None]:
    """Time the wrapped block and emit a single stderr line on exit.

    The line is always emitted — even on exception — with an ``error`` label
    when the block raised, so we can see how long a failed phase ran for.
    """
    start = time.perf_counter()
    error: str | None = None
    try:
        yield
    except BaseException as exc:
        error = type(exc).__name__
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000.0
        payload: dict[str, Any] = {"phase": name, "ms": round(ms, 2)}
        for k, v in labels.items():
            if v is not None:
                payload[k] = v
        if error is not None:
            payload["error"] = error
        try:
            print(f"{TIMING_PREFIX} {json.dumps(payload, ensure_ascii=False)}",
                  file=sys.stderr, flush=True)
        except Exception:
            # Never let instrumentation break the pipeline.
            pass


def strip_timing_lines(text: str) -> str:
    """Remove ``[timing] ...`` lines from a captured stderr blob.

    Used by EvaluationService before assembling the API response so users
    don't see timing JSON in the log pane.
    """
    if not text or TIMING_PREFIX not in text:
        return text
    return "\n".join(
        line for line in text.splitlines() if not line.startswith(TIMING_PREFIX)
    )
