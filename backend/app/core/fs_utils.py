"""
core/fs_utils.py
----------------
Filesystem helpers for discovering document folders and document files.
No metrics, no parsing, no output — pure path logic.

Uses SUPPORTED_EXTS from config/constants.py as the single source of truth
for which file extensions count as parser input documents.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from backend.app.config.constants import SUPPORTED_EXTS


def find_document_file(file_dir: Path) -> Path:
    """
    Find the document file sitting directly inside file_dir (not in GT/).
    Prefers the file whose stem matches the folder name when multiple exist.
    Raises FileNotFoundError if no supported file is found.
    """
    candidates = [
        f for f in file_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS
    ]

    if not candidates:
        raise FileNotFoundError(
            f"No supported document file found in {file_dir}\n"
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTS))}"
        )

    if len(candidates) > 1:
        name_match = [f for f in candidates if f.stem == file_dir.name]
        if name_match:
            return name_match[0]
        print(
            f"[warn] Multiple document files in '{file_dir.name}', "
            f"using '{candidates[0].name}'",
            file=sys.stderr,
        )

    return candidates[0]


def collect_files_dirs_to_test(input_dir: Path) -> List[Path]:
    """
    Return all subfolders of input_dir that contain:
      - a GT/ subfolder
      - at least one supported document file next to it

    Skipped folders are reported to stderr.
    """
    dirs: List[Path] = []

    for candidate in sorted(input_dir.iterdir()):
        if not candidate.is_dir():
            continue

        has_gt  = (candidate / "GT").exists()
        has_doc = any(
            f.is_file() and f.suffix.lower() in SUPPORTED_EXTS
            for f in candidate.iterdir()
        )

        if has_gt and has_doc:
            dirs.append(candidate)
        else:
            missing = []
            if not has_gt:
                missing.append("GT/")
            if not has_doc:
                missing.append("document file")
            print(
                f"[warn] Skipping '{candidate.name}' — missing: {', '.join(missing)}",
                file=sys.stderr,
            )

    return dirs
