# rss-feed-fetcher

> **Spec-driven development trial** — This project was generated from [SPECIFICATION.md](SPECIFICATION.md) with the help of Qwen 3.6 LLM. It serves as a trial of the spec-driven development approach, where the specification document is the single source of truth and the implementation is derived directly from it.

A Python application that fetches RSS feeds at configurable intervals, stores items in a PostgreSQL database, and exposes an MCP (Model Context Protocol) server for querying and managing feeds.

## Features

- **Multi-feed fetching** — Fetch from any number of RSS/Atom feed sources
- **Deduplication** — Items are deduplicated by GUID to avoid storing duplicates
- **Soft-deletion** — Items that disappear from a feed are marked as removed rather than deleted
- **Rich metadata** — Stores all feedparser fields (enclosures, categories, contributors, source, etc.) in a JSON column
- **MCP interface** — Query and manage feeds via MCP tools with support for both stdio (local) and SSE (remote) transport
- **Configurable scheduling** — Fetch interval is configurable via environment variable
- **Docker support** — Ready to deploy with Docker and docker-compose
- **Graceful shutdown** — Handles SIGINT and SIGTERM for clean exit

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Feed parsing | [feedparser](https://github.com/kurtmckee/feedparser) |
| HTTP client | [httpx](https://www.python-httpx.org/) |
| Database | PostgreSQL via [asyncpg](https://github.com/MagicStack/asyncpg) |
| ORM | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (async) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) |
| Scheduling | [APScheduler](https://github.com/agronholm/apscheduler) |
| MCP server | [mcp](https://github.com/modelcontextprotocol/python-sdk) |
| API transport | [Starlette](https://www.starlette.io/) + [uvicorn](https://www.uvicorn.org/) |
| Configuration | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| CLI | [Click](https://click.palletsprojects.com/) |

## Project Structure

```
rss-feed-fetcher/
├── src/
│   └── rss_fetcher/
│       ├── __init__.py
│       ├── config.py          # Settings via pydantic-settings
│       ├── models.py          # SQLAlchemy models (Feed, FeedItem)
│       ├── fetcher.py         # HTTP fetching + feed parsing
│       ├── processor.py       # Deduplication + persistence
│       ├── scheduler.py       # APScheduler with periodic jobs
│       ├── mcp_server.py      # MCP server (stdio/SSE transport)
│       └── main.py            # CLI entry point (Click)
├── tests/                     # pytest test suite
├── alembic/                   # Database migrations
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env.example
```

## Prerequisites

- **Python 3.11 or later**
- **PostgreSQL 12+** (with a database created and accessible)

## Installation

### 1. Clone and set up the virtual environment

```bash
cd rss-feed-fetcher
python -m venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 2. Configure environment variables

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```ini
# PostgreSQL connection details
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/rss_feed_fetcher

# Fetching configuration (interval in seconds, default: 3600)
FETCH_INTERVAL_SECONDS=3600

# List of feed URLs to fetch (comma-separated)
# FEED_URLS=https://example.com/feed,https://another.com/rss

# MCP configuration
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8080
```

### 3. Run database migrations

```bash
alembic upgrade head
```

## Running the Application

### CLI commands

```bash
# Run the full application (scheduler + MCP server)
rss-feed-fetcher run

# Run only the MCP server (useful for debugging)
rss-feed-fetcher mcp
```

The `run` command starts both the periodic feed-fetching scheduler and the MCP server on a shared event loop. The `mcp` command runs only the MCP server.

> **Note:** The `server` command (deprecated) also starts both scheduler and MCP, but only runs the scheduler — use `run` instead.

### Docker

Build and run with docker-compose:

```bash
docker compose up --build
```

This starts the application and exposes the MCP SSE endpoint on port 8080 (configurable via `MCP_PORT`).

## MCP Interface

The application exposes an MCP server with four tools. The transport is controlled by the `MCP_TRANSPORT` environment variable:

- **`stdio`** — Standard I/O transport (for local clients like Claude Desktop)
- **`sse`** — Server-Sent Events transport (for remote HTTP clients)

### Available tools

#### `list_feeds`

List all configured feeds.

**Arguments:** None

**Example:**
```json
{
  "tool": "list_feeds",
  "arguments": {}
}
```

#### `add_feed`

Add a new RSS feed source.

**Arguments:**

| Name | Type | Required | Description |
|---|---|---|---|
| `url` | string | Yes | The URL of the RSS feed to add |

**Example:**
```json
{
  "tool": "add_feed",
  "arguments": {
    "url": "https://example.com/feed.xml"
  }
}
```

#### `remove_feed`

Remove an RSS feed source by its URL.

**Arguments:**

| Name | Type | Required | Description |
|---|---|---|---|
| `url` | string | Yes | The URL of the RSS feed to remove |

**Example:**
```json
{
  "tool": "remove_feed",
  "arguments": {
    "url": "https://example.com/feed.xml"
  }
}
```

#### `fetch_items`

Fetch items from the database, with optional filtering.

**Arguments:**

| Name | Type | Required | Description |
|---|---|---|---|
| `feed_id` | string | No | Filter by feed ID (UUID) |
| `start_date` | string | No | Filter items published after this date (ISO 8601) |
| `end_date` | string | No | Filter items published before this date (ISO 8601) |

**Example:**
```json
{
  "tool": "fetch_items",
  "arguments": {
    "feed_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2026-01-01T00:00:00Z",
    "end_date": "2026-01-31T23:59:59Z"
  }
}
```

Returns up to 100 items, excluding those marked as removed from their feed.

### Client configuration example (HTTP SSE)

To connect an MCP client to the server running via SSE transport, configure it to use the HTTP endpoint:

```json
{
  "mcpServers": {
    "rss-feed-fetcher": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

This assumes the server is running with `MCP_TRANSPORT=sse` (the default) and `MCP_PORT=8080`.

## Database Schema

### `feeds`

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `url` | String | Feed URL (unique) |
| `title` | String | Feed title |
| `description` | String | Feed description |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

### `feed_items`

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `feed_id` | UUID | Foreign key to `feeds.id` |
| `guid` | String | Item identifier (indexed) |
| `title` | String | Item title |
| `link` | String | Item URL |
| `description` | Text | Item content |
| `published_at` | DateTime | Publication date |
| `author` | String | Item author |
| `fetched_at` | DateTime | When the item was fetched |
| `metadata` | JSON | Raw feedparser metadata (enclosures, categories, contributors, etc.) |
| `removed_from_feed` | Boolean | Soft-delete flag |

## Running Tests

```bash
pytest
pytest -v
pytest --cov=rss_fetcher --cov-report=term-missing
```

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://rss_user:rss_password@localhost:5432/rss_feed_fetcher` | PostgreSQL connection string |
| `FETCH_INTERVAL_SECONDS` | `3600` | Seconds between feed fetch cycles |
| `FEED_URLS` | `""` | Comma-separated list of feed URLs to seed on startup |
| `HTTP_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `MCP_TRANSPORT` | `"stdio"` | MCP transport: `stdio` or `sse` |
| `MCP_HOST` | `"0.0.0.0"` | SSE server bind address |
| `MCP_PORT` | `8080` | SSE server port |
