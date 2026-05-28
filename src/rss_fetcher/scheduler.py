"""Scheduler for periodic RSS feed fetching."""

from __future__ import annotations

import asyncio
import logging
import signal

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rss_fetcher.config import Settings
from rss_fetcher.fetcher import fetch_items_for_feed
from rss_fetcher.models import Feed
from rss_fetcher.processor import save_items

logger = logging.getLogger(__name__)


def _create_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory."""
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(database_url, pool_size=5, max_overflow=10)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _fetch_all_feeds(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Fetch all configured feeds."""
    async with session_factory() as session:
        result = await session.execute(select(Feed))
        feeds = result.scalars().all()

        for feed in feeds:
            try:
                items = await fetch_items_for_feed(session, feed, Settings())
                if items:
                    await save_items(session, feed, items)
                await session.commit()
            except Exception as exc:
                logger.error("Error fetching feed %s: %s", feed.url, exc)
                await session.rollback()


def create_scheduler(settings: Settings) -> AsyncIOScheduler:
    """Create an APScheduler for periodic feed fetching."""
    scheduler = AsyncIOScheduler()
    session_factory = _create_session_factory(settings.database_url)

    scheduler.add_job(
        _fetch_all_feeds,
        "interval",
        seconds=settings.fetch_interval_seconds,
        id="fetch_feeds",
        max_instances=1,
        args=(session_factory,),
    )

    return scheduler


def run_with_signal_handlers(scheduler: AsyncIOScheduler) -> None:
    """Run the scheduler with signal handlers for graceful shutdown."""
    loop = asyncio.get_event_loop()

    def _shutdown(signum: int, frame: object | None) -> None:
        logger.info("Received signal %d, shutting down...", signum)
        scheduler.shutdown(wait=False)
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown, sig, None)

    try:
        scheduler.start()
        loop.run_forever()
    finally:
        scheduler.shutdown(wait=False)
