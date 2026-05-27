"""Entry point for the RSS Feed Fetcher application."""

from __future__ import annotations

import asyncio
import logging
import signal

import click

from rss_fetcher.config import get_settings
from rss_fetcher.mcp_server import init_session_factory, run_sse_server, run_stdio_server
from rss_fetcher.scheduler import create_scheduler, run_with_signal_handlers

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


@click.group()
def cli() -> None:
    """RSS Feed Fetcher - Fetches RSS feeds and stores items in PostgreSQL."""
    pass


@cli.command()
def run() -> None:
    """Run the RSS Feed Fetcher (scheduler + MCP server)."""
    settings = get_settings()
    init_session_factory(settings.database_url)

    scheduler = create_scheduler(settings)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _shutdown(signum: int, frame: object | None) -> None:
        logger.info("Received signal %d, shutting down...", signum)
        scheduler.shutdown(wait=False)
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown, sig, None)

    loop.run_until_complete(_run_async(scheduler, settings))


async def _run_async(scheduler: object, settings: object) -> None:
    """Start scheduler and MCP server within a running event loop."""
    scheduler.start()  # type: ignore[union-attr]
    logger.info("Scheduler started — fetching every %d seconds", settings.fetch_interval_seconds)  # type: ignore[arg-type]

    match settings.mcp_transport:  # type: ignore[arg-type]
        case "stdio":
            logger.info("Starting MCP server (stdio transport)")
            await run_stdio_server()
        case "sse":
            logger.info(
                "Starting MCP server (SSE transport on %s:%d)",
                settings.mcp_host,
                settings.mcp_port,
            )
            await run_sse_server(settings.mcp_host, settings.mcp_port)
        case transport:
            click.echo(f"Unknown MCP transport: {transport}", err=True)
            raise click.exceptions.Exit(1)


@cli.command()
def server() -> None:
    """Run the RSS Feed Fetcher server (scheduler + MCP)."""
    settings = get_settings()
    init_session_factory(settings.database_url)

    scheduler = create_scheduler(settings)
    run_with_signal_handlers(scheduler)


@cli.command()
def mcp() -> None:
    """Run the MCP server only."""
    settings = get_settings()
    init_session_factory(settings.database_url)

    match settings.mcp_transport:
        case "stdio":
            asyncio.run(run_stdio_server())
        case "sse":
            asyncio.run(run_sse_server(settings.mcp_host, settings.mcp_port))
        case transport:
            click.echo(f"Unknown MCP transport: {transport}", err=True)
            raise click.exceptions.Exit(1)


if __name__ == "__main__":
    cli()
