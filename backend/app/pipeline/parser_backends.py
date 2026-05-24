"""
parser_backends.py
------------------
Parser backend implementations. Each backend knows how to call one
parser service and extract plain text from its response.

The Jeen parser service exposes a single endpoint (PARSER_URL, port 4004).
Every parser variant — document_intelligence, pdf_pymupdf, base_text_parser,
auto, etc. — is selected through the ``parser_method`` query parameter and
routed internally by the service. There is therefore one backend.

To add a backend for a genuinely different service:
  1. Subclass ParserBackend and implement call().
  2. Add an entry to _REGISTRY mapping the parser_method string to the class.
"""
from __future__ import annotations

import sys
import time
from abc import ABC, abstractmethod

import httpx

from backend.app.config.constants import (
    PARSER_HTTP_TIMEOUT as _TIMEOUT,
    PARSER_RATE_LIMIT_MAX_RETRIES as _MAX_RETRIES,
    PARSER_RATE_LIMIT_MAX_WAIT_SECONDS as _MAX_WAIT,
    PARSER_RATE_LIMIT_WAIT_SECONDS as _DEFAULT_WAIT,
)
from backend.app.config.env import PARSER_URL as _DEFAULT_URL


def _retry_after_seconds(resp: httpx.Response) -> float:
    """Seconds to wait before retrying a 429, honouring Retry-After when present."""
    raw = resp.headers.get("Retry-After")
    if raw:
        try:
            return min(float(raw), _MAX_WAIT)
        except ValueError:
            pass  # Retry-After can be an HTTP-date; fall back to the default wait
    return _DEFAULT_WAIT


class ParserBackend(ABC):
    @abstractmethod
    def call(self, file_bytes: bytes, filename: str) -> str:
        """Send file_bytes to the parser service and return plain text."""


class DefaultParserBackend(ParserBackend):
    """Routes to the Jeen parser service (PARSER_URL, port 4004).

    The parser variant is selected via the ``parser_method`` query param.
    Requests that come back HTTP 429 (rate limited) are retried with a wait.
    """

    def __init__(self, parser_method: str) -> None:
        self._url = (
            f"{_DEFAULT_URL}?parser_method={parser_method}"
            if parser_method
            else _DEFAULT_URL
        )

    def call(self, file_bytes: bytes, filename: str) -> str:
        headers = {
            "Content-Type": "application/octet-stream",
            "X-Original-Filename": filename,
        }

        attempt = 0
        while True:
            r = httpx.post(self._url, content=file_bytes, headers=headers, timeout=_TIMEOUT)

            if r.status_code == 429 and attempt < _MAX_RETRIES:
                wait = _retry_after_seconds(r)
                attempt += 1
                print(
                    f"[rate-limit] parser returned 429; waiting {wait:.0f}s then "
                    f"retrying ({attempt}/{_MAX_RETRIES})",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue

            r.raise_for_status()
            return r.json().get("content", "")


# Map parser_method strings to a dedicated backend class. Methods not listed
# here (the normal case) fall through to DefaultParserBackend, which sends the
# method to the Jeen service as a query param.
_REGISTRY: dict[str, type[ParserBackend]] = {}


def get_backend(parser_method: str) -> ParserBackend:
    """Return the appropriate ParserBackend for the given parser_method."""
    cls = _REGISTRY.get(parser_method)
    if cls is not None:
        return cls()
    return DefaultParserBackend(parser_method)
