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
ALLOWED_SCHEMAS=DPW_DL,advp

# Comma-separated list of allowed tables (leave empty to allow all tables)
ALLOWED_TABLES=T_DA_HRLY_PROD_DTLS,T_DA_EQP_HRLY_PROD_DTLS,T_DA_DELAY_HRLY_PROD_DTLS,T_DA_CONTR_CYCLE_SUMRY,DM_TARGETS,T_SLA_HOURLY_DTLS,DELAYS_T2_2H,T_ACTIVITY_DESC,T_DELAYS_REMARKS,DELAYS_T2,DM_LINES,EDW_VOYAGE_BOX_STAT,TBL_GATE_TOKENS,TBL_GATE_TOKENS_PRED,T_DA_HOURLY_SUMMARY_LIVE,T_DA_HRLY_PRD_SRC,T_DA_HRLY_PRD_VERT,Voyages

**Optional: Limit Search Space (Filtering):**
You can restrict the MCP server to only access specific schemas and tables by adding these optional environment variables:

```env
# Comma-separated list of allowed schemas (leave empty to allow all)
ALLOWED_SCHEMAS=public,analytics,reporting

# Comma-separated list of allowed tables (leave empty to allow all)  
ALLOWED_TABLES=users,orders,products,customers,sales_data
```

**Benefits of Filtering:**
- 🔒 **Security**: Restrict access to sensitive tables
- ⚡ **Performance**: Faster queries by limiting search space
- 🎯 **Focus**: AI assistant only sees relevant tables
- 📊 **Organization**: Work with specific datasets

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

## 🔍 Schema & Table Filtering

For databases with many irrelevant tables, you can limit the search space by configuring filters in your `.env` file:

### Example Filtering Configuration:
```env
# Only allow access to these schemas
ALLOWED_SCHEMAS=public,analytics,reporting

# Only allow access to these tables  
ALLOWED_TABLES=users,orders,products,customers,sales_summary
```

### How Filtering Works:
- **Schema Filtering**: If `ALLOWED_SCHEMAS` is set, only those schemas are accessible
- **Table Filtering**: If `ALLOWED_TABLES` is set, only those tables are accessible across all schemas
- **Combined Filtering**: You can use both filters together for maximum control
- **No Configuration**: Leave both empty to access all schemas and tables

### Filtering Benefits:
- ✅ **Faster Discovery**: AI assistant finds relevant tables quickly
- ✅ **Security**: Prevent access to sensitive or system tables
- ✅ **Focus**: Work with specific datasets without distractions
- ✅ **Performance**: Reduced query overhead on metadata operations

### Usage Examples:
```bash
# Example 1: Analytics team workspace
ALLOWED_SCHEMAS=analytics,reporting
ALLOWED_TABLES=sales_data,customer_metrics,revenue_summary

# Example 2: Application development
ALLOWED_SCHEMAS=public,application
ALLOWED_TABLES=users,orders,products,sessions

# Example 3: Data science project
ALLOWED_SCHEMAS=ml_data,experiments
ALLOWED_TABLES=training_data,features,model_results
```

## 🛠️ Available Database Tools
- **`query`** - Execute SQL queries
- **`list_tables`** - Show all tables (filtered by configuration)
- **`list_available_schemas`** - Show all available schemas (filtered by configuration)
- **`describe_table`** - Get table structure (respects filtering)
- **`get_schema_relationships`** - Show table relationships (respects filtering)
- **`test_connection`** - Test database connectivity
- **`get_common_queries`** - Get useful query patterns and examples

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
