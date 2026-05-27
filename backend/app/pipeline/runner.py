"""
runner.py
---------
In-process pipeline runner with parser-level concurrency (Stage 6A).

The same code that the CLI runs also runs inside the FastAPI worker — no
subprocess. ``run_pipeline`` iterates documents serially inside each parser
(per-parser concurrency is locked at 1 in Stage 6A) but runs different
parsers in parallel via a ``ThreadPoolExecutor``. Results are grouped by
``parser_method`` so output is deterministic regardless of which parser
finishes first.

Concurrency knob (Stage 6A):

    EVAL_PARSER_CONCURRENCY (env)
        Caps how many parsers may run in parallel. Defaults to
        ``EVAL_PARSER_CONCURRENCY_CAP_DEFAULT`` (= 3). The effective value
        is ``min(env-or-default, len(parser_methods))``, with a floor of 1.

Per-parser concurrency is intentionally NOT exposed — Stage 6A keeps each
parser sequential internally. That decision lives in Stage 6B.
"""
from __future__ import annotations

import io
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Tuple

from backend.app.config.constants import (
    DEFAULT_PARSER_METHOD,
    EVAL_PARSER_CONCURRENCY_CAP_DEFAULT,
)
from backend.app.core.fs_utils import collect_files_dirs_to_test, find_document_file
from backend.app.core.paths import (
    DIAG_FILENAME,
    DIAG_PP_FILENAME,
    GENERAL_FILENAME,
    GENERAL_PP_FILENAME,
    per_parser_parsing_dir,
    per_parser_reports_dir,
)
from backend.app.core.substitutions import SubstitutionTable
from backend.app.models.document_models import EvaluationArtifacts
from backend.app.pipeline.cache import RunCache
from backend.app.pipeline.diagnostics import (
    DIAGNOSTICS_FILENAME,
    DIAGNOSTICS_PP_FILENAME,
    run_diagnostics,
)
from backend.app.pipeline.evaluator import evaluate_document
from backend.app.pipeline.json_reporter import save_json_report
from backend.app.pipeline.ocr import pre_test
from backend.app.pipeline.postprocessing import Postprocessing
from backend.app.pipeline.timing import phase
from backend.app.pipeline.types import ParserResult

# Type alias: the per-document parser sets that diagnostics consumes.
_ParserData = Tuple[Set[str], Set[str], Set[str], str]


@dataclass
class _RunRecord:
    """A document folder + the artifacts evaluate_document produced for it."""
    file_dir:  Path
    artifacts: EvaluationArtifacts


# ─────────────────────────────────────────────────────────────────────────────
# Thread-local stdout/stderr proxy
# ─────────────────────────────────────────────────────────────────────────────

