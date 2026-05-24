"""
backend/app/main.py
---------------------
FastAPI application entry point for the Parsing Eval System backend.

Run with:
    uvicorn backend.app.main:app --reload --port 5000

Port 5000 matches the frontend Vite dev-server proxy (/api -> :5000) and the
CORS origins in config/constants.py. Change one and you must change all three.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config.constants import CORS_ORIGINS
from backend.app.routes import (
    comparison_routes,
    evaluation_routes,
    files_routes,
    results_routes,
    stream_routes,
)

app = FastAPI(title="Parsing Eval System API", version="1.0.0")

# ── CORS (local development) ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ───────────────────────────────────────────────────────────────
app.include_router(files_routes.router)
app.include_router(evaluation_routes.router)
app.include_router(results_routes.router)
app.include_router(stream_routes.router)
app.include_router(comparison_routes.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})
