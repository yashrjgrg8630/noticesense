from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.notice import ActionStatus, ExtractionMethod, NoticeStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DeadlineOut(ORMModel):
    id: str
    label: str
    due_date: date | None = None
    raw_text: str | None = None
    source_page: int | None = None


class ActionOut(ORMModel):
    id: str
    description: str
    status: ActionStatus
    due_date: date | None = None
    source_page: int | None = None
    sort_order: int


class ActionUpdate(BaseModel):
    status: ActionStatus


class PageOut(ORMModel):
    id: str
    page_number: int
    char_count: int
    used_ocr: bool


class ProcessingEventOut(ORMModel):
    id: str
    stage: str
    message: str
    progress: float
    created_at: datetime


class Citation(BaseModel):
    page_number: int
    quote: str


class ChatMessageOut(ORMModel):
    id: str
    role: str
    content: str
    citations: list[Citation] | None = None
    created_at: datetime


class NoticeListItem(ORMModel):
    id: str
    original_filename: str
    status: NoticeStatus
    title: str | None = None
    issuer: str | None = None
    category: str | None = None
    urgency: str | None = None
    page_count: int
    created_at: datetime
    next_due_date: date | None = None
    open_action_count: int = 0


class NoticeDetail(ORMModel):
    id: str
    original_filename: str
    content_type: str
    file_size: int
    status: NoticeStatus
    error_message: str | None = None
    page_count: int
    extraction_method: ExtractionMethod | None = None
    title: str | None = None
    issuer: str | None = None
    category: str | None = None
    summary: str | None = None
    urgency: str | None = None
    reference_number: str | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
    created_at: datetime
    updated_at: datetime
    analyzed_at: datetime | None = None
    deadlines: list[DeadlineOut] = Field(default_factory=list)
    actions: list[ActionOut] = Field(default_factory=list)
    pages: list[PageOut] = Field(default_factory=list)


class NoticeStatusOut(ORMModel):
    id: str
    status: NoticeStatus
    error_message: str | None = None
    events: list[ProcessingEventOut] = Field(default_factory=list)


class UploadResponse(BaseModel):
    id: str
    status: NoticeStatus
    duplicate_of: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class PageTextOut(ORMModel):
    page_number: int
    text: str
    used_ocr: bool
