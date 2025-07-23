"""
postgres_server.py

Defines a FastMCP server exposing Postgres access via SQLAlchemy.
Imports centralized config and logger from config.py.
Provides a single MCP tool `query` to execute arbitrary SQL safely,
logging both successful and failed executions.
Handles module imports when running from the `server/` folder by
inserting the project root into sys.path.
"""
import os
import sys

# Ensure project root is on the module search path
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, basedir)

from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Central configuration and logger
from config import DB_URL, logger

# Initialize FastMCP server instance
mcp = FastMCP("PostgresMCPServer")

# Initialize SQLAlchemy engine with connection ping
engine = create_engine(DB_URL, pool_pre_ping=True)

# Test DB connection and log result at server startup
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Successfully connected to the Postgres database.")
except SQLAlchemyError as exc:
    logger.error(f"Failed to connect to the Postgres database: {exc}")

@mcp.tool()
def query(sql: str = None) -> list[dict]:
    """
    Execute a SQL query against the configured Postgres database.

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
        return [{"error": error_msg, "example": "SELECT current_user, current_database()"}]
    
    logger.info(f"Received SQL query request: {sql}")
    try:
        logger.info("Attempting database connection...")
        with engine.connect() as conn:
            logger.info("Database connection established, executing query...")
            result = conn.execute(text(sql))
            # Handle different SQLAlchemy result types
            if result.returns_rows:
                rows = [dict(row) for row in result.mappings()]
                logger.info(f"Query executed successfully, returned {len(rows)} rows")
            else:
                rows = [{"affected_rows": result.rowcount, "operation": "completed"}]
                logger.info(f"Query executed successfully, affected {result.rowcount} rows")
        logger.info(f"Successfully executed SQL: {sql}")
        return rows
    except SQLAlchemyError as exc:
        error_msg = f"SQL execution failed: {str(exc)}"
        logger.error(error_msg)
        logger.error(f"Failed SQL query was: {sql}")
        return [{"error": error_msg}]
    except Exception as exc:
        error_msg = f"Unexpected error: {str(exc)}"
        logger.error(error_msg)
        logger.error(f"Failed SQL query was: {sql}")
        return [{"error": error_msg}]

@mcp.tool()
def list_tables(schema: str = "advp") -> dict:
    """
    List all tables in the specified schema.

    Args:
        schema (str): The schema name to list tables from. Defaults to 'advp'.

    Returns:
        dict: A dictionary containing table information and metadata.
    """
    logger.info(f"Listing tables in schema: {schema}")
    try:
        with engine.connect() as conn:
            # Get tables with additional metadata
            result = conn.execute(text("""
                SELECT 
                    table_name,
                    table_type,
                    CASE 
                        WHEN table_type = 'BASE TABLE' THEN 'table'
                        WHEN table_type = 'VIEW' THEN 'view'
                        ELSE LOWER(table_type)
                    END as object_type
                FROM information_schema.tables 
                WHERE table_schema = :schema
                ORDER BY table_name
            """), {"schema": schema})
            
            tables = [dict(row) for row in result.mappings()]
            
            # Get row counts for tables (not views)
            table_info = []
            for table in tables:
                if table['object_type'] == 'table':
                    try:
                        count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{schema}"."{table["table_name"]}"'))
                        row_count = count_result.scalar()
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
    """
    Test the database connection and return basic information.

    Returns:
        dict: Connection status and basic database information.
    """
    logger.info("Testing database connection...")
    try:
        with engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT current_user, current_database(), version()"))
            row = dict(result.mappings().fetchone())
            
            # Get table count
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'advp'"))
            table_count = result.scalar()
            
            info = {
                "status": "connected",
                "user": row["current_user"],
                "database": row["current_database"],
                "version": row["version"],
                "table_count": table_count,
                "connection_url": "postgresql://connect:***@localhost:5435/advp"
            }
            logger.info(f"Database connection test successful: {info}")
            return info
            
    except Exception as exc:
        error_info = {
            "status": "failed",
            "error": str(exc),
            "connection_url": "postgresql://connect:***@localhost:5435/advp"
        }
        logger.error(f"Database connection test failed: {error_info}")
        return error_info