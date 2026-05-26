"""
backend/app/service/evaluation_service.py
--------------------------------------------
EvaluationService: runs the pipeline subprocess and returns result dicts.
Receives a ReportService instance via constructor injection.
"""
from __future__ import annotations

import logging
import subprocess
import sys

from backend.app.config.constants import PIPELINE_MODULE, PIPELINE_SUBPROCESS_TIMEOUT
from backend.app.core.paths import FILES_DIR, GENERAL_JSON, ROOT
from backend.app.schemas.requests import EvaluateRequest
from backend.app.service.evaluation_history_service import EvaluationHistoryService
from backend.app.service.report_service import ReportService

logger = logging.getLogger(__name__)


class EvaluationService:
    def __init__(
        self,
        report_service: ReportService,
        history_service: EvaluationHistoryService,
    ) -> None:
        self._reports = report_service
        self._history = history_service

    def run_single_parser(self, parser_method: str, selected: list[str]) -> dict:
        """Run the evaluation pipeline for one parser and return the result dict."""
        self._reports.wipe_report_files()

        cmd = [
            sys.executable, "-m", PIPELINE_MODULE,
            str(FILES_DIR),
            "--output", str(GENERAL_JSON),
            "--parser", parser_method,
        ]
        if selected:
            cmd += ["--include", ",".join(selected)]

        try:
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

        reports = self._reports.load_all_reports()

        # A returncode of 0 alone is not success: the pipeline logs per-document
        # parser failures (503 unavailable, 404 unsupported type, 429 rate limit,
        # connection errors) to stderr and keeps going, so a run where *every*
        # document failed still exits 0 — but writes no report. Treat "no general
        # report produced" as an error so the UI surfaces the log instead of an
        # empty, falsely-"ok" parser tab.
        produced = reports.get("general") is not None
        ok = proc.returncode == 0 and produced

        result = {
            "status":     "ok" if ok else "error",
            "returncode": proc.returncode,
            "stdout":     proc.stdout,
            "stderr":     proc.stderr,
            **reports,
        }
        if not ok and not produced:
            result["error"] = (
                "No report was produced — every document failed to parse. "
                "See the log for the per-document cause "
                "(e.g. parser unavailable, unsupported file type, or rate limit)."
            )
        return result

    def run_evaluation(self, request: EvaluateRequest) -> dict:
        """Dispatch to single- or multi-parser evaluation.

        The full result is snapshotted to disk so the Results and Compare pages
        can restore per-parser data after a reload without re-running parsers.
        """
        parsers_list = request.parsers
        selected     = request.selected

        if len(parsers_list) == 1:
            result = self.run_single_parser(parsers_list[0], selected)
            # Tag the snapshot so /api/comparison/info can identify the parser
            # without the frontend having to track or send it back.
            result['_parser_id'] = parsers_list[0]
        else:
            parser_results: dict[str, dict] = {}
            for parser_method in parsers_list:
                parser_results[parser_method] = self.run_single_parser(parser_method, selected)
            result = {"multi_parser": True, "parsers": parser_results}

        self._reports.save_last_run(result)

        # Best-effort DB persistence: a failure here must never break /api/evaluate.
        try:
            self._history.persist_evaluation(request, result)
        except Exception:
            logger.exception("History persistence failed; evaluation response unaffected")

        return result
