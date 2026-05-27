"""Tests for database models."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from rss_fetcher.models import FeedItem


@pytest.mark.asyncio
async def test_create_feed(session, sample_feed):
    """Test creating a feed."""
    feed = await sample_feed()
    assert feed.id is not None
    assert feed.url == "https://example.com/feed"
    assert feed.title == "Example Feed"


@pytest.mark.asyncio
async def test_create_feed_item(session, sample_feed):
    """Test creating a feed item."""
    feed = await sample_feed()
    item = FeedItem(
        feed_id=feed.id,
        guid="test-guid-1",
        title="Test Item",
        link="https://example.com/item",
        description="Test description",
    )
    session.add(item)
    await session.commit()

    result = await session.execute(select(FeedItem).where(FeedItem.guid == "test-guid-1"))
    found = result.scalar_one()
    assert found.title == "Test Item"
    assert found.feed_id == feed.id


@pytest.mark.asyncio
async def test_feed_unique_constraint(session, sample_feed):
    """Test feed URL uniqueness."""
    await sample_feed(url="https://duplicate.com/feed")
    with pytest.raises(IntegrityError):
        await sample_feed(url="https://duplicate.com/feed")


@pytest.mark.asyncio
async def test_item_unique_constraint(session, sample_feed):
    """Test feed+guid uniqueness."""
    feed = await sample_feed()
    item = FeedItem(feed_id=feed.id, guid="unique-guid")
    session.add(item)
    await session.commit()

    with pytest.raises(IntegrityError):
        duplicate = FeedItem(feed_id=feed.id, guid="unique-guid")
        session.add(duplicate)
        await session.commit()
