"""Test fixtures for RSS Feed Fetcher."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rss_fetcher.models import Base, Feed


@pytest.fixture
def test_db_url() -> str:
    """Return a test database URL (uses in-memory SQLite by default)."""
    return os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture
async def engine(test_db_url):
    """Create a test database engine."""
    from sqlalchemy.ext.asyncio import create_async_engine as _create

    eng = _create(test_db_url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture
async def session_factory(engine):
    """Create a test session factory."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def session(session_factory):
    """Provide a test session."""
    async with session_factory() as s:
        yield s


@pytest.fixture
def sample_feed(session_factory):
    """Create a sample feed in the database."""
    async def _create(url: str = "https://example.com/feed", title: str = "Example Feed") -> Feed:
        async with session_factory() as s:
            feed = Feed(id=uuid4(), url=url, title=title)
            s.add(feed)
            await s.commit()
            await s.refresh(feed)
            return feed
    return _create
