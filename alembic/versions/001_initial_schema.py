"""Initial schema for RSS Feed Fetcher.

Revision ID: 001
Revises:
Create Date: 2026-05-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feeds",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=True),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.Index("ix_feeds_url", "url", unique=True),
    )

    op.create_table(
        "feed_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("feed_id", UUID(as_uuid=True), sa.ForeignKey("feeds.id"), nullable=False),
        sa.Column("guid", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=True),
        sa.Column("link", sa.String, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("published_at", sa.DateTime, nullable=True),
        sa.Column("author", sa.String, nullable=True),
        sa.Column("fetched_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("removed_from_feed", sa.Boolean, server_default=sa.false()),
        sa.Index("ix_feed_items_feed_id_guid", "feed_id", "guid", unique=True),
    )


def downgrade() -> None:
    op.drop_table("feed_items")
    op.drop_table("feeds")
