#!/bin/bash
# setup_mcp.sh - Setup script for MCP server

set -e

echo "🚀 Setting up PostgreSQL MCP Server..."

# Ensure we're in the project directory
cd "$(dirname "$0")"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv found: $(uv --version)"

# Sync dependencies
echo "📦 Installing dependencies..."
uv sync

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env with your PostgreSQL connection details:"
    echo "   DB_URL=postgresql://username:password@localhost:5432/database_name"
    echo ""
fi

# Test virtual environment
echo "🐍 Testing virtual environment..."
source .venv/bin/activate
python --version

# Test database connection
echo "🗄️ Testing database connection..."
if python test_connection.py; then
    echo ""
    echo "🎉 Setup complete! Your MCP server is ready to use."
    echo ""
    echo "📋 Next steps:"
    echo "  1. Make sure run_mcp.sh is executable: chmod +x run_mcp.sh"
    echo "  2. Add to Claude Desktop config: $(pwd)/run_mcp.sh"
    echo "  3. Test manually: uv run python main.py"
else
    echo ""
    echo "⚠️  Database connection failed. Please check your .env configuration."
    echo "   Edit .env file and run this script again."
fi
