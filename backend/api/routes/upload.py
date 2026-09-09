"""
routes/upload.py – POST /api/upload
Accepts a notice file, runs OCR + Phase 2 parsing + Phase 3 agents,
stores results in an in-memory session, returns session_id + agent results.
"""

import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.services.ocr_service import process_document
from backend.services.parsing_service import process_and_structure_document
from backend.router.agent_router import run_agents
from backend.core.config import settings

router = APIRouter()

# Simple in-memory session store  {session_id: {...}}
_sessions: dict = {}

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_notice(file: UploadFile = File(...)):
    """
    1. Save uploaded file temporarily.
    2. Run OCR → clean → parse (Phase 1 & 2).
    3. Run agent pipeline (Phase 3).
    4. Store everything in session; return session_id + results.
    """
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    # Save file
    dest = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # OCR
    raw_text = process_document(str(dest))
    if raw_text.startswith("Error"):
        dest.unlink(missing_ok=True)
        raise HTTPException(422, raw_text)

    # Parse
    structured_data, cleaned_text = process_and_structure_document(raw_text)

    # Agents
    agent_results = run_agents(cleaned_text)
    if agent_results.get("error"):
        raise HTTPException(500, agent_results["error"])

    # Store session
    session_id = uuid.uuid4().hex
    _sessions[session_id] = {
        "cleaned_text":   cleaned_text,
        "structured_data": structured_data,
        "agent_results":  agent_results,
        "filename":       file.filename,
    }

    # Cleanup file
    dest.unlink(missing_ok=True)

    return {
        "session_id":     session_id,
        "filename":       file.filename,
        "structured_data": structured_data,
        "agent_results":  agent_results,
    }


def get_session(session_id: str) -> dict:
    """Helper used by chat route."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found. Please re-upload the notice.")
    return session
