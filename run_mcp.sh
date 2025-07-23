#!/bin/bash
# run_mcp.sh - Wrapper script for Claude Desktop to ensure correct working directory

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Run the MCP server with uv
exec uv run python main.py
