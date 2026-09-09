from __future__ import annotations

import asyncio

from sqlalchemy import func as sa_func
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProviderError
from app.ai.factory import get_provider
from app.core.database import AsyncSessionLocal
from app.models.notice import (
    Action,
    Deadline,
    ExtractionMethod,
    Notice,
    NoticePage,
    NoticeStatus,
    ProcessingEvent,
)
from app.services import analysis, extraction, storage
from app.tasks.celery_app import celery


async def _record_event(
    db: AsyncSession, notice_id: str, stage: str, message: str, progress: float
) -> None:
    db.add(
        ProcessingEvent(
            notice_id=notice_id, stage=stage, message=message, progress=progress
        )
    )
    await db.commit()


async def _run(notice_id: str) -> None:
    async with AsyncSessionLocal() as db:
        notice = await db.get(Notice, notice_id)
        if notice is None:
            return

        try:
            # 1. Extraction
            notice.status = NoticeStatus.extracting
            await db.commit()
            await _record_event(db, notice_id, "extracting", "Reading document text", 0.15)

            content = storage.read_file(notice.stored_path)
            result = extraction.extract(content, notice.content_type)

            for page in result.pages:
                db.add(
                    NoticePage(
                        notice_id=notice_id,
                        page_number=page.page_number,
                        text=page.text,
                        char_count=len(page.text),
                        used_ocr=page.used_ocr,
                    )
                )
            notice.page_count = len(result.pages)
            notice.extraction_method = ExtractionMethod(result.method)
            await db.commit()

            any_text = any(p.text.strip() for p in result.pages)
            if not any_text:
                raise ValueError(
                    "No readable text could be extracted from this document."
                )

            ocr_pages = sum(1 for p in result.pages if p.used_ocr)
            method_note = (
                f"Extracted {len(result.pages)} page(s)"
                + (f", {ocr_pages} via OCR" if ocr_pages else "")
            )
            await _record_event(db, notice_id, "extracting", method_note, 0.45)

            # 2. Analysis
            notice.status = NoticeStatus.analyzing
            await db.commit()
            provider = get_provider()
            await _record_event(
                db,
                notice_id,
                "analyzing",
                f"Analyzing with {provider.name} ({provider.model})",
                0.6,
            )

            pages = [(p.page_number, p.text) for p in result.pages if p.text.strip()]
            parsed = await analysis.analyze_pages(provider, pages)

            notice.title = parsed.title
            notice.issuer = parsed.issuer
            notice.category = parsed.category
            notice.urgency = parsed.urgency
            notice.reference_number = parsed.reference_number
            notice.summary = parsed.summary
            notice.ai_provider = provider.name
            notice.ai_model = provider.model

            for deadline in parsed.deadlines:
                db.add(
                    Deadline(
                        notice_id=notice_id,
                        label=deadline.label,
                        due_date=deadline.due_date,
                        raw_text=deadline.raw_text,
                        source_page=deadline.source_page,
                    )
                )
            for index, action in enumerate(parsed.actions):
                db.add(
                    Action(
                        notice_id=notice_id,
                        description=action.description,
                        due_date=action.due_date,
                        source_page=action.source_page,
                        sort_order=index,
                    )
                )
            await db.commit()
            await _record_event(
                db,
                notice_id,
                "analyzing",
                f"Found {len(parsed.deadlines)} deadline(s) and {len(parsed.actions)} action(s)",
                0.9,
            )

            # 3. Done
            from sqlalchemy import func as sa_func

            notice.status = NoticeStatus.completed
            notice.analyzed_at = await _now(db)
            await db.commit()
            await _record_event(db, notice_id, "completed", "Analysis complete", 1.0)

        except (AIProviderError, ValueError) as exc:
            await _fail(db, notice, str(exc))
        except Exception as exc:  # noqa: BLE001 - surface unexpected errors to the UI
            await _fail(db, notice, f"Unexpected error during processing: {exc}")


async def _now(db: AsyncSession):
    from sqlalchemy import select as sa_select
    from sqlalchemy import func as sa_func

    return (await db.execute(sa_select(sa_func.now()))).scalar_one()


async def _fail(db: AsyncSession, notice: Notice, message: str) -> None:
    notice.status = NoticeStatus.failed
    notice.error_message = message
    await db.commit()
    await _record_event(db, notice.id, "failed", message, 1.0)


@celery.task(name="app.tasks.processing.process_notice")
def process_notice(notice_id: str) -> None:
    """Celery entrypoint: run the async processing pipeline to completion."""
    asyncio.run(_run(notice_id))
