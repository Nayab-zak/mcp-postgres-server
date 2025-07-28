# PostgreSQL MCP Server

A professional [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for secure PostgreSQL access from AI tools like Claude Desktop and Zed Editor.

---

## 🚀 Features
- **Direct PostgreSQL Access:** Securely run SQL queries from AI assistants
- **Easy Integration:** Works out-of-the-box with Claude Desktop and Zed Editor
- **Cross-Platform:** Supports Linux, macOS, and Windows
- **Automatic Lifecycle:** Server starts/stops automatically with your editor
- **Safe & Audited:** Parameterized queries, error handling, and logging

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.13+
- PostgreSQL database
- [`uv`](https://docs.astral.sh/uv/) package manager

### 2. Installation
```bash
git clone https://github.com/Nayab-zak/mcp-postgres-server.git
cd mcp-postgres-server
uv sync
cp .env.example .env  # Edit .env with your DB details
```

### 3. Configuration
- Edit `.env` with your PostgreSQL connection string:
  ```env
  DB_URL=postgresql://username:password@localhost:5432/database_name
  ```
- For Claude Desktop/Zed Editor, see `client_json_config_example/` for ready-to-use config templates.

### 4. Run the Server
- **Linux/macOS:**
  ```bash
  ./run_mcp.sh
  ```
- **Windows:**
  ```bat
  run_mcp.bat
  ```
- Or let Claude Desktop/Zed Editor start the server automatically when you ask a database question.

---

## 🖥️ How to Check if the Server is Running
- **Linux/macOS:**
  ```bash
  ps aux | grep PostgresMCPServer
  # or
  ps aux | grep "python main.py"
  ```
- **Windows:**
  ```bat
  tasklist | findstr PostgresMCPServer
  tasklist | findstr python
  ```
- If you only see the `grep`/`findstr` line, the server is not running.

---

## 🔄 Server Lifecycle
- **Automatic:** The server starts/stops automatically with Claude Desktop or Zed Editor.
- **Manual:** You can start/stop it from the terminal for testing.
- **No need to restart manually** during normal use—the editor manages it for you.

---

## 🛠️ Available Tools
| Tool             | Description                        | Example Usage                      |
|------------------|------------------------------------|------------------------------------|
| `test_connection`| Test DB connectivity               | "Test the database connection"     |
| `query`          | Execute SQL queries                | "Show me the first 5 users"        |
| `list_tables`    | List all tables with metadata      | "List all tables in the database"  |

---

## 🧑‍💻 Manual Testing
```bash
uv run python test_connection.py  # Test DB connection
uv run python main.py             # Run server directly
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
- **Connection failed?**
  - Check PostgreSQL is running: `pg_isready -h localhost -p 5432`
  - Verify credentials in `.env`
- **Server won't start?**
  - Test DB connection: `uv run python test_connection.py`
  - Check logs: `tail -f logs/app.log`
- **Editor integration issues?**
  - Linux/macOS: Ensure full path to `run_mcp.sh` in editor config and make it executable: `chmod +x run_mcp.sh`
  - Windows: Ensure full path to `run_mcp.bat` in editor config with proper backslashes
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
