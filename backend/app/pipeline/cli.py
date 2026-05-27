"""
cli.py
------
CLI entry point. A thin wrapper around ``runner.run_pipeline`` so the same
in-process evaluation code runs whether you call it from the terminal or
from FastAPI (Stage 4 of the perf refactor).

Usage:
  python -m backend.app.pipeline.cli <input_dir> --output results.json
  python -m backend.app.pipeline.cli <input_dir> --n 8 --output results.json
  python -m backend.app.pipeline.cli <input_dir> --include doc1,doc2 --parser my_parser
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure stdout/stderr handle Unicode (e.g. Hebrew filenames) on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse

from backend.app.config.constants import DEFAULT_PARSER_METHOD
from backend.app.core.paths import GENERAL_FILENAME
from backend.app.pipeline.runner import run_pipeline


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Evaluate RAG parser output against ground truth.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Metrics
-------
  Coverage  fraction of GT body trigrams found in parser output
  Noise     fraction of parser words not found anywhere in GT (lower = better)

Examples
--------
  python -m backend.app.pipeline.cli "C:/...files_to_test" --output results.json
  python -m backend.app.pipeline.cli "C:/...files_to_test" --n 8 --output results.json
        """
    )
    p.add_argument("input_dir", type=Path,
                   help="Folder containing one subfolder per document.")
    p.add_argument("--output",  type=Path,
                   help="Basename for the general-report JSON file inside "
                        "reports/<parser>/. Defaults to general_report.json.")
    p.add_argument("--n",       type=int, default=3,
                   help="N-gram size for coverage evaluation (default: 3).")
    p.add_argument("--include", type=str, default=None,
                   help="Comma-separated subfolder names to include (default: all).")
    p.add_argument("--parser",  type=str, default=DEFAULT_PARSER_METHOD,
                   help=f"Parser method to use (default: {DEFAULT_PARSER_METHOD}).")
    p.add_argument("--postprocessing", action="store_true", default=False,
                   help="Also run the postprocessing evaluation pass "
                        "(off by default — Stage 2 of the perf refactor).")
    return p


def main() -> None:
    args = build_arg_parser().parse_args()

    input_dir: Path = args.input_dir
    if not input_dir.exists():
        raise SystemExit(f"[error] Folder not found: {input_dir}")
    if not input_dir.is_dir():
        raise SystemExit(f"[error] Not a folder: {input_dir}")

    selected: list[str] = []
    if args.include:
        selected = [s.strip() for s in args.include.split(',') if s.strip()]

    # --output now controls only the basename (the report path is always
    # reports/<parser>/<basename>). When omitted, fall back to the canonical
    # general_report.json so the file shows up where the rest of the system
    # expects it.
    general_basename = args.output.name if args.output is not None else GENERAL_FILENAME

    results = run_pipeline(
        input_dir=input_dir,
        selected=selected,
        parser_methods=[args.parser],
        include_postprocessing=args.postprocessing,
        n=args.n,
        capture_output=False,
        general_filename=general_basename,
    )

    pr = results.get(args.parser)
    if pr is None:
        raise SystemExit(f"[error] No result for parser {args.parser}")
    if pr.error and pr.general is None:
        # Hard failure — surface non-zero exit so shell scripts notice.
        raise SystemExit(f"[error] {pr.error}")


if __name__ == "__main__":
    main()
