@echo off
REM run_postgres_mcp.bat - Wrapper script for Claude Desktop on Windows to ensure correct working directory

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Change to the script directory
cd /d "%SCRIPT_DIR%"

REM Run the PostgreSQL MCP server with uv
uv run python postgres_main.py
