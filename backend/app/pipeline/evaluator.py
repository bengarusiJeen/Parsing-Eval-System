"""
evaluator.py
------------
Core document evaluation logic.

evaluate_document() is the single entry point: given a folder that contains
a document file and a GT/ subfolder it runs the full evaluation pipeline and
returns an EvaluationArtifacts bundle.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from backend.app.config.constants import DEFAULT_PARSER_METHOD
from backend.app.core.fs_utils import find_document_file
from backend.app.core.substitutions import SubstitutionTable
from backend.app.core.text_utils import _is_punct_token, tokenize
from backend.app.models.document_models import (
    BlockResult,
    DocumentResult,
    EvaluationArtifacts,
    Score,
)
from backend.app.pipeline import gt_loader
from backend.app.pipeline.metrics import compute_coverage, compute_noise, generate_ngrams
from backend.app.pipeline.parser import parse
from backend.app.pipeline.postprocessing import Postprocessing


def _maybe_strip_punctuation_tokens(tokens: List[str], n: int) -> List[str]:
    if n <= 4:
        return tokens
    return [w for w in tokens if not _is_punct_token(w)]


def evaluate_document(
    file_dir:      Path,
    n:             int = 3,
    postprocessor: Optional[Postprocessing] = None,
    _parser_text:  Optional[str] = None,
    sub_table:     Optional[SubstitutionTable] = None,
    parser_method: str = DEFAULT_PARSER_METHOD,
) -> EvaluationArtifacts:
    """
    Evaluate a single document folder.

    Steps:
      1. Load GT blocks from gt/
      2. Find and parse the document file (or use *_parser_text* if supplied)
      3. Optionally apply *postprocessor* to the parser output
      4. Compute coverage (per block) and noise (document level)
      5. Return a fully populated EvaluationArtifacts

    Args:
        postprocessor  — if provided, apply its ``apply()`` method with the
                         GT vocab to the parser text before tokenisation (PP pass).
        _parser_text   — skip re-parsing and use this string directly;
                         lets the PP pass reuse the text cached from the
                         standard pass without calling the parser twice.
    """
    gt_dir = file_dir / "GT"
    if not gt_dir.exists():
        raise FileNotFoundError(f"Missing GT/ subfolder in {file_dir}")

    # ── Load GT ─────────────────────────────────────────────
    gt_blocks = gt_loader.load_gt(gt_dir)
    gt_blocks = [_maybe_strip_punctuation_tokens(block, n) for block in gt_blocks]
    if not gt_blocks:
        print(f"[warn] {file_dir.name}: no ==== body blocks found in GT",
              file=sys.stderr)

    all_gt_words_set = {word for block in gt_blocks for word in block}

    # ── Parse document ──────────────────────────────────────
    test_file = find_document_file(file_dir)
    raw_parser_text = (
        _parser_text if _parser_text is not None
        else parse(str(test_file), parser_method=parser_method)
    )

    # Apply postprocessor when running the PP evaluation pass.
    # Vocab is passed directly so the class stays stateless.
    if postprocessor is not None:
        working_text = postprocessor.apply(raw_parser_text, vocab=all_gt_words_set)
        postprocessed_text: Optional[str] = working_text
    else:
        working_text = raw_parser_text
        postprocessed_text = None

    parser_words = tokenize(working_text)
    parser_words = _maybe_strip_punctuation_tokens(parser_words, n)

    # ── Build lookup sets ────────────────────────────────────
    parser_words_set  = set(parser_words)
    parser_ngrams_set = set(generate_ngrams(parser_words, n))
    parser_bigrams_set = set(generate_ngrams(parser_words, 2))

    # ── Per-block coverage ───────────────────────────────────
    block_results: List[BlockResult] = []
    for i, block_words in enumerate(gt_blocks, start=1):
        coverage_block_score, missing = compute_coverage(
            block_words,
            parser_ngrams_set,
            parser_words_set=parser_words_set,
            n=n,
            sub_table=sub_table,
        )
        block_results.append(BlockResult(
            block_index          = i,
            coverage_block_score = coverage_block_score,
            missing_words        = missing,
        ))

    # ── Document-level noise ─────────────────────────────────
    noise_score, extra = compute_noise(all_gt_words_set, parser_words_set, sub_table=sub_table)

    # ── Aggregate coverage ───────────────────────────────────
    total_checked = sum(br.coverage_block_score.checked for br in block_results)
    total_failed  = sum(br.coverage_block_score.failed  for br in block_results)
    doc_coverage  = Score(checked=total_checked, failed=total_failed)

    result = DocumentResult(
        doc_name          = file_dir.name,
        doc_file          = str(test_file),
        coverage_score    = doc_coverage,
        noise_score       = noise_score,
        gt_word_count     = sum(len(b) for b in gt_blocks),
        parser_word_count = len(parser_words),
        block_results     = block_results,
        missing_trigrams  = [w for br in block_results for w in br.missing_words],
        extra_words       = extra,
    )

    file_ext = Path(str(test_file)).suffix.lower()

    return EvaluationArtifacts(
        result             = result,
        parser_ngrams_set  = parser_ngrams_set,
        parser_words_set   = parser_words_set,
        parser_bigrams_set = parser_bigrams_set,
        file_ext           = file_ext,
        raw_parser_text    = raw_parser_text,
        postprocessed_text = postprocessed_text,
    )