class _ThreadLocalStream:
    """Drop-in replacement for ``sys.stdout`` / ``sys.stderr`` that routes
    each thread's writes to its own target stream when one is set, and
    falls through to the wrapped real stream otherwise.

    Why this exists: ``contextlib.redirect_stdout`` swaps ``sys.stdout``
    process-wide. With ``ThreadPoolExecutor`` running multiple parser
    workers concurrently, two threads racing the swap would corrupt each
    other's captured logs. This proxy is installed once by ``run_pipeline``
    (when capture is requested) and each worker thread calls ``set_target``
    / ``clear_target`` for its own per-parser buffer.

    Falls through transparently for non-worker threads (e.g. the main
    request thread or FastAPI's other handlers), so nothing else in the
    process is affected.
    """

    def __init__(self, fallback) -> None:
        self._fallback = fallback
        self._local    = threading.local()

    def _target(self):
        return getattr(self._local, "stream", None) or self._fallback

    def set_target(self, stream) -> None:
        self._local.stream = stream

    def clear_target(self) -> None:
        if hasattr(self._local, "stream"):
            del self._local.stream

    # ── File-like surface ──────────────────────────────────────────────────

    def write(self, s):
        return self._target().write(s)

    def flush(self):
        try:
            return self._target().flush()
        except Exception:
            return None

    def isatty(self):
        try:
            return self._fallback.isatty()
        except Exception:
            return False

    def fileno(self):
        return self._fallback.fileno()

    # Anything else (encoding, buffer, reconfigure, …) delegates to the
    # current target — keeps libraries that introspect sys.stderr happy.
    def __getattr__(self, name):
        return getattr(self._target(), name)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(
    input_dir:              Path,
    selected:               list[str],
    parser_methods:         list[str],
    *,
    include_postprocessing: bool = False,
    n:                      int  = 3,
    capture_output:         bool = False,
    general_filename:       str  = GENERAL_FILENAME,
) -> dict[str, ParserResult]:
    """Run the evaluation pipeline in-process for one or more parsers.

    Different parser methods run in parallel (Stage 6A); inside each parser,
    documents are processed serially. The returned dict is keyed by
    ``parser_method`` and ordered to match the input ``parser_methods`` list
    — order does NOT depend on which parser finished first.

    Args:
        input_dir              Folder containing one subfolder per document.
        selected               Document folder names to include. Empty = all.
        parser_methods         Ordered list of parser_method strings.
        include_postprocessing If True, run Pass 2 (postprocessing evaluation)
                                after Pass 1 for every parser. Default off.
        n                      N-gram size for coverage. Default 3.
        capture_output         When True, redirect each parser worker's
                                stdout/stderr into the matching ParserResult.
                                CLI passes False so output flows to the user's
                                terminal; the service passes True so it can
                                surface logs to the frontend.
        general_filename       Basename of the general report file inside the
                                per-parser subfolder. Defaults to
                                ``general_report.json``.

    Side effects:
        Writes ``reports/<parser>/general_report.json``, ``diagnostics_report.json``,
        and (if PP requested) the two ``postprocessing-*`` siblings. Writes
        raw + PP text to ``data/parsing_results/<parser>/``. Each parser's
        previous outputs in those subfolders are wiped up front so PP-on→PP-off
        transitions don't leak stale files.
    """
    # Resolve a single SubstitutionTable for the whole run — it's identical
    # across parsers and across both passes.
    sub_table = SubstitutionTable.load(
        Path(__file__).parent.parent / "core" / "substitutions.json"
    )

    # Validate input_dir gracefully. We can't SystemExit from inside a FastAPI
    # worker; return per-parser errors instead.
    if not input_dir.exists() or not input_dir.is_dir():
        msg = f"Input folder not found or not a directory: {input_dir}"
        return {p: ParserResult(parser_method=p, error=msg) for p in parser_methods}

    # Install thread-local stdout/stderr proxies once for the whole call.
    # Worker threads set their own per-parser targets inside _run_one_parser;
    # non-worker threads fall through to the real streams unchanged.
    proxy_installed = False
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    if capture_output:
        sys.stdout = _ThreadLocalStream(original_stdout)
        sys.stderr = _ThreadLocalStream(original_stderr)
        proxy_installed = True

    try:
        with phase("pipeline_total",
                   parsers=len(parser_methods),
                   docs=len(selected),
                   postprocessing=include_postprocessing):

            # pre_test is input_dir-scoped, not parser-scoped — run it once for
            # the whole request. Failures inside pre_test are best-effort.
            with phase("pre_test"):
                try:
                    pre_test(input_dir)
                except Exception as exc:
                    print(f"[warn] pre_test failed: {exc}", file=sys.stderr)

            files_dirs = collect_files_dirs_to_test(input_dir)
            if selected:
                include_set = {name.strip() for name in selected if name and name.strip()}
                files_dirs = [d for d in files_dirs if d.name in include_set]

            if not files_dirs:
                msg = "No matching document folders found."
                return {p: ParserResult(parser_method=p, error=msg) for p in parser_methods}

            # Stage 5 + 6A: one cache for the whole request. We pre-load GT and
            # document bytes on the main thread BEFORE spawning workers, so the
            # cache is read-only from worker threads (no locks needed).
            cache = RunCache()
            _preload_cache(cache, files_dirs, n)

            # Stage 6A: parser-level concurrency. Effective workers =
            # min(env cap, number of parsers). One task per parser_method;
            # each task drives its documents serially.
            workers = _resolve_parser_concurrency(len(parser_methods))

            collected: dict[str, ParserResult] = {}
            with ThreadPoolExecutor(max_workers=workers,
                                    thread_name_prefix="eval-parser") as pool:
                futures = {
                    pool.submit(
                        _run_one_parser,
                        parser_method,
                        files_dirs,
                        sub_table,
                        n=n,
                        include_postprocessing=include_postprocessing,
                        capture_output=capture_output,
                        general_filename=general_filename,
                        cache=cache,
                    ): parser_method
                    for parser_method in parser_methods
                }
                for future in as_completed(futures):
                    parser_method = futures[future]
                    try:
                        collected[parser_method] = future.result()
                    except BaseException as exc:
                        # Defensive: _run_one_parser already catches its own
                        # exceptions, but a thread-pool internal failure or
                        # KeyboardInterrupt could still surface here. One
                        # parser's failure must never crash the whole run.
                        collected[parser_method] = ParserResult(
                            parser_method=parser_method,
                            error=f"Worker crashed: {exc}",
                        )

        # Re-order to match the caller's parser_methods list so the response
        # shape is deterministic regardless of completion order.
        return {pm: collected[pm] for pm in parser_methods}

    finally:
        if proxy_installed:
            sys.stdout = original_stdout
            sys.stderr = original_stderr


