# Main goal of the applicaiton

The application fetches multiple rss feeds and stores the items in a database.
The application should be written in python and should be able to run on a server.

# Functional requirements
1. The application should be able to fetch rss feeds from multiple sources.
2. The application should be able to store the items in a database.
3. The application should be able to handle errors gracefully, such as network issues or invalid rss feeds.
4. The application should be able to update the items in the database when new items are found in the rss feeds.
5. The application should be able to ignore duplicate items when storing in the database.
6. The application should be able to provide a MCP interface for fetching the items from the database.
7. The application should fetch the rss feeds at regular intervals, such as every hour.
8. The application should update the feed items in the database when new items are found in the rss feeds, and should also keep items that are no longer present in the rss feeds.

# MCP Interface
1. The application should provide a MCP tool for fetching the items from the database, with options for filtering by feed source and date range.
2. The application should provide a MCP tool for adding new rss feeds to the application.
3. The application should provide a MCP tool for removing rss feeds from the application.
4. The application should provide a MCP tool for listing all the rss feeds that are currently being fetched by the application.
5. The MCP server should support SSE (Server-Sent Events) transport for remote clients, with stdio transport available for local use.

# Non-functional requirements
1. The application should be able to run on a server.
2. The application should be able to handle a large number of rss feeds and items in the database.
3. The application should be able to run continuously without crashing or consuming too much resources.
4. The application should be able to log errors and important events for debugging and monitoring purposes.
5. The application should be able to be easily deployed and configured on a server.
6. The application should be well-structured and comply with best practices for python development, such as using virtual environments and following PEP 8 guidelines.
7. The application should be able to be easily tested and maintained, with clear documentation and code comments.
8. The application should store the feed items in the database with all the relevant information, such as title, link, description, publication date, metadata and feed source.
9. The application should use postgres database for storing the items, and should be able to connect to the database using environment variables for configuration.
10. The MCP transport should be configurable via the MCP_TRANSPORT environment variable, supporting both stdio (for local use) and SSE (for remote clients). The MCP tools should be implemented as separate commands that can be executed from the command line.
11. The MCP server should expose separate tool endpoints
12. The application should be packaged in a docker container for easy deployment on a server, and should include a docker-compose file for setting up the application. The user should provide their own postgres database connection details through environment variables when running the container.
13. The MCP interface should not be authenticated, but should be designed in a way that it can be easily extended to support authentication in the future if needed.
14. The application should store all feedparser fields (enclosures, categories, contributors).