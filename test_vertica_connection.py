#!/usr/bin/env python3
"""
Test script for the Vertica MCP server connection.
"""
import os
import sys

# Ensure we can import from the parent directory
sys.path.insert(0, os.path.dirname(__file__))

from servers.vertica_server import mcp

def test_vertica_connection():
    """Test the Vertica database connection using the MCP server's test_connection tool."""
    try:
        print("🔗 Testing Vertica MCP server connection...")
        
        # Import the test_connection function directly
        from servers.vertica_server import test_connection
        
        # Call the test_connection function
        result = test_connection()
        
        print("\n📊 Connection Test Results:")
        print("=" * 40)
        
        if result.get("status") == "connected":
            print("✅ Status: Connected")
            print(f"🏢 Database: {result.get('database', 'Unknown')}")
            print(f"👤 User: {result.get('user', 'Unknown')}")
            print(f"📋 Tables: {result.get('table_count', 'Unknown')}")
            print(f"🔗 Connection: {result.get('connection_url', 'Unknown')}")
            if 'version' in result:
                print(f"🏷️  Version: {result['version']}")
            return True
        else:
            print("❌ Status: Failed")
            print(f"💥 Error: {result.get('error', 'Unknown error')}")
            print(f"🔗 Connection: {result.get('connection_url', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"💥 Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Vertica MCP Server Connection Test")
    print("=" * 40)
    
    success = test_vertica_connection()
    
    if success:
        print("\n🎉 Vertica MCP server is ready to use!")
        sys.exit(0)
    else:
        print("\n❌ Vertica MCP server connection failed!")
        print("💡 Check your .env file and ensure Vertica is running.")
        sys.exit(1)