# ─────────────────────────────────────────────────────────────────────────────
# Concurrency resolver
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_parser_concurrency(num_parsers: int) -> int:
    """Effective parser-pool size for this run.

    ``min(env cap, num_parsers)``, with a floor of 1 and a sane fallback if
    the env var is malformed.
    """
    env_val = os.getenv("EVAL_PARSER_CONCURRENCY", "").strip()
    cap: int
    if env_val:
        try:
            cap = max(1, int(env_val))
        except ValueError:
            cap = EVAL_PARSER_CONCURRENCY_CAP_DEFAULT
    else:
        cap = EVAL_PARSER_CONCURRENCY_CAP_DEFAULT
    return max(1, min(cap, num_parsers))


# ─────────────────────────────────────────────────────────────────────────────
# Cache preload — runs on the main thread before workers spawn
# ─────────────────────────────────────────────────────────────────────────────

def _preload_cache(cache: RunCache, files_dirs: list[Path], n: int) -> None:
    """Load GT artifacts and document bytes for every doc serially, on the
    main thread, so the cache is read-only when worker threads access it.

    Preload errors are warnings only — the per-parser worker will surface the
    real exception with the correct parser context.
    """
    with phase("preload_cache", docs=len(files_dirs)):
        for file_dir in files_dirs:
            try:
                cache.gt_artifacts(file_dir, n)
            except Exception as exc:
                print(f"[warn] preload GT failed for {file_dir.name}: {exc}",
                      file=sys.stderr)
            try:
                test_file = find_document_file(file_dir)
                cache.doc_bytes(test_file)
            except Exception as exc:
                print(f"[warn] preload bytes failed for {file_dir.name}: {exc}",
                      file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
# Per-parser worker (runs on a ThreadPoolExecutor thread)
# ─────────────────────────────────────────────────────────────────────────────

def _run_one_parser(
    parser_method:          str,
    files_dirs:             list[Path],
    sub_table:              SubstitutionTable,
    *,
    n:                      int,
    include_postprocessing: bool,
    capture_output:         bool,
    general_filename:       str,
    cache:                  RunCache,
) -> ParserResult:
    """Run Pass 1 (and optionally Pass 2) for a single parser_method.

    Stage 6A: this function runs in a worker thread when more than one
    parser is selected. Each call wipes its own per-parser report files,
    writes to its own per-parser folder under reports/ and parsing_results/,
    and captures its own stdout/stderr through the thread-local proxy.
    Other parsers running in sibling threads are fully isolated.
    """
    with phase("per_parser", parser=parser_method):
        parser_reports_dir = per_parser_reports_dir(parser_method)
        parser_reports_dir.mkdir(parents=True, exist_ok=True)
        _wipe_parser_reports(parser_method)

        stdout_buf: Optional[io.StringIO] = io.StringIO() if capture_output else None
        stderr_buf: Optional[io.StringIO] = io.StringIO() if capture_output else None

        error_msg: Optional[str] = None
        try:
            if capture_output:
                # sys.stdout / sys.stderr are the _ThreadLocalStream proxies
                # installed by run_pipeline. Setting the per-thread target
                # routes prints from this worker into its own buffer without
                # touching sibling parser threads.
                sys.stdout.set_target(stdout_buf)   # type: ignore[union-attr]
                sys.stderr.set_target(stderr_buf)   # type: ignore[union-attr]

            try:
                _do_pipeline_work(
                    parser_method=parser_method,
                    files_dirs=files_dirs,
                    sub_table=sub_table,
                    n=n,
                    include_postprocessing=include_postprocessing,
                    parser_reports_dir=parser_reports_dir,
                    general_filename=general_filename,
                    cache=cache,
                )
            except Exception as exc:
                # Per-doc try/except inside _do_pipeline_work normally swallows
                # document-level failures. Anything that escapes that becomes a
                # whole-parser error so sibling parsers keep running.
                error_msg = str(exc)
        finally:
            if capture_output:
                sys.stdout.clear_target()   # type: ignore[union-attr]
                sys.stderr.clear_target()   # type: ignore[union-attr]

        reports = _load_parser_reports(parser_method, general_filename=general_filename)

        # Treat "no general report produced" as a parser-level error —
        # matches the subprocess-path check in EvaluationService.
        if error_msg is None and reports["general"] is None:
            error_msg = (
                "No report was produced — every document failed to parse. "
                "See the log for the per-document cause "
                "(e.g. parser unavailable, unsupported file type, or rate limit)."
            )

        return ParserResult(
            parser_method = parser_method,
            general       = reports["general"],
            diagnostic    = reports["diagnostic"],
            general_pp    = reports["general_pp"],
            diagnostic_pp = reports["diagnostic_pp"],
            stdout        = stdout_buf.getvalue() if stdout_buf is not None else "",
            stderr        = stderr_buf.getvalue() if stderr_buf is not None else "",
            error         = error_msg,
        )


def _do_pipeline_work(
    *,
    parser_method:          str,
    files_dirs:             list[Path],
    sub_table:              SubstitutionTable,
    n:                      int,
    include_postprocessing: bool,
    parser_reports_dir:     Path,
    general_filename:       str,
    cache:                  RunCache,
) -> None:
    """Run Pass 1 + (optional) Pass 2 for one parser. Writes reports to disk."""

    # ── Pass 1 — raw evaluation ─────────────────────────────────────────────
    run_records: List[_RunRecord] = []
    with phase("raw_pass", parser=parser_method, docs=len(files_dirs)):
        for file_dir in files_dirs:
            try:
                artifacts = evaluate_document(
                    file_dir, n=n, sub_table=sub_table,
                    parser_method=parser_method, cache=cache,
                )
                run_records.append(_RunRecord(file_dir=file_dir, artifacts=artifacts))
            except NotImplementedError as e:
                # Fatal-class signal the CLI used to SystemExit on. In-process
                # we re-raise so _run_one_parser captures it as the parser's
                # ParserResult.error and sibling parsers keep running.
                print(f"\n[!] {e}", file=sys.stderr)
                raise
            except Exception as e:
                print(f"[error] {file_dir.name}: {e}", file=sys.stderr)

    results      = [r.artifacts.result for r in run_records]
    parser_data: List[_ParserData] = [
        (r.artifacts.parser_ngrams_set,
         r.artifacts.parser_words_set,
         r.artifacts.parser_bigrams_set,
         r.artifacts.file_ext)
        for r in run_records
    ]

    if results:
        with phase("write_general_report", parser=parser_method):
            save_json_report(results, parser_reports_dir / general_filename, n=n)
        with phase("run_diagnostics", parser=parser_method, pp=False):
            run_diagnostics(
                results,
                parser_data,
                output_filename=DIAGNOSTICS_FILENAME,
                output_dir=parser_reports_dir,
            )

    # ── Pass 2 — postprocessing evaluation (optional) ───────────────────────
    if not include_postprocessing:
        return

    with phase("pp_pass", parser=parser_method, docs=len(run_records)):
        pp = Postprocessing()
        pp_text_dir = per_parser_parsing_dir(parser_method)
        pp_text_dir.mkdir(parents=True, exist_ok=True)

        pp_run_records: List[_RunRecord] = []
        for record in run_records:
            try:
                artifacts_pp = evaluate_document(
                    record.file_dir,
                    n=n,
                    postprocessor=pp,
                    _parser_text=record.artifacts.raw_parser_text,
                    sub_table=sub_table,
                    cache=cache,
                )
                pp_run_records.append(_RunRecord(file_dir=record.file_dir, artifacts=artifacts_pp))

                if artifacts_pp.postprocessed_text is not None:
                    out_file = pp_text_dir / f"{record.file_dir.name}_after_post.txt"
                    out_file.write_text(artifacts_pp.postprocessed_text, encoding="utf-8")
            except Exception as e:
                print(f"[warn] Postprocessing failed for {record.file_dir.name}: {e}",
                      file=sys.stderr)

    results_pp     = [r.artifacts.result for r in pp_run_records]
    parser_data_pp: List[_ParserData] = [
        (r.artifacts.parser_ngrams_set,
         r.artifacts.parser_words_set,
         r.artifacts.parser_bigrams_set,
         r.artifacts.file_ext)
        for r in pp_run_records
    ]

    if results_pp:
        pp_basename = "postprocessing-" + general_filename
        with phase("write_pp_general_report", parser=parser_method):
            save_json_report(results_pp, parser_reports_dir / pp_basename, n=n)
        with phase("run_diagnostics", parser=parser_method, pp=True):
            run_diagnostics(
                results_pp,
                parser_data_pp,
                output_filename=DIAGNOSTICS_PP_FILENAME,
                output_dir=parser_reports_dir,
            )


# ─────────────────────────────────────────────────────────────────────────────
# File I/O helpers (kept local so the runner has no service-layer dependencies)
# ─────────────────────────────────────────────────────────────────────────────

def _wipe_parser_reports(parser_method: str) -> None:
    """Delete this parser's previous report files (raw + PP). Best-effort."""
    parser_dir = per_parser_reports_dir(parser_method)
    for name in (GENERAL_FILENAME, DIAG_FILENAME, GENERAL_PP_FILENAME, DIAG_PP_FILENAME):
        try:
            (parser_dir / name).unlink(missing_ok=True)
        except OSError:
            pass


def _load_parser_reports(parser_method: str, *, general_filename: str) -> dict:
    """Read the four JSON files this parser just wrote into a dict."""
    parser_dir = per_parser_reports_dir(parser_method)
    pp_basename = "postprocessing-" + general_filename

    def _load(name: str) -> dict | None:
        p = parser_dir / name
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError):
            return None

    return {
        "general":       _load(general_filename),
        "diagnostic":    _load(DIAGNOSTICS_FILENAME),
        "general_pp":    _load(pp_basename),
        "diagnostic_pp": _load(DIAGNOSTICS_PP_FILENAME),
    }


# Make the default parser_method discoverable for callers that want it.
__all__ = ["run_pipeline", "DEFAULT_PARSER_METHOD"]
