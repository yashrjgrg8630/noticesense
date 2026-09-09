from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.notice import Action, ActionStatus, Deadline, Notice
from app.schemas.notice import (
    ActionOut,
    ActionUpdate,
    NoticeDetail,
    NoticeListItem,
    NoticeStatusOut,
    PageTextOut,
)
from app.services import storage

router = APIRouter(prefix="/notices", tags=["notices"])


async def _get_notice_or_404(db: AsyncSession, notice_id: str, *, with_relations: bool = False) -> Notice:
    stmt = select(Notice).where(Notice.id == notice_id)
    if with_relations:
        stmt = stmt.options(
            selectinload(Notice.deadlines),
            selectinload(Notice.actions),
            selectinload(Notice.pages),
        )
    notice = (await db.execute(stmt)).scalars().first()
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found.")
    return notice


@router.get("", response_model=list[NoticeListItem])
async def list_notices(db: AsyncSession = Depends(get_db)) -> list[NoticeListItem]:
    notices = (
        await db.execute(
            select(Notice)
            .options(selectinload(Notice.deadlines), selectinload(Notice.actions))
            .order_by(Notice.created_at.desc())
        )
    ).scalars().all()

    items: list[NoticeListItem] = []
    for notice in notices:
        due_dates = [d.due_date for d in notice.deadlines if d.due_date is not None]
        open_actions = sum(
            1 for a in notice.actions if a.status in (ActionStatus.pending, ActionStatus.in_progress)
        )
        items.append(
            NoticeListItem(
                id=notice.id,
                original_filename=notice.original_filename,
                status=notice.status,
                title=notice.title,
                issuer=notice.issuer,
                category=notice.category,
                urgency=notice.urgency,
                page_count=notice.page_count,
                created_at=notice.created_at,
                next_due_date=min(due_dates) if due_dates else None,
                open_action_count=open_actions,
            )
        )
    return items


@router.get("/{notice_id}", response_model=NoticeDetail)
async def get_notice(notice_id: str, db: AsyncSession = Depends(get_db)) -> Notice:
    return await _get_notice_or_404(db, notice_id, with_relations=True)


@router.get("/{notice_id}/status", response_model=NoticeStatusOut)
async def get_status(notice_id: str, db: AsyncSession = Depends(get_db)) -> Notice:
    stmt = (
        select(Notice)
        .where(Notice.id == notice_id)
        .options(selectinload(Notice.events))
    )
    notice = (await db.execute(stmt)).scalars().first()
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found.")
    return notice


@router.get("/{notice_id}/pages", response_model=list[PageTextOut])
async def get_pages(notice_id: str, db: AsyncSession = Depends(get_db)) -> list:
    notice = await _get_notice_or_404(db, notice_id, with_relations=True)
    return sorted(notice.pages, key=lambda p: p.page_number)


@router.get("/{notice_id}/file")
async def get_file(notice_id: str, db: AsyncSession = Depends(get_db)) -> Response:
    notice = await _get_notice_or_404(db, notice_id)
    try:
        data = storage.read_file(notice.stored_path)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stored file is missing."
        ) from exc
    return Response(
        content=data,
        media_type=notice.content_type,
        headers={"Content-Disposition": f'inline; filename="{notice.original_filename}"'},
    )


@router.patch("/{notice_id}/actions/{action_id}", response_model=ActionOut)
async def update_action(
    notice_id: str,
    action_id: str,
    payload: ActionUpdate,
    db: AsyncSession = Depends(get_db),
) -> Action:
    action = (
        await db.execute(
            select(Action).where(Action.id == action_id, Action.notice_id == notice_id)
        )
    ).scalars().first()
    if action is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found.")
    action.status = payload.status
    await db.commit()
    await db.refresh(action)
    return action


@router.delete("/{notice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notice(notice_id: str, db: AsyncSession = Depends(get_db)) -> Response:
    notice = await _get_notice_or_404(db, notice_id)
    storage.delete_file(notice.stored_path)
    await db.delete(notice)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
