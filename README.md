# PostgreSQL & Vertica MCP Server

A professional [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server providing## 🧩 Project Structure
```
mcp-postgres-server/
├── postgres_main.py               # PostgreSQL server entry point
├── vertica_main.py                # Vertica server entry point
├── config.py                      # Configuration and logging
├── servers/
│   ├── postgres_server.py         # PostgreSQL MCP server implementation
│   └── vertica_server.py          # Vertica MCP server implementation
├── run_postgres_mcp.sh / run_postgres_mcp.bat  # PostgreSQL wrapper scripts
├── run_vertica_mcp.sh / run_vertica_mcp.bat    # Vertica wrapper scripts
├── setup_mcp.sh                   # Setup and testing script
├── test_connection.py             # PostgreSQL connection test
├── test_vertica_connection.py     # Vertica connection test
├── client_json_config_example/    # Editor config templates for both servers
├── .env.example                   # Environment template
└── README.md                      # This file
```se access from AI tools like Claude Desktop and Zed Editor.

**Supports:** PostgreSQL and Vertica databases

---

## 🚀 Features
- **Dual Database Support:** PostgreSQL and Vertica database access
- **Direct Database Access:** Securely run SQL queries from AI assistants
- **Easy Integration:** Works out-of-the-box with Claude Desktop and Zed Editor
- **Cross-Platform:** Supports Linux, macOS, and Windows
- **Automatic Lifecycle:** Server starts/stops automatically with your editor
- **Safe & Audited:** Parameterized queries, error handling, and logging

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.13+
- PostgreSQL or Vertica database (or both)
- [`uv`](https://docs.astral.sh/uv/) package manager

### 2. Installation
```bash
git clone https://github.com/Nayab-zak/mcp-postgres-server.git
cd mcp-postgres-server
uv sync
cp .env.example .env  # Edit .env with your DB details
```

### 3. Configuration
Edit `.env` with your database connection strings:

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

For Claude Desktop/Zed Editor, see `client_json_config_example/` for ready-to-use config templates:
- `claude_desktop_config.json` - PostgreSQL only
- `vertica_claude_desktop_config.json` - Vertica only  
- `combined_claude_desktop_config.json` - Both servers
- `zed_settings.json` - PostgreSQL only for Zed
- `vertica_zed_settings.json` - Vertica only for Zed
- `combined_zed_settings.json` - Both servers for Zed

### 4. Run the Servers

**PostgreSQL Server:**
- **Linux/macOS:** `./run_postgres_mcp.sh`
- **Windows:** `run_postgres_mcp.bat`

**Vertica Server:**
- **Linux/macOS:** `./run_vertica_mcp.sh`  
- **Windows:** `run_vertica_mcp.bat`

Or let Claude Desktop/Zed Editor start the servers automatically when you ask database questions.

---

## 🖥️ How to Check if Servers are Running

**PostgreSQL Server:**
- **Linux/macOS:**
  ```bash
  ps aux | grep PostgresMCPServer
  # or
  ps aux | grep "python postgres_main.py"
  ```
- **Windows:**
  ```bat
  tasklist | findstr PostgresMCPServer
  tasklist | findstr python
  ```

**Vertica Server:**
- **Linux/macOS:**
  ```bash
  ps aux | grep VerticaMCPServer
  # or
  ps aux | grep "python vertica_main.py"
  ```
- **Windows:**
  ```bat
  tasklist | findstr VerticaMCPServer
  tasklist | findstr python
  ```

If you only see the `grep`/`findstr` line, the server is not running.

---

## 🔄 Server Lifecycle
- **Automatic:** Servers start/stop automatically with Claude Desktop or Zed Editor.
- **Manual:** You can start/stop them from the terminal for testing.
- **No need to restart manually** during normal use—the editor manages them for you.
- **Multiple servers:** You can run both PostgreSQL and Vertica servers simultaneously.

---

## 🛠️ Available Tools
| Tool             | Description                        | Example Usage                      |
|------------------|------------------------------------|------------------------------------|
| `test_connection`| Test DB connectivity               | "Test the database connection"     |
| `query`          | Execute SQL queries                | "Show me the first 5 users"        |
| `list_tables`    | List all tables with metadata      | "List all tables in the database"  |

---

## 🧑‍💻 Manual Testing

**PostgreSQL:**
```bash
uv run python test_connection.py      # Test PostgreSQL connection
uv run python postgres_main.py        # Run PostgreSQL server directly
```

**Vertica:**
```bash
uv run python test_vertica_connection.py  # Test Vertica connection
uv run python vertica_main.py             # Run Vertica server directly
```

---

## 🧩 Project Structure
```
mcp-postgres-server/
├── main.py                     # Entry point
├── config.py                   # Configuration and logging
├── servers/
│   └── postgres_server.py      # MCP server implementation
├── run_mcp.sh / run_mcp.bat    # Wrapper scripts
├── setup_mcp.sh                # Setup and testing script
├── test_connection.py          # DB connection test
├── client_json_config_example/ # Editor config templates
├── .env.example                # Environment template
└── README.md                   # This file
```

---

## 🛟 Troubleshooting

**Connection failed?**
- **PostgreSQL:** Check if PostgreSQL is running: `pg_isready -h localhost -p 5432`
- **Vertica:** Check if Vertica is running and accessible on the configured port
- Verify credentials in `.env`

**Server won't start?**
- **PostgreSQL:** Test connection: `uv run python test_connection.py`
- **Vertica:** Test connection: `uv run python test_vertica_connection.py`
- Check logs: `tail -f logs/app.log`

**Editor integration issues?**
- Linux/macOS: Ensure full path to wrapper scripts in editor config and make them executable
- Windows: Ensure full path to `.bat` scripts in editor config with proper backslashes
- Use the appropriate config templates in `client_json_config_example/`
- Restart your editor after config changes

---

## 🔒 Security Notes
- Parameterized queries prevent SQL injection
- All DB operations are logged
- Supports read-only DB users for safety
- Error messages are sanitized

---

## 📄 License
MIT License — see the LICENSE file for details.

## 🤝 Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request
