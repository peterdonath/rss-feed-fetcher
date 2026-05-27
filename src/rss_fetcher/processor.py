"""Processor for deduplicating and storing feed items."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rss_fetcher.models import Feed, FeedItem

logger = logging.getLogger(__name__)


async def _get_existing_guids(session: AsyncSession, feed_id: UUID) -> set[str]:
    """Get all existing GUIDs for a feed."""
    result = await session.execute(select(FeedItem.guid).where(FeedItem.feed_id == feed_id))
    return {row[0] for row in result.all()}


async def _mark_removed_items(
    session: AsyncSession,
    feed_id: UUID,
    existing_guids: set[str],
    current_guids: set[str],
) -> int:
    """Mark items that no longer appear in the feed."""
    removed_guids = existing_guids - current_guids
    if not removed_guids:
        return 0

    await session.execute(
        FeedItem.__table__.update()
        .where(FeedItem.feed_id == feed_id)
        .where(FeedItem.guid.in_(removed_guids))
        .values(removed_from_feed=True, updated_at=datetime.now(UTC))
    )
    logger.info("Marked %d items as removed from feed %s", len(removed_guids), feed_id)
    return len(removed_guids)


async def save_items(
    session: AsyncSession,
    feed: Feed,
    items: list[FeedItem],
) -> tuple[int, int, int]:
    """Save items to the database, skipping duplicates.

    Returns (inserted, skipped, removed) counts.
    """
    existing_guids = await _get_existing_guids(session, feed.id)
    current_guids = {item.guid for item in items}

    new_items = [item for item in items if item.guid not in existing_guids]
    skipped = len(items) - len(new_items)

    for item in new_items:
        session.add(item)

    removed_count = await _mark_removed_items(session, feed.id, existing_guids, current_guids)

    await session.commit()

    logger.info(
        "Feed %s: inserted=%d, skipped=%d, removed=%d",
        feed.url,
        len(new_items),
        skipped,
        removed_count,
    )

    return len(new_items), skipped, removed_count
