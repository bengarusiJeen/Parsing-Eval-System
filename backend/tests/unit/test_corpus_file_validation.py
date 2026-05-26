"""Unit tests for the on-disk corpus file validation."""
from __future__ import annotations

import pytest

from backend.app.service import corpus_service as cs_mod
from backend.app.service.corpus_service import CorpusValidationError, _validate_file_on_disk


def _make_eval_layout(root, name: str, gt_text: str | None = "block one\n=====\n", gt_present: bool = True, file_dir: bool = True):
    folder = root / name
    if file_dir:
        folder.mkdir(parents=True, exist_ok=True)
    if gt_present:
        gt = folder / "GT"
        gt.mkdir(parents=True, exist_ok=True)
        if gt_text is not None:
            (gt / "Text.txt").write_text(gt_text, encoding="utf-8")
    return folder


def test_rejects_when_folder_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(cs_mod, "FILES_DIR", tmp_path)
    with pytest.raises(CorpusValidationError) as exc:
        _validate_file_on_disk("no_such_file")
    assert exc.value.code == "file_not_found"


def test_rejects_when_gt_folder_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(cs_mod, "FILES_DIR", tmp_path)
    _make_eval_layout(tmp_path, "doc-a", gt_present=False)
    with pytest.raises(CorpusValidationError) as exc:
        _validate_file_on_disk("doc-a")
    assert exc.value.code == "no_gt_folder"


def test_rejects_when_gt_has_no_text_file(monkeypatch, tmp_path):
    monkeypatch.setattr(cs_mod, "FILES_DIR", tmp_path)
    _make_eval_layout(tmp_path, "doc-b", gt_text=None)
    with pytest.raises(CorpusValidationError) as exc:
        _validate_file_on_disk("doc-b")
    # gt_loader raises FileNotFoundError → wrapped as "invalid_gt"
    assert exc.value.code == "invalid_gt"


def test_rejects_when_gt_has_no_blocks(monkeypatch, tmp_path):
    monkeypatch.setattr(cs_mod, "FILES_DIR", tmp_path)
    # No delimiters → load_gt returns []
    _make_eval_layout(tmp_path, "doc-c", gt_text="just some text without delimiters\n")
    with pytest.raises(CorpusValidationError) as exc:
        _validate_file_on_disk("doc-c")
    assert exc.value.code == "empty_gt"


def test_accepts_valid_file(monkeypatch, tmp_path):
    monkeypatch.setattr(cs_mod, "FILES_DIR", tmp_path)
    # One block between two ==== delimiters
    _make_eval_layout(
        tmp_path, "doc-good",
        gt_text="====\nhello world this is a block\n====\n",
    )
    # Should not raise
    _validate_file_on_disk("doc-good")
