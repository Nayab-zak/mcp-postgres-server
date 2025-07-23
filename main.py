from servers.postgres_server import mcp

def main():
    """
    Starts the PostgresMCPServer using stdio transport.
    This is the standard way MCP servers communicate with clients
    like Claude Desktop app or Zed editor.
    """
    # For FastMCP, run() is a synchronous method that handles the stdio transport
    mcp.run()


if __name__ == "__main__":
    main()