from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.base import AIProviderError
from app.ai.factory import get_provider
from app.core.database import get_db
from app.models.notice import ChatMessage, Notice, NoticePage, NoticeStatus
from app.schemas.notice import ChatMessageOut, ChatRequest
from app.services import chat_service

router = APIRouter(prefix="/notices", tags=["chat"])


@router.get("/{notice_id}/messages", response_model=list[ChatMessageOut])
async def list_messages(notice_id: str, db: AsyncSession = Depends(get_db)) -> list[ChatMessage]:
    notice = await db.get(Notice, notice_id)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found.")
    messages = (
        await db.execute(
            select(ChatMessage)
            .where(ChatMessage.notice_id == notice_id)
            .order_by(ChatMessage.created_at)
        )
    ).scalars().all()
    return list(messages)


@router.post("/{notice_id}/messages", response_model=list[ChatMessageOut])
async def post_message(
    notice_id: str,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> list[ChatMessage]:
    notice = await db.get(Notice, notice_id)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found.")
    if notice.status != NoticeStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This notice is still being processed. Chat is available once analysis completes.",
        )

    pages_rows = (
        await db.execute(
            select(NoticePage)
            .where(NoticePage.notice_id == notice_id)
            .order_by(NoticePage.page_number)
        )
    ).scalars().all()
    pages = [(p.page_number, p.text) for p in pages_rows if p.text.strip()]
    if not pages:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No document text is available to answer questions.",
        )

    history_rows = (
        await db.execute(
            select(ChatMessage)
            .where(ChatMessage.notice_id == notice_id)
            .order_by(ChatMessage.created_at)
        )
    ).scalars().all()
    history = [(m.role, m.content) for m in history_rows]

    user_message = ChatMessage(notice_id=notice_id, role="user", content=payload.message)
    db.add(user_message)
    await db.commit()

    try:
        provider = get_provider()
        answer, citations = await chat_service.answer_question(
            provider, pages, history, payload.message
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    assistant_message = ChatMessage(
        notice_id=notice_id,
        role="assistant",
        content=answer,
        citations=citations or None,
    )
    db.add(assistant_message)
    await db.commit()

    return [user_message, assistant_message]
