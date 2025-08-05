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

@mcp.tool()
def describe_table(table_name: str, schema: str = "public") -> dict:
    """
    Get detailed information about a specific table including columns, types, and projections.

    Args:
        table_name (str): The name of the table to describe. Required.
        schema (str): The schema name. Defaults to 'public'.

    Returns:
        dict: Detailed table information including columns, data types, projections, and row count.
    """
    logger.info(f"Describing Vertica table: {schema}.{table_name}")
    try:
        with vertica_python.connect(**connection_info) as conn:
            cursor = conn.cursor()
            
            # Get column information from Vertica system tables
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    data_type_length,
                    numeric_precision,
                    numeric_scale
                FROM v_catalog.columns 
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table_name))
            
            columns = []
            for row in cursor.fetchall():
                column_dict = {
                    'column_name': row[0],
                    'data_type': row[1],
                    'is_nullable': row[2],
                    'column_default': row[3],
                    'data_type_length': row[4],
                    'numeric_precision': row[5],
                    'numeric_scale': row[6]
                }
                columns.append(column_dict)
            
            if not columns:
                return {"error": f"Table '{schema}.{table_name}' not found"}
            
            # Get projection information (Vertica-specific)
            cursor.execute("""
                SELECT 
                    projection_name,
                    is_super_projection,
                    projection_column_count,
                    created_epoch
                FROM v_catalog.projections 
                WHERE anchor_table_name = %s AND projection_schema = %s
            """, (table_name, schema))
            
            projections = []
            for row in cursor.fetchall():
                proj_dict = {
                    'projection_name': row[0],
                    'is_super_projection': row[1],
                    'column_count': row[2],
                    'created_epoch': row[3]
                }
                projections.append(proj_dict)
            
            # Get row count
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{schema}"."{table_name}"')
                row_count = cursor.fetchone()[0]
            except:
                row_count = 'N/A'
            
            # Get table size information
            try:
                cursor.execute("""
                    SELECT 
                        used_bytes,
                        row_count as estimated_rows
                    FROM v_monitor.storage_containers 
                    WHERE schema_name = %s AND table_name = %s
                    LIMIT 1
                """, (schema, table_name))
                
                storage_info = cursor.fetchone()
                if storage_info:
                    used_bytes = storage_info[0]
                    estimated_rows = storage_info[1]
                else:
                    used_bytes = 'N/A'
                    estimated_rows = 'N/A'
            except:
                used_bytes = 'N/A'
                estimated_rows = 'N/A'
            
            table_info = {
                "schema": schema,
                "table_name": table_name,
                "row_count": row_count,
                "estimated_rows": estimated_rows,
                "used_bytes": used_bytes,
                "columns": columns,
                "projections": projections,
                "summary": {
                    "total_columns": len(columns),
                    "nullable_columns": len([c for c in columns if c['is_nullable']]),
                    "total_projections": len(projections),
                    "super_projections": len([p for p in projections if p['is_super_projection']])
                }
            }
            
            logger.info(f"Successfully described Vertica table {schema}.{table_name}")
            return table_info
            
    except Exception as exc:
        error_msg = f"Failed to describe table '{schema}.{table_name}': {str(exc)}"
        logger.error(error_msg)
        return {"error": error_msg}

