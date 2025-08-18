# PostgreSQL & Vertica MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that enables AI tools like Claude Desktop and Zed Editor to securely access PostgreSQL and Vertica databases.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.13+
- PostgreSQL or Vertica database
- [`uv`](https://docs.astral.sh/uv/) package manager

### 2. Installation
```bash
git clone https://github.com/Nayab-zak/mcp-postgres-server.git
cd mcp-postgres-server
uv sync
```

### 3. Configuration
Create a `.env` file with your database credentials:

**For PostgreSQL:**
```env
DB_URL=postgresql://username:password@localhost:5432/database_name
```

**For Vertica:**
```env
VERTICA_HOST=localhost
VERTICA_PORT=5433
VERTICA_DB=VMart
VERTICA_USER=dbadmin
VERTICA_PASSWORD=your_password
```

### 4. Editor Integration

**Claude Desktop:**
Copy the config content to `~/.config/claude/claude_desktop_config.json`:
```bash
# For PostgreSQL only
cp client_json_config_example/claude_desktop_config.json ~/.config/claude/claude_desktop_config.json

# For Vertica only
cp client_json_config_example/vertica_claude_desktop_config.json ~/.config/claude/claude_desktop_config.json

# For both databases
cp client_json_config_example/combined_claude_desktop_config.json ~/.config/claude/claude_desktop_config.json
```

**Zed Editor:**
Add the config content to your Zed settings file (`~/.config/zed/settings.json`):
```bash
# For PostgreSQL only
cat client_json_config_example/zed_settings.json >> ~/.config/zed/settings.json

# For Vertica only  
cat client_json_config_example/vertica_zed_settings.json >> ~/.config/zed/settings.json

# For both databases
cat client_json_config_example/combined_zed_settings.json >> ~/.config/zed/settings.json
```

### 5. Start Using
Once configured, ask your AI assistant database questions like:
- "List all tables in the database"
- "Show me the structure of the users table"
- "What are the relationships between tables?"

The server will start automatically when needed.

## 🛠️ Available Database Tools
- **`query`** - Execute SQL queries
- **`list_tables`** - Show all tables
- **`describe_table`** - Get table structure
- **`get_schema_relationships`** - Show table relationships
- **`test_connection`** - Test database connectivity

## 🧑‍💻 Manual Testing
```bash
# Test connections
uv run python test_connection.py          # PostgreSQL
uv run python test_vertica_connection.py  # Vertica

# Run servers directly
uv run python postgres_main.py            # PostgreSQL
uv run python vertica_main.py             # Vertica
```

## 🛟 Troubleshooting
- **Connection issues:** Verify database is running and credentials in `.env` are correct
- **Server won't start:** Run test scripts above to check connectivity
- **Editor integration:** Ensure full paths in config files and restart editor after changes
