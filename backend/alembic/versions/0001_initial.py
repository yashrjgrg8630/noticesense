"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


notice_status = sa.Enum(
    "uploaded", "extracting", "analyzing", "completed", "failed", name="notice_status"
)
extraction_method = sa.Enum("native", "ocr", "mixed", name="extraction_method")
action_status = sa.Enum(
    "pending", "in_progress", "done", "dismissed", name="action_status"
)


def upgrade() -> None:
    bind = op.get_bind()
    notice_status.create(bind, checkfirst=True)
    extraction_method.create(bind, checkfirst=True)
    action_status.create(bind, checkfirst=True)

    op.create_table(
        "notices",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("stored_path", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("status", notice_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("extraction_method", extraction_method, nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("issuer", sa.String(length=512), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("urgency", sa.String(length=32), nullable=True),
        sa.Column("reference_number", sa.String(length=256), nullable=True),
        sa.Column("ai_provider", sa.String(length=32), nullable=True),
        sa.Column("ai_model", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notices_sha256", "notices", ["sha256"])
    op.create_index("ix_notices_status", "notices", ["status"])
    op.create_index("ix_notices_category", "notices", ["category"])

    op.create_table(
        "notice_pages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("notice_id", sa.String(length=36), sa.ForeignKey("notices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("char_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("used_ocr", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_notice_pages_notice_id", "notice_pages", ["notice_id"])

    op.create_table(
        "deadlines",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("notice_id", sa.String(length=36), sa.ForeignKey("notices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(length=512), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
    )
    op.create_index("ix_deadlines_notice_id", "deadlines", ["notice_id"])
    op.create_index("ix_deadlines_due_date", "deadlines", ["due_date"])

    op.create_table(
        "actions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("notice_id", sa.String(length=36), sa.ForeignKey("notices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", action_status, nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_actions_notice_id", "actions", ["notice_id"])
    op.create_index("ix_actions_status", "actions", ["status"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("notice_id", sa.String(length=36), sa.ForeignKey("notices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_messages_notice_id", "chat_messages", ["notice_id"])

    op.create_table(
        "processing_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("notice_id", sa.String(length=36), sa.ForeignKey("notices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_processing_events_notice_id", "processing_events", ["notice_id"])


def downgrade() -> None:
    op.drop_table("processing_events")
    op.drop_table("chat_messages")
    op.drop_table("actions")
    op.drop_table("deadlines")
    op.drop_table("notice_pages")
    op.drop_table("notices")

    bind = op.get_bind()
    action_status.drop(bind, checkfirst=True)
    extraction_method.drop(bind, checkfirst=True)
    notice_status.drop(bind, checkfirst=True)
