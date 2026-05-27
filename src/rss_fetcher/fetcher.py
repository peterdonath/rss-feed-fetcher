"""RSS Feed fetcher with error handling."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import feedparser
from sqlalchemy.ext.asyncio import AsyncSession

from rss_fetcher.config import Settings
from rss_fetcher.models import Feed, FeedItem

logger = logging.getLogger(__name__)


def parse_feed(feed_data: str) -> dict[str, Any]:
    """Parse RSS/Atom feed data.

    Returns a dict with feed-level metadata and list of items.
    """
    parsed = feedparser.parse(feed_data)
    return {
        "feed_title": parsed.feed.get("title"),
        "feed_description": parsed.feed.get("description"),
        "items": list(parsed.entries),
    }


def _extract_item_metadata(entry: dict[str, Any]) -> dict[str, Any]:
    """Extract all feedparser fields into a metadata dict."""
    metadata: dict[str, Any] = {}
    for key in ("enclosures", "categories", "contributors", "source", "summary_detail"):
        if key in entry:
            metadata[key] = entry[key]
    return metadata


def _parse_published(entry: dict[str, Any]) -> datetime | None:
    """Parse published date from feed entry."""
    for attr in ("published_parsed", "updated_parsed"):
        parsed = entry.get(attr)
        if parsed and parsed[0] > 0:
            return datetime(*parsed[:6], tzinfo=UTC)
    return None


async def fetch_and_parse_feed(
    session: AsyncSession,
    feed_url: str,
    settings: Settings,
) -> Feed | None:
    """Fetch a feed, parse it, and return the Feed record.

    Returns None if fetching fails.
    """
    import httpx

    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
            response = await client.get(feed_url)
            response.raise_for_status()
    except Exception as exc:
        logger.error("Failed to fetch feed %s: %s", feed_url, exc)
        return None

    try:
        data = parse_feed(response.text)
    except Exception as exc:
        logger.error("Failed to parse feed %s: %s", feed_url, exc)
        return None

    feed = await session.get(Feed, feed_url)
    if feed is None:
        feed = Feed(
            id=uuid4(),
            url=feed_url,
            title=data["feed_title"],
            description=data["feed_description"],
        )
        session.add(feed)
        await session.commit()

    return feed


async def fetch_items_for_feed(
    session: AsyncSession,
    feed: Feed,
    settings: Settings,
) -> list[FeedItem]:
    """Fetch all items from a feed and return new items.

    This does not persist items — call processor.save_items() afterward.
    """
    import httpx

    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
            response = await client.get(feed.url)
            response.raise_for_status()
    except Exception as exc:
        logger.error("Failed to fetch feed %s: %s", feed.url, exc)
        return []

    try:
        data = parse_feed(response.text)
    except Exception as exc:
        logger.error("Failed to parse feed %s: %s", feed.url, exc)
        return []

    items: list[FeedItem] = []
    for entry in data["items"]:
        guid = entry.get("id") or entry.get("link") or str(uuid4())
        item = FeedItem(
            feed_id=feed.id,
            guid=guid,
            title=entry.get("title"),
            link=entry.get("link"),
            description=entry.get("summary"),
            published_at=_parse_published(entry),
            author=entry.get("author"),
            metadata=_extract_item_metadata(entry),
        )
        items.append(item)

    return items
