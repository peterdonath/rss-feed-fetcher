"""Configuration for the RSS Feed Fetcher application."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://rss_user:rss_password@localhost:5432/rss_feed_fetcher"

    # Fetching
    fetch_interval_seconds: int = 3600
    feed_urls: str = ""
    http_timeout: int = 30

    # MCP
    mcp_transport: str = "stdio"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8080


def get_settings() -> Settings:
    """Create and return application settings."""
    return Settings()
