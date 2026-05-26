"""
backend/app/service/corpus_service.py
---------------------------------------
Business logic for corpus CRUD and corpus-file assignment.

File-assignment validation reuses the existing pipeline GT loader so a file
that wouldn't be accepted by the evaluator can't be added to a corpus.
"""
from __future__ import annotations

import logging
from typing import Callable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.paths import FILES_DIR
from backend.app.db.models.corpus import Corpus
from backend.app.db.models.corpus_file import CorpusFile
from backend.app.pipeline import gt_loader
from backend.app.repositories.corpus_repository import CorpusRepository

logger = logging.getLogger(__name__)


class CorpusValidationError(Exception):
    """Raised for bad input that the route should translate to a 400."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


class CorpusConflictError(Exception):
    """Raised for unique-constraint or duplicate-assignment conflicts → 409."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def _validate_file_on_disk(file_name: str) -> None:
    """Reject if the file folder doesn't exist or doesn't have a valid GT."""
    folder = FILES_DIR / file_name
    if not folder.is_dir():
        raise CorpusValidationError(
            "file_not_found",
            f"No folder named {file_name!r} under the evaluation files directory.",
        )
    gt_dir = folder / "GT"
    if not gt_dir.is_dir():
        raise CorpusValidationError(
            "no_gt_folder",
            f"File {file_name!r} has no GT/ folder.",
        )
    try:
        blocks = gt_loader.load_gt(gt_dir)
    except Exception as exc:
        raise CorpusValidationError(
            "invalid_gt",
            f"GT for {file_name!r} is not parseable: {exc}",
        )
    if not blocks:
        raise CorpusValidationError(
            "empty_gt",
            f"GT for {file_name!r} produced no blocks — would not score in evaluation.",
        )


class CorpusService:
    def __init__(
        self,
        repository: CorpusRepository,
        session_factory: Callable[[], Session],
    ) -> None:
        self._repo = repository
        self._session_factory = session_factory

    # ── corpora ──────────────────────────────────────────────────────────────

    def list_corpora(self, *, include_inactive: bool = False) -> list[Corpus]:
        db = self._session_factory()
        try:
            return self._repo.list_corpora(db, include_inactive=include_inactive)
        finally:
            db.close()

    def get_corpus(self, corpus_id: int) -> Corpus | None:
        db = self._session_factory()
        try:
            return self._repo.get_corpus(db, corpus_id)
        finally:
            db.close()

    def create_corpus(
        self,
        *,
        name: str,
        description: str | None,
        overall_ratio: float,
        is_active: bool = True,
    ) -> Corpus:
        db = self._session_factory()
        try:
            if self._repo.get_corpus_by_name(db, name) is not None:
                raise CorpusConflictError(f"Corpus named {name!r} already exists.")
            corpus = self._repo.create_corpus(
                db,
                name=name,
                description=description,
                overall_ratio=overall_ratio,
                is_active=is_active,
            )
            db.commit()
            db.refresh(corpus)
            return corpus
        except IntegrityError:
            db.rollback()
            raise CorpusConflictError(f"Corpus named {name!r} already exists.")
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def update_corpus(
        self,
        corpus_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        overall_ratio: float | None = None,
        is_active: bool | None = None,
    ) -> Corpus | None:
        db = self._session_factory()
        try:
            corpus = self._repo.get_corpus(db, corpus_id)
            if corpus is None:
                return None
            if name is not None and name != corpus.name:
                existing = self._repo.get_corpus_by_name(db, name)
                if existing is not None and existing.id != corpus.id:
                    raise CorpusConflictError(f"Corpus named {name!r} already exists.")
            corpus = self._repo.update_corpus(
                db,
                corpus,
                name=name,
                description=description,
                overall_ratio=overall_ratio,
                is_active=is_active,
            )
            db.commit()
            db.refresh(corpus)
            return corpus
        except IntegrityError:
            db.rollback()
            raise CorpusConflictError("Update would violate a unique constraint.")
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ── corpus files ─────────────────────────────────────────────────────────

    def list_files(
        self, corpus_id: int, *, include_inactive: bool = False
    ) -> list[CorpusFile] | None:
        db = self._session_factory()
        try:
            corpus = self._repo.get_corpus(db, corpus_id)
            if corpus is None:
                return None
            return self._repo.list_corpus_files(
                db, corpus_id, include_inactive=include_inactive
            )
        finally:
            db.close()

    def assign_file(self, corpus_id: int, file_name: str) -> CorpusFile:
        """Assign an existing on-disk file to a corpus after validating GT.

        Raises CorpusValidationError(404/400-ish) or CorpusConflictError(409).
        """
        # Validate before opening a transaction — purely on-disk check.
        _validate_file_on_disk(file_name)

        db = self._session_factory()
        try:
            corpus = self._repo.get_corpus(db, corpus_id)
            if corpus is None:
                raise CorpusValidationError(
                    "corpus_not_found", f"Corpus {corpus_id} not found."
                )
            existing = self._repo.get_corpus_file(db, corpus_id, file_name)
            if existing is not None:
                raise CorpusConflictError(
                    f"File {file_name!r} is already assigned to corpus {corpus_id} "
                    f"(use PATCH to change is_active)."
                )
            cf = self._repo.add_corpus_file(
                db, corpus_id=corpus_id, file_name=file_name, is_active=True
            )
            db.commit()
            db.refresh(cf)
            return cf
        except IntegrityError:
            db.rollback()
            raise CorpusConflictError(
                f"File {file_name!r} is already assigned to corpus {corpus_id}."
            )
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def update_file(
        self,
        corpus_id: int,
        file_name: str,
        *,
        is_active: bool | None = None,
    ) -> CorpusFile | None:
        db = self._session_factory()
        try:
            cf = self._repo.get_corpus_file(db, corpus_id, file_name)
            if cf is None:
                return None
            cf = self._repo.update_corpus_file(db, cf, is_active=is_active)
            db.commit()
            db.refresh(cf)
            return cf
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
