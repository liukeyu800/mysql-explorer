# SQLite Explorer MCP Server

An MCP server that provides safe, read-only access to SQLite databases through Model Context Protocol (MCP). This server is built with the FastMCP framework, which enables LLMs to explore and query SQLite databases with built-in safety features and query validation.

## Installation

Install using FastMCP:

```bash
fastmcp install sqlite_explorer.py --name "SQLite Explorer" -e SQLITE_DB_PATH=/path/to/db
```

Replace `/path/to/db` with the path to your SQLite database file.

## MCP Tools

The server exposes the following tools to LLMs:

### read_query
Execute a SELECT query on the database with built-in safety validations.

### list_tables 
List all available tables in the database.

### describe_table
Get detailed schema information for a specific table.

## Safety Features

- Restricts queries to SELECT statements only (including WITH clauses)
- Prevents multiple statements in a single query
- Automatically adds row limits to prevent memory issues
- Uses parameterized queries to prevent SQL injection
- Read-only connection to protect data integrity

## Development Documentation

The repository includes two key documentation files for MCP development:

- `mcp-documentation.txt`: Contains comprehensive documentation about the Model Context Protocol, including concepts like resources, tools, prompts, and transports. Essential for understanding MCP's architecture and capabilities.

- `fastmcp-documentation.txt`: Provides specific documentation about FastMCP, including installation, configuration, and usage. Useful for understanding how to package and distribute MCP servers.

These files serve as context when developing MCP servers and can be used with LLMs to assist in development.

## Environment Variables

- `SQLITE_DB_PATH`: (Required) Full path to the SQLite database file

## Requirements

- Python 3.6+
- FastMCP
- SQLite3 database file