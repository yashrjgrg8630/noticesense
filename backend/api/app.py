"""
backend/api/app.py – NoticeSense FastAPI Entry Point
Serves the HTML/JS frontend as static files and exposes /api/* REST endpoints.
"""

import sys, os
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.upload import router as upload_router
from backend.api.routes.chat   import router as chat_router

app = FastAPI(title="NoticeSense API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes ────────────────────────────────────────────────────────────────
app.include_router(upload_router, prefix="/api")
app.include_router(chat_router,   prefix="/api")

# ── Serve static HTML/JS/CSS frontend ────────────────────────────────────────
STATIC_DIR = PROJECT_ROOT / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", include_in_schema=False)
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str = ""):
    """Serve the SPA index.html for all non-API routes."""
    index = STATIC_DIR / "index.html"
    return FileResponse(str(index))

@app.get("/health")
async def health():
    return {"status": "ok", "service": "NoticeSense API"}