@mcp.tool()
def get_schema_relationships(schema: str = "public") -> dict:
    """
    Get foreign key relationships and table dependencies in the Vertica schema.

    Args:
        schema (str): The schema name. Defaults to 'public'.

    Returns:
        dict: Information about table relationships and suggested joins.
    """
    logger.info(f"Getting Vertica schema relationships for: {schema}")
    try:
        with vertica_python.connect(**connection_info) as conn:
            cursor = conn.cursor()
            
            # Get foreign key relationships from Vertica system tables
            cursor.execute("""
                SELECT 
                    fk.table_name as source_table,
                    fk.column_name as source_column,
                    fk.reference_table_name as target_table,
                    fk.reference_column_name as target_column,
                    fk.constraint_name
                FROM v_catalog.foreign_keys fk
                WHERE fk.table_schema = %s
                ORDER BY fk.table_name, fk.column_name
            """, (schema,))
            
            relationships = []
            for row in cursor.fetchall():
                rel_dict = {
                    'source_table': row[0],
                    'source_column': row[1],
                    'target_table': row[2],
                    'target_column': row[3],
                    'constraint_name': row[4]
                }
                relationships.append(rel_dict)
            
            # Create suggested JOIN patterns
            join_suggestions = []
            for rel in relationships:
                join_pattern = f"""
-- Join {rel['source_table']} with {rel['target_table']}
SELECT * FROM "{schema}"."{rel['source_table']}" s
JOIN "{schema}"."{rel['target_table']}" t 
    ON s."{rel['source_column']}" = t."{rel['target_column']}"
                """.strip()
                join_suggestions.append({
                    "description": f"Join {rel['source_table']} → {rel['target_table']}",
                    "sql_pattern": join_pattern,
                    "relationship": rel
                })
            
            return {
                "schema": schema,
                "database_type": "Vertica",
                "relationships": relationships,
                "join_suggestions": join_suggestions,
                "summary": {
                    "total_relationships": len(relationships),
                    "connected_tables": len(set([r['source_table'] for r in relationships] + [r['target_table'] for r in relationships]))
                }
            }
            
    except Exception as exc:
        error_msg = f"Failed to get schema relationships for '{schema}': {str(exc)}"
        logger.error(error_msg)
        return {"error": error_msg}

@mcp.tool()
def get_common_queries() -> dict:
    """
    Get common query patterns and examples for the Vertica database.

    Returns:
        dict: Collection of useful Vertica query patterns and examples.
    """
    logger.info("Providing common Vertica query patterns")
    
    common_queries = {
        "basic_exploration": [
            {
                "description": "List all tables with projection info",
                "sql": """
SELECT 
    t.table_name,
    COUNT(p.projection_name) as projection_count,
    SUM(CASE WHEN p.is_super_projection THEN 1 ELSE 0 END) as super_projections
FROM v_catalog.tables t
LEFT JOIN v_catalog.projections p ON t.table_name = p.anchor_table_name
WHERE t.table_schema = 'public'
GROUP BY t.table_name
ORDER BY t.table_name;
                """.strip()
            },
            {
                "description": "Get table storage information",
                "sql": """
SELECT 
    schema_name,
    table_name,
    SUM(used_bytes) as total_bytes,
    SUM(row_count) as total_rows
FROM v_monitor.storage_containers
WHERE schema_name = 'public'
GROUP BY schema_name, table_name
ORDER BY total_bytes DESC;
                """.strip()
            }
        ],
        "performance_monitoring": [
            {
                "description": "Check query performance",
                "sql": """
SELECT 
    user_name,
    request_type,
    request_duration_ms,
    processed_row_count,
    LEFT(request, 100) as query_preview
FROM v_monitor.query_requests 
WHERE start_timestamp >= NOW() - INTERVAL '1 hour'
ORDER BY request_duration_ms DESC
LIMIT 10;
                """.strip()
            },
            {
                "description": "Monitor projection usage",
                "sql": """
SELECT 
    projection_schema,
    projection_name,
    used_count,
    last_used_time
FROM v_monitor.projection_usage
WHERE projection_schema = 'public'
ORDER BY used_count DESC;
                """.strip()
            }
        ],
        "data_analysis": [
            {
                "description": "Analyze column statistics",
                "sql": """
SELECT 
    schema_name,
    table_name,
    column_name,
    statistics_type,
    statistics_value
FROM v_catalog.column_statistics
WHERE schema_name = 'public'
ORDER BY table_name, column_name;
                """.strip()
            },
            {
                "description": "Check data distribution",
                "sql": """
-- Replace 'your_table' and 'your_column' with actual names
SELECT 
    your_column,
    COUNT(*) as frequency,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
FROM "public"."your_table"
GROUP BY your_column
ORDER BY frequency DESC
LIMIT 20;
                """.strip()
            }
        ]
    }
    
    return {
        "database_type": "Vertica",
        "default_schema": "public",
        "query_categories": common_queries,
        "vertica_specific_tips": [
            "Vertica is columnar - queries are optimized for analytics",
            "Use projections for query optimization",
            "COPY command is fastest for bulk data loading",
            "Check v_monitor schema for performance monitoring",
            "Use ANALYZE_STATISTICS to update column statistics"
        ],
        "optimization_tips": [
            "Create projections for frequently queried columns",
            "Use segmented projections for large tables",
            "Monitor query_requests table for slow queries",
            "Consider unsegmented projections for small lookup tables"
        ]
    }
