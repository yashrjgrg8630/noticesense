from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.notice import Notice, NoticeStatus
from app.schemas.notice import UploadResponse
from app.services import storage
from app.services.storage import UploadValidationError
from app.tasks.processing import process_notice

router = APIRouter(prefix="/notices", tags=["upload"])


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_notice(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    content = await file.read()
    content_type = file.content_type or ""

    try:
        digest = storage.validate_and_fingerprint(content, content_type)
    except UploadValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # De-duplicate: if the exact bytes were already processed, return that notice.
    existing = (
        await db.execute(
            select(Notice).where(Notice.sha256 == digest).order_by(Notice.created_at.desc())
        )
    ).scalars().first()
    if existing is not None:
        return UploadResponse(id=existing.id, status=existing.status, duplicate_of=existing.id)

    stored_path = storage.save_file(content, content_type)
    notice = Notice(
        original_filename=file.filename or "notice",
        stored_path=stored_path,
        content_type=content_type,
        file_size=len(content),
        sha256=digest,
        status=NoticeStatus.uploaded,
    )
    db.add(notice)
    await db.commit()
    await db.refresh(notice)

    # Hand off to the background worker.
    process_notice.delay(notice.id)

    return UploadResponse(id=notice.id, status=notice.status, duplicate_of=None)
