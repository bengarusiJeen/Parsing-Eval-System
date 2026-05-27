"""
parser.py
---------
Document parser plug-in. Delegates to the appropriate ParserBackend
(see parser_backends.py) based on the parser_method string.

Expected signature:
    parse(file_path: str, parser_method: str, cache: RunCache | None) -> str
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from backend.app.core.paths import per_parser_parsing_dir
from backend.app.pipeline.cache import RunCache
from backend.app.pipeline.parser_backends import get_backend


def _save_output(file_path: Path, text: str, parser_method: str) -> None:
    """Persist the parser's raw text under ``data/parsing_results/<parser>/``.

    The per-parser subfolder (Stage 3) prevents the previous "two parsers
    overwrite the same {doc}.txt" collision when multi-parser runs share
    documents.
    """
    out_dir = per_parser_parsing_dir(parser_method)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (file_path.stem + ".txt")
    out.write_text(text, encoding="utf-8")


def parse(
    file_path:     str,
    parser_method: str = "base_text_parser",
    cache:         Optional[RunCache] = None,
) -> str:
    """Extract plain text from a document via the appropriate parser service.

    Args:
        cache  — optional per-run cache (Stage 5). When provided, the document
                 bytes are read once and shared across parsers in the same run.
                 When None, the bytes are read fresh on every call.
    """
    path = Path(file_path)
    file_bytes = cache.doc_bytes(path) if cache is not None else path.read_bytes()

    # HTTP headers must be ASCII — fall back to a safe name for non-ASCII filenames (e.g. Hebrew)
    try:
        path.name.encode("ascii")
        safe_filename = path.name
    except UnicodeEncodeError:
        safe_filename = f"document{path.suffix}"

    text = get_backend(parser_method).call(file_bytes, safe_filename)
    _save_output(path, text, parser_method)
    return text