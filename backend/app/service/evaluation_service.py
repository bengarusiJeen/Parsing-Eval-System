"""
backend/app/service/evaluation_service.py
--------------------------------------------
EvaluationService: runs the pipeline subprocess and returns result dicts.
Receives a ReportService instance via constructor injection.
"""
from __future__ import annotations

import subprocess
import sys

from backend.app.config.constants import PIPELINE_MODULE, PIPELINE_SUBPROCESS_TIMEOUT
from backend.app.core.paths import FILES_DIR, GENERAL_JSON, ROOT
from backend.app.schemas.requests import EvaluateRequest
from backend.app.service.report_service import ReportService


class EvaluationService:
    def __init__(self, report_service: ReportService) -> None:
        self._reports = report_service

    def run_single_parser(self, parser_method: str, selected: list[str]) -> dict:
        """Run the evaluation pipeline for one parser and return the result dict."""
        self._reports.wipe_report_files()

        cmd = [
            sys.executable, "-m", PIPELINE_MODULE,
            str(FILES_DIR),
            "--verbose",
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

        return {
            "status":     "ok" if proc.returncode == 0 else "error",
            "returncode": proc.returncode,
            "stdout":     proc.stdout,
            "stderr":     proc.stderr,
            **reports,
        }

    def run_evaluation(self, request: EvaluateRequest) -> dict:
        """Dispatch to single- or multi-parser evaluation."""
        parsers_list = request.parsers
        selected     = request.selected

        if len(parsers_list) == 1:
            return self.run_single_parser(parsers_list[0], selected)

        parser_results: dict[str, dict] = {}
        for parser_method in parsers_list:
            parser_results[parser_method] = self.run_single_parser(parser_method, selected)

        return {"multi_parser": True, "parsers": parser_results}
