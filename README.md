# PostgreSQL MCP Server

A simple [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for secure PostgreSQL access from AI tools like Claude Desktop and Zed Editor.

## What does this project do?
- Lets AI assistants connect to your PostgreSQL database securely
- Provides tools to test connection, run SQL queries, and list tables
- Works on Linux, macOS, and Windows

## Quick Start

### 1. Prerequisites
- Python 3.13+
- PostgreSQL database
- [`uv`](https://docs.astral.sh/uv/) package manager

### 2. Install & Configure
```bash
git clone https://github.com/Nayab-zak/mcp-postgres-server.git
cd mcp-postgres-server
uv sync
cp .env.example .env  # Edit .env with your DB details
```

### 3. Run the Server
- **Linux/macOS:**
  ```bash
  ./run_mcp.sh
  ```
- **Windows:**
  ```bat
  run_mcp.bat
  ```

Or, let Claude Desktop/Zed Editor start the server automatically when you ask a database question.

## How to Check if the Server is Running

- **Linux/macOS:**
  ```bash
  ps aux | grep "python main.py"
  # or
  ps aux | grep uv

  #or

  ps aux | grep PostgresMCPServer
  ```
- **Windows:**
  Open Command Prompt and run:
  ```bat
  tasklist | findstr python
  tasklist | findstr uv
  ```

## How It Works
- The server starts automatically when Claude Desktop or Zed Editor needs it
- It stops when you close the editor
- You can also run it manually for testing

## Minimal Manual Testing
```bash
uv run python test_connection.py  # Test DB connection
uv run python main.py             # Run server directly
```

---

For advanced configuration, see the example config files in `client_json_config_example/`.