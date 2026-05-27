"""SQLAlchemy models for RSS Feed Fetcher."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class Feed(Base):
    """Represents an RSS feed source."""

    __tablename__ = "feeds"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list[FeedItem]] = relationship(back_populates="feed", lazy="selectin")


class FeedItem(Base):
    """Represents an item from an RSS feed."""

    __tablename__ = "feed_items"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    feed_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("feeds.id"), nullable=False
    )
    guid: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    link: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    author: Mapped[str | None] = mapped_column(String, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    _metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    removed_from_feed: Mapped[bool] = mapped_column(Boolean, default=False)

    feed: Mapped[Feed] = relationship(back_populates="items")

    __table_args__ = (
        Index("ix_feed_items_feed_id_guid", "feed_id", "guid", unique=True),
    )
