"""
vertica_server.py

Defines a FastMCP server exposing Vertica access via vertica-python.
Imports centralized config and logger from config.py.
Provides tools for `query`, `list_tables`, and `test_connection` to execute SQL safely,
logging both successful and failed executions.
"""
import os
import sys

# Ensure project root is on the module search path
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, basedir)

from mcp.server.fastmcp import FastMCP
import vertica_python

# Central configuration and logger
from config import VERTICA_HOST, VERTICA_PORT, VERTICA_DB, VERTICA_USER, VERTICA_PASSWORD, logger

# Initialize FastMCP server instance
mcp = FastMCP("VerticaMCPServer")

# Vertica connection parameters
connection_info = {
    'host': VERTICA_HOST,
    'port': int(VERTICA_PORT),
    'user': VERTICA_USER,
    'password': VERTICA_PASSWORD,
    'database': VERTICA_DB,
    'autocommit': True
}

# Test DB connection and log result at server startup
try:
    with vertica_python.connect(**connection_info) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
    logger.info("Successfully connected to the Vertica database.")
except Exception as exc:
    logger.error(f"Failed to connect to the Vertica database: {exc}")

@mcp.tool()
def query(sql: str = None) -> list[dict]:
    """
    Execute a SQL query against the configured Vertica database.

    Args:
        sql (str): The raw SQL statement to execute. Required.

    Returns:
        list[dict]: A list of rows returned by the query, each as a dict.
                    If an error occurs, returns a dict with an "error" key.
    """
    # Handle missing SQL parameter gracefully
    if sql is None or sql.strip() == "":
        error_msg = "SQL query is required. Please provide a valid SQL statement."
        logger.warning("Query tool called without SQL parameter")
        return [{"error": error_msg, "example": "SELECT current_user(), current_database()"}]
    
    logger.info(f"Received SQL query request: {sql}")
    try:
        logger.info("Attempting database connection...")
        with vertica_python.connect(**connection_info) as conn:
            logger.info("Database connection established, executing query...")
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # Check if query returns rows
            if cursor.description:
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                # Fetch all rows and convert to list of dicts
                rows = []
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    rows.append(row_dict)
                logger.info(f"Query executed successfully, returned {len(rows)} rows")
                return rows
            else:
                # Non-SELECT query (INSERT, UPDATE, DELETE, etc.)
                affected_rows = cursor.rowcount if hasattr(cursor, 'rowcount') else 0
                logger.info(f"Query executed successfully, affected {affected_rows} rows")
                return [{"affected_rows": affected_rows, "operation": "completed"}]
                
    except Exception as exc:
        error_msg = f"SQL execution failed: {str(exc)}"
        logger.error(error_msg)
        logger.error(f"Failed SQL query was: {sql}")
        return [{"error": error_msg}]

@mcp.tool()
def list_tables(schema: str = "public") -> dict:
    """
    List all tables in the specified schema.

    Args:
        schema (str): The schema name to list tables from. Defaults to 'public'.

    Returns:
        dict: A dictionary containing table information and metadata.
    """
    logger.info(f"Listing tables in schema: {schema}")
    try:
        with vertica_python.connect(**connection_info) as conn:
            cursor = conn.cursor()
            
            # Get tables with additional metadata for Vertica
            cursor.execute("""
                SELECT 
                    table_name,
                    table_type,
                    CASE 
                        WHEN table_type = 'TABLE' THEN 'table'
                        WHEN table_type = 'VIEW' THEN 'view'
                        ELSE LOWER(table_type)
                    END as object_type
                FROM v_catalog.tables 
                WHERE table_schema = %s
                ORDER BY table_name
            """, (schema,))
            
            columns = [desc[0] for desc in cursor.description]
            tables = []
            for row in cursor.fetchall():
                table_dict = dict(zip(columns, row))
                tables.append(table_dict)
            
            # Get row counts for tables (not views)
            table_info = []
            for table in tables:
                if table['object_type'] == 'table':
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM "{schema}"."{table["table_name"]}"')
                        row_count = cursor.fetchone()[0]
                        table['row_count'] = row_count
                    except:
                        table['row_count'] = 'N/A'
                else:
                    table['row_count'] = 'N/A'
                table_info.append(table)
            
            logger.info(f"Found {len(table_info)} tables in schema '{schema}'")
            return {
                "schema": schema,
                "table_count": len(table_info),
                "tables": table_info
            }
            
    except Exception as exc:
        error_msg = f"Failed to list tables in schema '{schema}': {str(exc)}"
        logger.error(error_msg)
        return {"error": error_msg, "schema": schema}

@mcp.tool()
def test_connection() -> dict:
    """
    Test the database connection and return basic information.

    Returns:
        dict: Connection status and basic database information.
    """
    logger.info("Testing Vertica database connection...")
    try:
        with vertica_python.connect(**connection_info) as conn:
            cursor = conn.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT current_user(), current_database(), version()")
            row = cursor.fetchone()
            
            # Get table count from public schema
            cursor.execute("SELECT COUNT(*) FROM v_catalog.tables WHERE table_schema = 'public'")
            table_count = cursor.fetchone()[0]
            
            info = {
                "status": "connected",
                "user": row[0],
                "database": row[1],
                "version": row[2][:100] + "..." if len(row[2]) > 100 else row[2],  # Truncate version
                "table_count": table_count,
                "connection_url": f"vertica://{VERTICA_USER}:***@{VERTICA_HOST}:{VERTICA_PORT}/{VERTICA_DB}"
            }
            logger.info(f"Vertica database connection test successful")
            return info
            
    except Exception as exc:
        error_info = {
            "status": "failed",
            "error": str(exc),
            "connection_url": f"vertica://{VERTICA_USER}:***@{VERTICA_HOST}:{VERTICA_PORT}/{VERTICA_DB}"
        }
        logger.error(f"Vertica database connection test failed: {error_info}")
        return error_info
