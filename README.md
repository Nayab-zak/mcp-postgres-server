PostgreSQL MCP Server

A Model Context Protocol (MCP) server that provides secure PostgreSQL database access for AI assistants like Claude Desktop and Zed Editor.
Features

    🗄️ Direct PostgreSQL Access: Execute SQL queries safely through MCP protocol
    🔒 Secure Query Execution: Parameterized queries with comprehensive error handling
    📊 Database Exploration: Built-in tools to list tables and inspect schema
    🚀 Easy Setup: Simple configuration with uv package manager
    🔧 Editor Integration: Ready-to-use configs for Claude Desktop and Zed Editor

Quick Start
Prerequisites

    Python 3.13+
    PostgreSQL database
    uv package manager

Installation

Clone the repository:

git clone https://github.com/Nayab-zak/mcp-postgres-server.git
cd mcp-postgres-server

Install dependencies:

uv sync

Configure environment:

cp .env.example .env
# Edit .env with your PostgreSQL connection details

Set up database connection in .env:

DB_URL=postgresql://username:password@localhost:5432/database_name

Test the setup:

./setup_mcp.sh

Configuration
Claude Desktop
Linux/macOS

    Copy the configuration from claude_desktop_config.json
    Add it to your Claude Desktop config file (~/.config/claude/claude_desktop_config.json)
    Update the path in the config to point to your run_mcp.sh script:

{
  "mcpServers": {
    "postgres-mcp": {
      "command": "/full/path/to/your/mcp-postgres-server/run_mcp.sh"
    }
  }
}

Windows

    Copy the configuration from claude_desktop_config.json
    Add it to your Claude Desktop config file (%APPDATA%\Claude\claude_desktop_config.json)
    Update the path in the config to point to your run_mcp.bat script:

{
  "mcpServers": {
    "postgres-mcp": {
      "command": "C:\\full\\path\\to\\your\\mcp-postgres-server\\run_mcp.bat"
    }
  }
}

Zed Editor
Linux/macOS

    Copy the configuration from zed_settings.json
    Add it to your Zed settings (~/.config/zed/settings.json)
    Update the path to point to your run_mcp.sh script

Windows

    Copy the configuration from zed_settings.json
    Add it to your Zed settings (%APPDATA%\Zed\settings.json)
    Update the path to point to your run_mcp.bat script

Available Tools
Tool 	Description 	Example Usage
test_connection 	Test database connectivity and get info 	"Test the database connection"
query 	Execute SQL queries 	"Show me the first 5 users"
list_tables 	List all tables with metadata 	"List all tables in the database"
Usage Examples

Once connected to Claude Desktop or Zed:

    "Test the database connection" - Verify connectivity
    "List all tables in my database" - Explore schema
    "Show me the first 10 rows from users table" - Query data
    "Count how many records are in each table" - Get table sizes
    "Describe the structure of the orders table" - Inspect schema

How It Works

- The server starts automatically when Claude Desktop or Zed Editor needs it
- It stops when you close the editor
- You can also run it manually for testing
- **Autorestarting and lifecycle management is handled by Claude Desktop or Zed Editor—not by the run_mcp.sh or run_mcp.bat scripts.**

Benefits:

    🔋 Resource Efficient: Server only runs when needed
    🚀 Always Fresh: Each session starts with a clean server
    🛡️ Secure: No persistent connections left open
    🔄 Reliable: Auto-restart if anything goes wrong

Manual Testing

# Test database connection
uv run python test_connection.py

# Run MCP server directly
uv run python main.py

# Use the wrapper script
# Linux/macOS:
./run_mcp.sh

# Windows:
run_mcp.bat

Project Structure

mcp-postgres-server/
├── main.py                     # Entry point
├── config.py                   # Configuration and logging
├── servers/
│   └── postgres_server.py     # MCP server implementation
├── run_mcp.sh                 # Wrapper script for editors (Linux/macOS)
├── run_mcp.bat                # Wrapper script for editors (Windows)
├── setup_mcp.sh               # Setup and testing script
├── test_connection.py         # Database connection test
├── claude_desktop_config.json # Claude Desktop config template
├── zed_settings.json          # Zed Editor config template
├── .env.example               # Environment template
└── README.md                  # This file

Troubleshooting
Connection Issues

Database connection failed:

# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Verify credentials in .env file
cat .env

Server won't start:

# Test database connection
uv run python test_connection.py

# Check logs
tail -f logs/app.log

    Editor integration issues:
        Linux/macOS: Ensure full path to run_mcp.sh in editor config and make it executable: chmod +x run_mcp.sh
        Windows: Ensure full path to run_mcp.bat in editor config with proper backslashes
        Restart your editor after configuration changes

Security Notes

    Uses parameterized queries to prevent SQL injection
    Logs all database operations for auditing
    Supports read-only database users for enhanced security
    Error messages sanitized to prevent information leakage

License

This project is licensed under the MIT License - see the LICENSE file for details.
Contributing

    Fork the repository
    Create your feature branch (git checkout -b feature/amazing-feature)
    Commit your changes (git commit -m 'Add some amazing feature')
    Push to the branch (git push origin feature/amazing-feature)
    Open a Pull Request
