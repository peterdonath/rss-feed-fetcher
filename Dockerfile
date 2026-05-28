FROM python:3.11-slim

WORKDIR /app

# Copy application code
COPY src/ ./src/

# Install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Run the application
CMD ["rss-feed-fetcher", "run"]
