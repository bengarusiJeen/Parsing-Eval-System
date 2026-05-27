"""
backend/app/service/stream_service.py
----------------------------------------
StreamService: builds annotated segment data for the Document Stream
Comparison view. Receives a ReportService instance via constructor injection.
"""
from __future__ import annotations

from pathlib import Path

from backend.app.config.constants import GT_BLOCK_DELIMITER
from backend.app.core.paths import (
    FILES_DIR,
    PARSING_FILES_DIR,
    per_parser_parsing_dir,
)
from backend.app.service.report_service import ReportService


class StreamService:
    def __init__(self, report_service: ReportService) -> None:
        self._reports = report_service

    # ── static text helpers (no I/O, no service deps) ───────────────────────

    @staticmethod
    def parse_gt_blocks(raw: str) -> list[str]:
        """Extract text blocks from a GT Text.txt (delimited by ==== lines)."""
        blocks: list[str] = []
        current: list[str] = []
        in_block = False
        for line in raw.splitlines():
            if line.strip() == GT_BLOCK_DELIMITER:
                if in_block:
                    text = "\n".join(current).strip()
                    if text:
                        blocks.append(text)
                    current, in_block = [], False
                else:
                    in_block = True
            elif in_block:
                current.append(line)
        if in_block and current:
            text = "\n".join(current).strip()
            if text:
                blocks.append(text)
        return blocks

    @staticmethod
    def annotate(
        text: str, spec: list[tuple[str, str]]
    ) -> list[tuple[int, int, str]]:
        """
        Find non-overlapping (start, end, cls) spans for each (word, cls) in spec.
        Earlier entries in spec take priority.
        """
        used: set[int] = set()
        spans: list[tuple[int, int, str]] = []
        for word, cls in spec:
            if not word or not text:
                continue
            wlen = len(word)
            pos = 0
            while True:
                idx = text.find(word, pos)
                if idx == -1:
                    break
                end = idx + wlen
                if not used.intersection(range(idx, end)):
                    spans.append((idx, end, cls))
                    used.update(range(idx, end))
                pos = idx + 1
        return sorted(spans)

    @staticmethod
    def build_segments(
        text: str, spans: list[tuple[int, int, str]]
    ) -> list[dict]:
        """Convert annotated spans into a [{text, cls}] segment list."""
        segs: list[dict] = []
        pos = 0
        for start, end, cls in spans:
            if start > pos:
                segs.append({"text": text[pos:start], "cls": ""})
            segs.append({"text": text[start:end], "cls": cls})
            pos = end
        if pos < len(text):
            segs.append({"text": text[pos:], "cls": ""})
        return [s for s in segs if s["text"]]

    # ── main entry point ─────────────────────────────────────────────────────

    def build_stream_data(self, doc_name: str, parser_method: str | None = None) -> dict:
        """
        Build the full stream comparison payload for the given document name.
        Returns a dict with keys: gt, raw, pp, has_gt, has_raw, has_pp.

        When ``parser_method`` is provided (the normal case post-Stage-3),
        raw/PP text and the four report files are read from this parser's
        subfolder. The flat layout is used as a fallback so legacy snapshots
        keep working.
        """
        gt_file = FILES_DIR / doc_name / "GT" / "Text.txt"

        # Pick the (per-parser, flat) path pair for raw text + PP text.
        def _pick(per_parser: Path, flat: Path) -> Path:
            return per_parser if per_parser.exists() else flat

        flat_raw = PARSING_FILES_DIR / f"{doc_name}.txt"
        flat_pp  = PARSING_FILES_DIR / f"{doc_name}_after_post.txt"
        if parser_method:
            parser_dir = per_parser_parsing_dir(parser_method)
            raw_file = _pick(parser_dir / f"{doc_name}.txt",            flat_raw)
            pp_file  = _pick(parser_dir / f"{doc_name}_after_post.txt", flat_pp)
        else:
            raw_file = flat_raw
            pp_file  = flat_pp

        gt_text = raw_text = pp_text = None

        if gt_file.exists():
            blocks  = self.parse_gt_blocks(
                gt_file.read_text(encoding="utf-8", errors="replace")
            )
            gt_text = "\n\n".join(blocks)

        if raw_file.exists():
            raw_text = raw_file.read_text(encoding="utf-8", errors="replace").strip()

        if pp_file.exists():
            pp_text = pp_file.read_text(encoding="utf-8", errors="replace").strip()

        # Load report slices for this document. Per-parser when known
        # (so multi-parser runs hit the right diagnostics), flat otherwise.
        if parser_method:
            reps = self._reports.load_all_reports_for(parser_method)
        else:
            reps = self._reports.load_all_reports()
        diag_doc    = self._reports.find_doc(reps.get("diagnostic"),    doc_name)
        diag_pp_doc = self._reports.find_doc(reps.get("diagnostic_pp"), doc_name)
        gen_doc     = self._reports.find_doc(reps.get("general"),       doc_name)
        gen_pp_doc  = self._reports.find_doc(reps.get("general_pp"),    doc_name)

        def _issues(doc: dict | None) -> dict:
            dp  = (doc or {}).get("detected_problems", {})
            fmt = dp.get("FORMATTING_ISSUES", {})
            return {
                "ocr":      dp.get("OCR_SPLIT",    {}).get("issues",  []),
                "merged":   dp.get("MERGED_WORDS", {}).get("issues",  []),
                "punct":    fmt.get("MISPLACED_PUNCTUATION", {}).get("issues", []),
                "reversal": fmt.get("WORD_ORDER_REVERSAL",   {}).get("issues", []),
                "unclass":  dp.get("UNCLASSIFIED", {}).get("ngrams",  []),
            }

        raw_iss = _issues(diag_doc)
        pp_iss  = _issues(diag_pp_doc)

        noise_raw = (gen_doc    or {}).get("noise", {}).get("noise_words", [])
        noise_pp  = (gen_pp_doc or {}).get("noise", {}).get("noise_words", [])

        raw_ocr_originals = {i.get("original_word", "") for i in raw_iss["ocr"]}
        pp_ocr_originals  = {i.get("original_word", "") for i in pp_iss["ocr"]}
        ocr_fixed = raw_ocr_originals - pp_ocr_originals
        ocr_still = raw_ocr_originals & pp_ocr_originals

        raw_merged_set   = {i.get("merged_word", "") for i in raw_iss["merged"]}
        pp_merged_set    = {i.get("merged_word", "") for i in pp_iss["merged"]}
        merged_fixed_set = raw_merged_set - pp_merged_set

        fixed_orig_words: set[str] = set()
        for iss in raw_iss["merged"]:
            if iss.get("merged_word", "") in merged_fixed_set:
                fixed_orig_words.update(iss.get("original", []))

        raw_spec: list[tuple[str, str]] = []
        for iss in raw_iss["ocr"]:
            for frag in iss.get("fragments_in_parser", []):
                raw_spec.append((frag, "hl-error"))
        for iss in raw_iss["merged"]:
            raw_spec.append((iss.get("merged_word", ""), "hl-format"))
        for iss in raw_iss["punct"] + raw_iss["reversal"]:
            pt = iss.get("parser_text", "")
            if pt:
                raw_spec.append((pt, "hl-format"))
        for w in noise_raw:
            raw_spec.append((w, "hl-noise"))

        gt_spec: list[tuple[str, str]] = []
        for w in ocr_fixed:
            gt_spec.append((w, "hl-fixed"))
        for w in ocr_still:
            gt_spec.append((w, "hl-missing"))
        for w in fixed_orig_words:
            gt_spec.append((w, "hl-fixed"))
        for ng in pp_iss["unclass"]:
            gt_spec.append((ng, "hl-missing"))

        pp_spec: list[tuple[str, str]] = []
        for w in ocr_fixed:
            pp_spec.append((w, "hl-fixed"))
        for iss in pp_iss["ocr"]:
            for frag in iss.get("fragments_in_parser", []):
                pp_spec.append((frag, "hl-error"))
        for w in fixed_orig_words:
            pp_spec.append((w, "hl-fixed"))
        for iss in pp_iss["merged"]:
            pp_spec.append((iss.get("merged_word", ""), "hl-format"))
        for iss in pp_iss["punct"] + pp_iss["reversal"]:
            pt = iss.get("parser_text", "")
            if pt:
                pp_spec.append((pt, "hl-format"))
        for w in noise_pp:
            pp_spec.append((w, "hl-noise"))

        def _segs(text: str | None, spec: list[tuple[str, str]]) -> list[dict]:
            if text is None:
                return []
            return self.build_segments(text, self.annotate(text, spec))

        return {
            "gt":      _segs(gt_text,  gt_spec),
            "raw":     _segs(raw_text, raw_spec),
            "pp":      _segs(pp_text,  pp_spec),
            "has_gt":  gt_text  is not None,
            "has_raw": raw_text is not None,
            "has_pp":  pp_text  is not None,
        }
