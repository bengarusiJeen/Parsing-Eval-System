"""
cli.py
------
CLI entry point and two-pass evaluation orchestrator.

Usage:
  python -m backend.app.pipeline.cli <input_dir> --output results.json
  python -m backend.app.pipeline.cli <input_dir> --n 8 --output results.json
  python -m backend.app.pipeline.cli <input_dir> --include doc1,doc2 --parser my_parser
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Tuple

# Ensure stdout/stderr handle Unicode (e.g. Hebrew filenames) on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse

from backend.app.config.constants import DEFAULT_PARSER_METHOD
from backend.app.core.fs_utils import collect_files_dirs_to_test
from backend.app.core.paths import PARSING_FILES_DIR
from backend.app.core.substitutions import SubstitutionTable
from backend.app.models.document_models import DocumentResult, EvaluationArtifacts
from backend.app.pipeline.diagnostics import DIAGNOSTICS_PP_FILENAME, run_diagnostics
from backend.app.pipeline.evaluator import evaluate_document
from backend.app.pipeline.json_reporter import save_json_report
from backend.app.pipeline.ocr import pre_test
from backend.app.pipeline.postprocessing import Postprocessing


@dataclass
class RunRecord:
    """Groups a document folder with its evaluation artifacts from Pass 1."""
    file_dir:  Path
    artifacts: EvaluationArtifacts


# ══════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════

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
                   help="Save JSON report to this file.")
    p.add_argument("--n",       type=int, default=3,
                   help="N-gram size for coverage evaluation (default: 3).")
    p.add_argument("--include", type=str, default=None,
                   help="Comma-separated subfolder names to include (default: all).")
    p.add_argument("--parser",  type=str, default=DEFAULT_PARSER_METHOD,
                   help=f"Parser method to use (default: {DEFAULT_PARSER_METHOD}).")
    return p


def main() -> None:
    args = build_arg_parser().parse_args()

    input_dir: Path = args.input_dir
    if not input_dir.exists():
        raise SystemExit(f"[error] Folder not found: {input_dir}")
    if not input_dir.is_dir():
        raise SystemExit(f"[error] Not a folder: {input_dir}")

    pre_test(input_dir)

    files_dirs = collect_files_dirs_to_test(input_dir)
    if not files_dirs:
        raise SystemExit("No valid document folders found.")

    if args.include:
        include_set = {n.strip() for n in args.include.split(',')}
        files_dirs  = [d for d in files_dirs if d.name in include_set]
        if not files_dirs:
            raise SystemExit("No matching document folders found for --include filter.")

    sub_table = SubstitutionTable.load(
        Path(__file__).parent.parent / "core" / "substitutions.json"
    )

    # ══════════════════════════════════════════════
    # Pass 1 — Standard evaluation
    # ══════════════════════════════════════════════
    run_records: List[RunRecord] = []

    for file_dir in files_dirs:
        try:
            artifacts = evaluate_document(
                file_dir, n=args.n, sub_table=sub_table, parser_method=args.parser
            )
            run_records.append(RunRecord(file_dir=file_dir, artifacts=artifacts))
        except NotImplementedError as e:
            print(f"\n[!] {e}", file=sys.stderr)
            raise SystemExit(1)
        except Exception as e:
            print(f"[error] {file_dir.name}: {e}", file=sys.stderr)

    results     = [r.artifacts.result      for r in run_records]
    parser_data: List[Tuple[Set[str], Set[str], Set[str], str]] = [
        (r.artifacts.parser_ngrams_set,
         r.artifacts.parser_words_set,
         r.artifacts.parser_bigrams_set,
         r.artifacts.file_ext)
        for r in run_records
    ]

    if args.output and results:
        save_json_report(results, args.output, n=args.n)

    if results:
        run_diagnostics(results, parser_data)

    # ══════════════════════════════════════════════
    # Pass 2 — Postprocessing evaluation
    # ══════════════════════════════════════════════
    pp = Postprocessing()
    pp_text_dir = PARSING_FILES_DIR
    pp_text_dir.mkdir(exist_ok=True)

    pp_run_records: List[RunRecord] = []

    for record in run_records:
        try:
            artifacts_pp = evaluate_document(
                record.file_dir,
                n=args.n,
                postprocessor=pp,
                _parser_text=record.artifacts.raw_parser_text,
                sub_table=sub_table,
            )
            pp_run_records.append(RunRecord(file_dir=record.file_dir, artifacts=artifacts_pp))

            # Write postprocessed text to file — reuse the cached result from evaluate_document.
            if artifacts_pp.postprocessed_text is not None:
                out_file = pp_text_dir / f"{record.file_dir.name}_after_post.txt"
                out_file.write_text(artifacts_pp.postprocessed_text, encoding="utf-8")
        except Exception as e:
            print(f"[warn] Postprocessing failed for {record.file_dir.name}: {e}",
                  file=sys.stderr)

    results_pp     = [r.artifacts.result for r in pp_run_records]
    parser_data_pp: List[Tuple[Set[str], Set[str], Set[str], str]] = [
        (r.artifacts.parser_ngrams_set,
         r.artifacts.parser_words_set,
         r.artifacts.parser_bigrams_set,
         r.artifacts.file_ext)
        for r in pp_run_records
    ]

    if args.output and results_pp:
        pp_output = args.output.parent / ("postprocessing-" + args.output.stem + args.output.suffix)
        save_json_report(results_pp, pp_output, n=args.n)

    if results_pp:
        run_diagnostics(results_pp, parser_data_pp, output_filename=DIAGNOSTICS_PP_FILENAME)


if __name__ == "__main__":
    main()
