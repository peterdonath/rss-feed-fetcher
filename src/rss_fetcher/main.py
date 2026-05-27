"""Entry point for the RSS Feed Fetcher application."""

from __future__ import annotations

import logging

import click

from rss_fetcher.config import get_settings
from rss_fetcher.mcp_server import init_session_factory, run_sse_server, run_stdio_server
from rss_fetcher.scheduler import create_scheduler, run_with_signal_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


@click.group()
def cli() -> None:
    """RSS Feed Fetcher - Fetches RSS feeds and stores items in PostgreSQL."""
    pass


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

    import asyncio

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
