"""
backend/app/db/session.py
---------------------------
SQLAlchemy engine + session factory.

The engine is created once at import time using DATABASE_URL from config/env.
SessionLocal is a sessionmaker; each request that needs DB access opens a
fresh session via the FastAPI `get_db` dependency (defined in dependencies.py).

Security: the DATABASE_URL is intentionally not logged anywhere in this module.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config.env import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)
