"""
backend/app/service/evaluation_service.py
--------------------------------------------
EvaluationService: runs the evaluation pipeline in-process (Stage 4 of the
perf refactor) and reshapes the result into the existing /api/evaluate
response. Receives a ReportService instance via constructor injection.

Set ``EVAL_USE_SUBPROCESS=1`` in the environment to fall back to the legacy
per-parser ``python -m backend.app.pipeline.cli`` subprocess path; this is a
rollback hatch and not the default.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys

from backend.app.config.constants import PIPELINE_MODULE, PIPELINE_SUBPROCESS_TIMEOUT
from backend.app.core.paths import FILES_DIR, GENERAL_JSON, ROOT
from backend.app.pipeline.runner import run_pipeline
from backend.app.pipeline.timing import phase, strip_timing_lines
from backend.app.pipeline.types import ParserResult
from backend.app.schemas.requests import EvaluateRequest
from backend.app.service.evaluation_history_service import EvaluationHistoryService
from backend.app.service.report_service import ReportService

logger = logging.getLogger(__name__)


def _use_subprocess() -> bool:
    """Rollback hatch — set EVAL_USE_SUBPROCESS=1 to keep the legacy path."""
    return os.getenv("EVAL_USE_SUBPROCESS", "").strip() not in ("", "0", "false", "False")


class EvaluationService:
    def __init__(
        self,
        report_service: ReportService,
        history_service: EvaluationHistoryService,
    ) -> None:
        self._reports = report_service
        self._history = history_service

    # ── Public entry point ─────────────────────────────────────────────────

    def run_evaluation(self, request: EvaluateRequest) -> dict:
        """Dispatch to single- or multi-parser evaluation.

        The full result is snapshotted to disk so the Results and Compare pages
        can restore per-parser data after a reload without re-running parsers.
        """
        parsers_list = request.parsers
        selected     = request.selected
        include_pp   = request.include_postprocessing

        # Stage 3: the flat reports/*.json files are only kept up-to-date for
        # single-parser runs. Wipe them up front so a multi-parser request
        # can't leave a stale flat copy from a previous single-parser run.
        self._reports.wipe_report_files()

        with phase("run_evaluation_total",
                   parsers=len(parsers_list), docs=len(selected), postprocessing=include_pp):
            if _use_subprocess():
                result = self._run_via_subprocess(parsers_list, selected, include_pp)
            else:
                result = self._run_in_process(parsers_list, selected, include_pp)

            # Backward-compat for any external reader of the flat report
            # paths: mirror the single-parser subfolder out to reports/*.
            if len(parsers_list) == 1:
                self._reports.copy_per_parser_to_flat(parsers_list[0])

            self._reports.save_last_run(result)

            # Best-effort DB persistence: a failure here must never break /api/evaluate.
            try:
                self._history.persist_evaluation(request, result)
            except Exception:
                logger.exception("History persistence failed; evaluation response unaffected")

        return result

    # ── In-process path (Stage 4 default) ──────────────────────────────────

    def _run_in_process(
        self,
        parsers_list: list[str],
        selected:     list[str],
        include_pp:   bool,
    ) -> dict:
        """Call the in-process runner once for all parsers and reshape."""
        bundle = run_pipeline(
            input_dir              = FILES_DIR,
            selected               = selected,
            parser_methods         = parsers_list,
            include_postprocessing = include_pp,
            capture_output         = True,
        )

        if len(parsers_list) == 1:
            p = parsers_list[0]
            result = self._shape_parser_result(bundle.get(p) or ParserResult(parser_method=p))
            # Tag the snapshot so /api/comparison/info can identify the parser
            # without the frontend having to track or send it back.
            result['_parser_id'] = p
            return result

        parser_results: dict[str, dict] = {}
        for p in parsers_list:
            parser_results[p] = self._shape_parser_result(
                bundle.get(p) or ParserResult(parser_method=p)
            )
        return {"multi_parser": True, "parsers": parser_results}

    @staticmethod
    def _shape_parser_result(pr: ParserResult) -> dict:
        """Reshape a ParserResult into the existing /api/evaluate dict shape.

        ``returncode`` / ``stdout`` / ``stderr`` are preserved as response keys
        so the frontend log pane and any consumer of those fields keep working
        — they're now virtual values populated from the in-process run.
        """
        produced = pr.general is not None
        ok       = pr.error is None and produced

        result: dict = {
            "status":     "ok" if ok else "error",
            "returncode": 0 if ok else 1,
            "stdout":     pr.stdout,
            "stderr":     strip_timing_lines(pr.stderr),
            "general":       pr.general,
            "diagnostic":    pr.diagnostic,
            "general_pp":    pr.general_pp,
            "diagnostic_pp": pr.diagnostic_pp,
        }
        if not ok:
            result["error"] = pr.error or (
                "No report was produced — every document failed to parse. "
                "See the log for the per-document cause "
                "(e.g. parser unavailable, unsupported file type, or rate limit)."
            )
        return result

    # ── Subprocess path (rollback only) ────────────────────────────────────

    def _run_via_subprocess(
        self,
        parsers_list: list[str],
        selected:     list[str],
        include_pp:   bool,
    ) -> dict:
        """Legacy: one ``python -m backend.app.pipeline.cli`` subprocess per parser.

        Kept reachable via ``EVAL_USE_SUBPROCESS=1`` so we can fall back if the
        in-process path turns out to misbehave in a way we don't catch in tests.
        """
        if len(parsers_list) == 1:
            with phase("per_parser", parser=parsers_list[0]):
                result = self._run_single_parser_subprocess(parsers_list[0], selected, include_pp)
            result['_parser_id'] = parsers_list[0]
            return result

        parser_results: dict[str, dict] = {}
        for parser_method in parsers_list:
            with phase("per_parser", parser=parser_method):
                parser_results[parser_method] = self._run_single_parser_subprocess(
                    parser_method, selected, include_pp,
                )
        return {"multi_parser": True, "parsers": parser_results}

    def _run_single_parser_subprocess(
        self,
        parser_method: str,
        selected: list[str],
        include_postprocessing: bool = False,
    ) -> dict:
        """Run the evaluation pipeline for one parser via subprocess.

        Wipes only **this parser's** subfolder reports before running so a
        previous run's PP reports never leak into this run's response when
        ``include_postprocessing=False``, and so concurrent multi-parser runs
        no longer clobber each other's flat report files (Stage 3).
        """
        self._reports.wipe_for(parser_method, include_pp=True)

        cmd = [
            sys.executable, "-m", PIPELINE_MODULE,
            str(FILES_DIR),
            "--output", str(GENERAL_JSON),
            "--parser", parser_method,
        ]
        if selected:
            cmd += ["--include", ",".join(selected)]
        if include_postprocessing:
            cmd += ["--postprocessing"]

        try:
            with phase("subprocess", parser=parser_method,
                       postprocessing=include_postprocessing):
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=PIPELINE_SUBPROCESS_TIMEOUT,
                    cwd=str(ROOT),
                )
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": f"Evaluation timed out after {PIPELINE_SUBPROCESS_TIMEOUT} s.",
                "stdout": "",
                "stderr": "",
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc), "stdout": "", "stderr": ""}

        with phase("load_reports", parser=parser_method):
            reports = self._reports.load_all_reports_for(parser_method)

        # A returncode of 0 alone is not success: the pipeline logs per-document
        # parser failures (503 unavailable, 404 unsupported type, 429 rate limit,
        # connection errors) to stderr and keeps going, so a run where *every*
        # document failed still exits 0 — but writes no report. Treat "no general
        # report produced" as an error so the UI surfaces the log instead of an
        # empty, falsely-"ok" parser tab.
        produced = reports.get("general") is not None
        ok = proc.returncode == 0 and produced

        # Strip timing lines from stderr so the UI log pane stays clean.
        clean_stderr = strip_timing_lines(proc.stderr)

        result = {
            "status":     "ok" if ok else "error",
            "returncode": proc.returncode,
            "stdout":     proc.stdout,
            "stderr":     clean_stderr,
            **reports,
        }
        if not ok and not produced:
            result["error"] = (
                "No report was produced — every document failed to parse. "
                "See the log for the per-document cause "
                "(e.g. parser unavailable, unsupported file type, or rate limit)."
            )
        return result
