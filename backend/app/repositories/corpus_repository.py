"""
backend/app/repositories/corpus_repository.py
-----------------------------------------------
All DB access for the corpora and corpus_files tables.
Stateless — methods accept a Session argument owned by the calling service.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models.corpus import Corpus
from backend.app.db.models.corpus_file import CorpusFile


class CorpusRepository:
    # ── corpora ──────────────────────────────────────────────────────────────

    def list_corpora(
        self, db: Session, *, include_inactive: bool = False
    ) -> list[Corpus]:
        stmt = select(Corpus).order_by(Corpus.id)
        if not include_inactive:
            stmt = stmt.where(Corpus.is_active.is_(True))
        return list(db.execute(stmt).scalars().all())

    def get_corpus(self, db: Session, corpus_id: int) -> Corpus | None:
        return db.get(Corpus, corpus_id)

    def get_corpus_by_name(self, db: Session, name: str) -> Corpus | None:
        stmt = select(Corpus).where(Corpus.name == name)
        return db.execute(stmt).scalar_one_or_none()

    def create_corpus(
        self,
        db: Session,
        *,
        name: str,
        description: str | None,
        overall_ratio: float,
        is_active: bool = True,
    ) -> Corpus:
        corpus = Corpus(
            name=name,
            description=description,
            overall_ratio=overall_ratio,
            is_active=is_active,
        )
        db.add(corpus)
        db.flush()
        return corpus

    def update_corpus(
        self,
        db: Session,
        corpus: Corpus,
        *,
        name: str | None = None,
        description: str | None = None,
        overall_ratio: float | None = None,
        is_active: bool | None = None,
    ) -> Corpus:
        if name is not None:
            corpus.name = name
        if description is not None:
            corpus.description = description
        if overall_ratio is not None:
            corpus.overall_ratio = overall_ratio
        if is_active is not None:
            corpus.is_active = is_active
        db.flush()
        return corpus

    def list_active_corpora_with_files(self, db: Session) -> list[Corpus]:
        """Active corpora with their active file assignments eager-loaded.

        Used by the overall weighted timeline so we can compute every corpus's
        per-run score from a single fetch.
        """
        stmt = (
            select(Corpus)
            .options(selectinload(Corpus.files))
            .where(Corpus.is_active.is_(True))
            .order_by(Corpus.id)
        )
        return list(db.execute(stmt).scalars().all())

    # ── corpus_files ─────────────────────────────────────────────────────────

    def list_corpus_files(
        self,
        db: Session,
        corpus_id: int,
        *,
        include_inactive: bool = False,
    ) -> list[CorpusFile]:
        stmt = (
            select(CorpusFile)
            .where(CorpusFile.corpus_id == corpus_id)
            .order_by(CorpusFile.id)
        )
        if not include_inactive:
            stmt = stmt.where(CorpusFile.is_active.is_(True))
        return list(db.execute(stmt).scalars().all())

    def get_corpus_file(
        self, db: Session, corpus_id: int, file_name: str
    ) -> CorpusFile | None:
        stmt = select(CorpusFile).where(
            CorpusFile.corpus_id == corpus_id,
            CorpusFile.file_name == file_name,
        )
        return db.execute(stmt).scalar_one_or_none()

    def add_corpus_file(
        self,
        db: Session,
        *,
        corpus_id: int,
        file_name: str,
        is_active: bool = True,
    ) -> CorpusFile:
        cf = CorpusFile(corpus_id=corpus_id, file_name=file_name, is_active=is_active)
        db.add(cf)
        db.flush()
        return cf

    def update_corpus_file(
        self,
        db: Session,
        cf: CorpusFile,
        *,
        is_active: bool | None = None,
    ) -> CorpusFile:
        if is_active is not None:
            cf.is_active = is_active
        db.flush()
        return cf

    def get_active_file_names(self, db: Session, corpus_id: int) -> list[str]:
        stmt = (
            select(CorpusFile.file_name)
            .where(
                CorpusFile.corpus_id == corpus_id,
                CorpusFile.is_active.is_(True),
            )
            .order_by(CorpusFile.file_name)
        )
        return list(db.execute(stmt).scalars().all())
