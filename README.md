# SQLite Explorer MCP Server

An MCP server that provides safe, read-only access to SQLite databases through Model Context Protocol (MCP). This server is built with the FastMCP framework, which enables LLMs to explore and query SQLite databases with built-in safety features and query validation.

## 📑 Table of Contents
- [MCP Tools](#%EF%B8%8F-mcp-tools)
- [Getting Started](#-getting-started)
- [Installation Options](#-installation-options)
  - [Claude Desktop](#option-1-install-for-claude-desktop)
  - [Cline VSCode Plugin](#option-2-install-for-cline-vscode-plugin)
- [Safety Features](#-safety-features)
- [Development Documentation](#-development-documentation)
- [Environment Variables](#%EF%B8%8F-environment-variables)
- [Requirements](#-requirements)

## 🛠️ MCP Tools

The server exposes the following tools to LLMs:

### read_query
Execute a SELECT query on the database with built-in safety validations.

### list_tables 
List all available tables in the database.

### describe_table
Get detailed schema information for a specific table.

## 🚀 Getting Started

Clone the repository:

```bash
git clone https://github.com/rooveterinary/sqlite-explorer-fastmcp-mcp-server.git
cd sqlite-explorer-fastmcp-mcp-server
```

## 📦 Installation Options

You can install this MCP server in either Claude Desktop or the Cline VSCode plugin. Choose the option that best suits your needs.

### Option 1: Install for Claude Desktop

Install using FastMCP:

```bash
fastmcp install sqlite_explorer.py --name "SQLite Explorer" -e SQLITE_DB_PATH=/path/to/db
```

Replace `/path/to/db` with the path to your SQLite database file.

### Option 2: Install for Cline VSCode Plugin

To use this server with the [Cline VSCode plugin](http://cline.bot):

1. In VSCode, click the server icon (☰) in the Cline plugin sidebar
2. Click the "Edit MCP Settings" button (✎)
3. Add the following configuration to the settings file:

```json
{
  "sqlite-explorer": {
    "command": "uv",
    "args": [
      "run",
      "--with",
      "fastmcp",
      "fastmcp",
      "run",
      "/path/to/repo/sqlite_explorer.py"
    ],
    "env": {
      "SQLITE_DB_PATH": "/path/to/your/database.db"
    }
  }
}
```

Replace:
- `/path/to/repo` with the full path to where you cloned this repository (e.g., `/Users/username/Projects/sqlite-explorer-fastmcp-mcp-server`)
- `/path/to/your/database.db` with the full path to your SQLite database file

## 🔒 Safety Features

- Restricts queries to SELECT statements only (including WITH clauses)
- Prevents multiple statements in a single query
- Automatically adds row limits to prevent memory issues
- Uses parameterized queries to prevent SQL injection
- Read-only connection to protect data integrity

## 📚 Development Documentation

The repository includes two key documentation files for MCP development:

- `mcp-documentation.txt`: Contains comprehensive documentation about the Model Context Protocol, including concepts like resources, tools, prompts, and transports. Essential for understanding MCP's architecture and capabilities.

- `fastmcp-documentation.txt`: Provides specific documentation about FastMCP, including installation, configuration, and usage. Useful for understanding how to package and distribute MCP servers.

These files serve as context when developing MCP servers and can be used with LLMs to assist in development.

## ⚙️ Environment Variables

- `SQLITE_DB_PATH`: (Required) Full path to the SQLite database file

## 📋 Requirements

- Python 3.6+
- FastMCP
- SQLite3 database file