"""MCP server for RSS Feed Fetcher."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from mcp.server import Server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rss_fetcher.models import Feed, FeedItem

logger = logging.getLogger(__name__)

app = Server("rss-feed-fetcher")

# Global session factory — initialized in main
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_session_factory(database_url: str) -> None:
    """Set the session factory for the MCP server."""
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(database_url, pool_size=5, max_overflow=10)
    global _session_factory
    _session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class AddFeedRequest(BaseModel):
    url: str


class RemoveFeedRequest(BaseModel):
    url: str


class FetchItemsRequest(BaseModel):
    feed_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None


@app.list_tools()
async def list_tools() -> ListToolsResult:
    """List available MCP tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="list_feeds",
                description="List all RSS feeds that are currently being fetched.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name="add_feed",
                description="Add a new RSS feed to the application.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the RSS feed to add.",
                        },
                    },
                    "required": ["url"],
                },
            ),
            Tool(
                name="remove_feed",
                description="Remove an RSS feed from the application.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the RSS feed to remove.",
                        },
                    },
                    "required": ["url"],
                },
            ),
            Tool(
                name="fetch_items",
                description="Fetch feed items from the database with optional filtering.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "feed_id": {
                            "type": "string",
                            "description": "Filter by feed ID (optional).",
                        },
                        "start_date": {
                            "type": "string",
                            "description": (
                                "Filter items published after this date "
                                "(ISO format, optional)."
                            ),
                        },
                        "end_date": {
                            "type": "string",
                            "description": (
                                "Filter items published before this date "
                                "(ISO format, optional)."
                            ),
                        },
                    },
                    "required": [],
                },
            ),
        ]
    )


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle MCP tool calls."""
    if _session_factory is None:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: database not initialized")]
        )

    match name:
        case "list_feeds":
            return await _handle_list_feeds()
        case "add_feed":
            return await _handle_add_feed(AddFeedRequest.model_validate(arguments))
        case "remove_feed":
            return await _handle_remove_feed(RemoveFeedRequest.model_validate(arguments))
        case "fetch_items":
            return await _handle_fetch_items(FetchItemsRequest.model_validate(arguments))
        case _:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                is_error=True,
            )


async def _handle_list_feeds() -> CallToolResult:
    """Handle list_feeds tool call."""
    async with _session_factory() as session:
        result = await session.execute(select(Feed))
        feeds = result.scalars().all()

    feeds_list = [
        {
            "id": str(feed.id),
            "url": feed.url,
            "title": feed.title,
            "description": feed.description,
        }
        for feed in feeds
    ]

    return CallToolResult(content=[TextContent(type="text", text=str(feeds_list))])


async def _handle_add_feed(request: AddFeedRequest) -> CallToolResult:
    """Handle add_feed tool call."""
    async with _session_factory() as session:
        feed = Feed(id=UUID(int=0), url=request.url)
        session.add(feed)
        await session.commit()

    return CallToolResult(content=[TextContent(type="text", text=f"Feed added: {request.url}")])


async def _handle_remove_feed(request: RemoveFeedRequest) -> CallToolResult:
    """Handle remove_feed tool call."""
    async with _session_factory() as session:
        result = await session.execute(select(Feed).where(Feed.url == request.url))
        feed = result.scalar_one_or_none()

        if feed is None:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Feed not found: {request.url}")],
                is_error=True,
            )

        await session.delete(feed)
        await session.commit()

    return CallToolResult(content=[TextContent(type="text", text=f"Feed removed: {request.url}")])


async def _handle_fetch_items(request: FetchItemsRequest) -> CallToolResult:
    """Handle fetch_items tool call."""
    conditions = [FeedItem.removed_from_feed == False]  # noqa: E712

    if request.feed_id:
        conditions.append(FeedItem.feed_id == UUID(request.feed_id))

    if request.start_date:
        start = datetime.fromisoformat(request.start_date)
        conditions.append(FeedItem.published_at >= start)

    if request.end_date:
        end = datetime.fromisoformat(request.end_date)
        conditions.append(FeedItem.published_at <= end)

    async with _session_factory() as session:
        result = await session.execute(
            select(FeedItem)
            .join(Feed)
            .where(and_(*conditions))
            .order_by(FeedItem.published_at.desc())
            .limit(100)
        )
        items = result.scalars().all()

    items_list = [
        {
            "id": str(item.id),
            "feed_id": str(item.feed_id),
            "title": item.title,
            "link": item.link,
            "description": item.description,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "author": item.author,
        }
        for item in items
    ]

    return CallToolResult(content=[TextContent(type="text", text=str(items_list))])


async def run_stdio_server() -> None:
    """Run the MCP server with stdio transport."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


async def run_sse_server(host: str, port: int) -> None:
    """Run the MCP server with SSE transport."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await app.run(
                streams[0], streams[1], app.create_initialization_options()
            )

    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    starlette_app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages/", endpoint=handle_messages, methods=["POST"]),
        ]
    )

    import uvicorn

    config = uvicorn.Config(starlette_app, host=host, port=port)
    server = uvicorn.Server(config)
    await server.serve()
