"""
parser_backends.py
------------------
Parser backend implementations. Each backend knows how to call one
parser service and extract plain text from its response.

To add a new parser service:
  1. Subclass ParserBackend and implement call().
  2. Add an entry to _REGISTRY mapping the parser_method string to the class.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from backend.app.config.constants import PARSER_HTTP_TIMEOUT as _TIMEOUT
from backend.app.config.env import (
    PARSER_URL as _DEFAULT_URL,
    PYMUPDF_PARSER_URL as _PYMUPDF_URL,
)


class ParserBackend(ABC):
    @abstractmethod
    def call(self, file_bytes: bytes, filename: str) -> str:
        """Send file_bytes to the parser service and return plain text."""


class DefaultParserBackend(ParserBackend):
    """Routes to the default parser service (port 4004)."""

    def __init__(self, parser_method: str) -> None:
        self._url = (
            f"{_DEFAULT_URL}?parser_method={parser_method}"
            if parser_method
            else _DEFAULT_URL
        )

    def call(self, file_bytes: bytes, filename: str) -> str:
        r = httpx.post(
            self._url,
            content=file_bytes,
            headers={
                "Content-Type": "application/octet-stream",
                "X-Original-Filename": filename,
            },
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        return r.json().get("content", "")


class PyMuPDFParserBackend(ParserBackend):
    """Routes to the PyMuPDF service (port 8001); flattens RAG block format."""

    def call(self, file_bytes: bytes, filename: str) -> str:
        r = httpx.post(
            f"{_PYMUPDF_URL}?method=markdown",
            content=file_bytes,
            headers={
                "Content-Type": "application/octet-stream",
                "X-Original-Filename": filename,
            },
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        blocks = r.json().get("blocks", [])
        return "\n".join(b.get("text", "") for b in blocks if b.get("text"))


# Map parser_method strings to their backend classes.
# Keys not present here fall through to DefaultParserBackend.
_REGISTRY: dict[str, type[ParserBackend]] = {
    "pdf_pymupdf": PyMuPDFParserBackend,
}


def get_backend(parser_method: str) -> ParserBackend:
    """Return the appropriate ParserBackend for the given parser_method."""
    cls = _REGISTRY.get(parser_method)
    if cls is not None:
        return cls()
    return DefaultParserBackend(parser_method)
