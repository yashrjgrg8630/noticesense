from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class NoticeStatus(str, enum.Enum):
    uploaded = "uploaded"
    extracting = "extracting"
    analyzing = "analyzing"
    completed = "completed"
    failed = "failed"


class ExtractionMethod(str, enum.Enum):
    native = "native"
    ocr = "ocr"
    mixed = "mixed"


class ActionStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"
    dismissed = "dismissed"


class Notice(Base):
    __tablename__ = "notices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    status: Mapped[NoticeStatus] = mapped_column(
        Enum(NoticeStatus, name="notice_status"), default=NoticeStatus.uploaded, nullable=False, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extraction_method: Mapped[ExtractionMethod | None] = mapped_column(
        Enum(ExtractionMethod, name="extraction_method"), nullable=True
    )

    # AI-produced structured analysis
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    issuer: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    pages: Mapped[list[NoticePage]] = relationship(
        back_populates="notice", cascade="all, delete-orphan", order_by="NoticePage.page_number"
    )
    deadlines: Mapped[list[Deadline]] = relationship(
        back_populates="notice", cascade="all, delete-orphan", order_by="Deadline.due_date"
    )
    actions: Mapped[list[Action]] = relationship(back_populates="notice", cascade="all, delete-orphan")
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="notice", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )
    events: Mapped[list[ProcessingEvent]] = relationship(
        back_populates="notice", cascade="all, delete-orphan", order_by="ProcessingEvent.created_at"
    )


class NoticePage(Base):
    __tablename__ = "notice_pages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    notice_id: Mapped[str] = mapped_column(
        ForeignKey("notices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_ocr: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    notice: Mapped[Notice] = relationship(back_populates="pages")


class Deadline(Base):
    __tablename__ = "deadlines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    notice_id: Mapped[str] = mapped_column(
        ForeignKey("notices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(512), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)

    notice: Mapped[Notice] = relationship(back_populates="deadlines")


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    notice_id: Mapped[str] = mapped_column(
        ForeignKey("notices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus, name="action_status"), default=ActionStatus.pending, nullable=False, index=True
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    notice: Mapped[Notice] = relationship(back_populates="actions")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    notice_id: Mapped[str] = mapped_column(
        ForeignKey("notices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # List of {page_number, quote} objects backing an assistant answer.
    citations: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    notice: Mapped[Notice] = relationship(back_populates="messages")


class ProcessingEvent(Base):
    __tablename__ = "processing_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    notice_id: Mapped[str] = mapped_column(
        ForeignKey("notices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    notice: Mapped[Notice] = relationship(back_populates="events")
