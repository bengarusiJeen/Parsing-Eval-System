"""
parser.py
---------
Document parser plug-in. Delegates to the appropriate ParserBackend
(see parser_backends.py) based on the parser_method string.

Expected signature:
    parse(file_path: str, parser_method: str) -> str
"""
from __future__ import annotations

from pathlib import Path

from backend.app.core.paths import PARSING_FILES_DIR
from backend.app.pipeline.parser_backends import get_backend

_OUTPUT_DIR = PARSING_FILES_DIR


def _save_output(file_path: Path, text: str) -> None:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = _OUTPUT_DIR / (file_path.stem + ".txt")
    out.write_text(text, encoding="utf-8")


def parse(file_path: str, parser_method: str = "base_text_parser") -> str:
    """Extract plain text from a document via the appropriate parser service."""
    path = Path(file_path)
    file_bytes = path.read_bytes()

    # HTTP headers must be ASCII — fall back to a safe name for non-ASCII filenames (e.g. Hebrew)
    try:
        path.name.encode("ascii")
        safe_filename = path.name
    except UnicodeEncodeError:
        safe_filename = f"document{path.suffix}"

    text = get_backend(parser_method).call(file_bytes, safe_filename)
    _save_output(path, text)
    return text