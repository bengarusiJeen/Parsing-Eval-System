"""
backend/app/db/base.py
-----------------------
Declarative base for all SQLAlchemy ORM models.

All ORM models in `backend/app/db/models/` inherit from `Base` so a single
`Base.metadata.create_all(engine)` call in init_db creates every table.
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
