"""
cache.py
--------
Per-run caching for the in-process pipeline.

Stage 5 of the perf refactor: a multi-parser run sees identical GT and
identical document bytes for every parser. ``RunCache`` loads each of those
exactly once and hands the same object back on subsequent requests, scoped
to the lifetime of a single ``run_pipeline`` call (one HTTP request, one
CLI invocation).

Not thread-safe by design — Stage 5 keeps the runner synchronous. When
Stage 6 introduces concurrency it will either lock the cache or use a
per-thread variant; that decision belongs to Stage 6, not here.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

from backend.app.core.text_utils import _is_punct_token
from backend.app.pipeline import gt_loader
from backend.app.pipeline.timing import phase


@dataclass(frozen=True)
class GtArtifacts:
    """Parsed + tokenized GT for one document, already punctuation-stripped
    for the requested ``n``. Both fields are exactly the shapes
    ``evaluate_document`` used to build inline before this stage.
    """
    gt_blocks:        List[List[str]]
    all_gt_words_set: Set[str]


def _maybe_strip_punctuation_tokens(tokens: List[str], n: int) -> List[str]:
    """Mirror of ``evaluator._maybe_strip_punctuation_tokens``. Kept local so
    importing the cache doesn't pull in the evaluator (which imports the
    cache for its type hint, which would create a circular import).
    """
    if n <= 4:
        return tokens
    return [w for w in tokens if not _is_punct_token(w)]


class RunCache:
    """Dict-backed cache keyed by ``(file_dir, n)`` for GT, by ``file_path``
    for document bytes. Memory is bounded by the number of files in one run
    — at the corpus sizes this project handles (≤20 docs typical), this is
    a non-issue. If we ever push to hundreds of files, swap for an LRU.
    """

    def __init__(self) -> None:
        self._gt:    dict[tuple[Path, int], GtArtifacts] = {}
        self._bytes: dict[Path, bytes]                   = {}

    # ── GT ──────────────────────────────────────────────────────────────────

    def gt_artifacts(self, file_dir: Path, n: int) -> GtArtifacts:
        """Return the parsed + tokenized GT for ``file_dir`` (loads on miss).

        Wrapped in a ``gt_load`` timing phase that only fires on a cache miss
        — handy for the Stage 5 verification ("GT counted ~1× per doc per
        run, not 2× per parser per doc").
        """
        key = (file_dir, n)
        cached = self._gt.get(key)
        if cached is not None:
            return cached

        with phase("gt_load", doc=file_dir.name, n=n):
            gt_dir = file_dir / "GT"
            if not gt_dir.exists():
                raise FileNotFoundError(f"Missing GT/ subfolder in {file_dir}")

            gt_blocks = gt_loader.load_gt(gt_dir)
            gt_blocks = [_maybe_strip_punctuation_tokens(block, n) for block in gt_blocks]
            if not gt_blocks:
                print(f"[warn] {file_dir.name}: no ==== body blocks found in GT",
                      file=sys.stderr)

            all_gt_words_set: Set[str] = {w for block in gt_blocks for w in block}
            art = GtArtifacts(gt_blocks=gt_blocks, all_gt_words_set=all_gt_words_set)

        self._gt[key] = art
        return art

    # ── Document bytes ──────────────────────────────────────────────────────

    def doc_bytes(self, file_path: Path) -> bytes:
        """Return the raw bytes of ``file_path`` (reads on miss).

        Cuts ``N`` disk reads down to 1 when N parsers all process the same
        document, which is the common case for multi-parser evaluations.
        """
        cached = self._bytes.get(file_path)
        if cached is not None:
            return cached
        data = file_path.read_bytes()
        self._bytes[file_path] = data
        return data
