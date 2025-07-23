#!/usr/bin/env python3
"""
test_connection.py - Simple test script to verify MCP server and database connectivity
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from config import DB_URL, logger
    from sqlalchemy import create_engine, text
    
    print("Testing PostgreSQL connection...")
    engine = create_engine(DB_URL, pool_pre_ping=True)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ Database connection successful!")
        print(f"📊 PostgreSQL version: {version}")
        
    print("\nTesting MCP server import...")
    from servers.postgres_server import mcp
    print("✅ MCP server import successful!")
    
    # Check server attributes safely
    server_name = getattr(mcp, 'name', getattr(mcp, '_name', 'PostgresMCPServer'))
    print(f"🔧 Server name: {server_name}")
    
    # Check if tools are registered
    tools = getattr(mcp, '_tools', {})
    if tools:
        print(f"🛠️ Registered tools: {list(tools.keys())}")
    else:
        print("🛠️ No tools found (this might be normal)")
    
    print("\n🎉 All tests passed! Your MCP server is ready to use.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
