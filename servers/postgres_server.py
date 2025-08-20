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
from config import is_schema_allowed, is_table_allowed, get_schema_filter_sql, get_table_filter_sql, filter_tables_list, validate_table_access, get_default_schema
from config import ALLOWED_SCHEMAS_LIST, ALLOWED_TABLES_LIST
from config import validate_sql_access

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
        # Validate SQL against allowed schema/table filters
        ok, err = validate_sql_access(sql, default_schema=get_default_schema("public"))
        if not ok:
            logger.warning(f"Blocked SQL due to scope restriction: {err}")
            return [{"error": err, "note": "Query restricted by ALLOWED_SCHEMAS/ALLOWED_TABLES in .env"}]
        logger.info("Attempting database connection...")
        with engine.connect() as conn:
            logger.info("Database connection established, executing query...")
            # Constrain name resolution to allowed schemas only
            if ALLOWED_SCHEMAS_LIST:
                schema_list = ", ".join([f'"{s}"' for s in ALLOWED_SCHEMAS_LIST])
                try:
                    conn.execute(text(f"SET search_path TO {schema_list}"))
                except Exception as _e:
                    logger.warning(f"Failed to set search_path: {_e}")
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
def list_tables(schema: str = None) -> dict:
    """
    List all tables in the specified schema.

    Args:
        schema (str): The schema name to list tables from. Uses first allowed schema or 'public' if not specified.

    Returns:
        dict: A dictionary containing table information and metadata.
    """
    # Use dynamic default schema if none provided
    if schema is None:
        schema = get_default_schema("public")
    
    # Check if schema is allowed
    if not is_schema_allowed(schema):
        available_schemas = ", ".join(ALLOWED_SCHEMAS_LIST) if ALLOWED_SCHEMAS_LIST else "all schemas"
        return {
            "error": f"Schema '{schema}' is not allowed. Available schemas: {available_schemas}",
            "allowed_schemas": ALLOWED_SCHEMAS_LIST
        }
    
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
            
            # Apply table filtering if configured
            if ALLOWED_TABLES_LIST:
                tables = [table for table in tables if table['table_name'] in ALLOWED_TABLES_LIST]
            
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
            
            # Add filtering metadata
            filter_info = {}
            if ALLOWED_SCHEMAS_LIST:
                filter_info["filtered_by_schemas"] = ALLOWED_SCHEMAS_LIST
            if ALLOWED_TABLES_LIST:
                filter_info["filtered_by_tables"] = ALLOWED_TABLES_LIST
                # Add information about which allowed tables were found
                found_tables = [t['table_name'] for t in table_info]
                available_allowed = [t for t in ALLOWED_TABLES_LIST if t in found_tables]
                missing_allowed = [t for t in ALLOWED_TABLES_LIST if t not in found_tables]
                if available_allowed:
                    filter_info["found_allowed_tables"] = available_allowed
                if missing_allowed:
                    filter_info["missing_allowed_tables"] = missing_allowed
            
            # Only return error if no tables found and we have table filtering
            if len(table_info) == 0 and ALLOWED_TABLES_LIST:
                return {
                    "error": f"No allowed tables found in schema '{schema}'. Allowed tables: {', '.join(ALLOWED_TABLES_LIST)}",
                    "schema": schema,
                    "allowed_tables": ALLOWED_TABLES_LIST
                }
            
            logger.info(f"Found {len(table_info)} tables in schema '{schema}' (after filtering)")
            result = {
                "schema": schema,
                "table_count": len(table_info),
                "tables": table_info
            }
            
            if filter_info:
                result["filtering_applied"] = filter_info
                
            return result
            
    except Exception as exc:
        error_msg = f"Failed to list tables in schema '{schema}': {str(exc)}"
        logger.error(error_msg)
        return {"error": error_msg, "schema": schema}

@mcp.tool()
def list_available_schemas() -> dict:
    """
    List all available schemas in the PostgreSQL database, filtered by allowed schemas.

    Returns:
        dict: Information about available schemas and filtering status.
    """
    logger.info("Listing available PostgreSQL schemas")
    try:
        with engine.connect() as conn:
            # Get all non-system schemas
            base_query = """
                SELECT 
                    schema_name,
                    schema_owner
                FROM information_schema.schemata
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            """
            
            # Add schema filtering if specified
            schema_filter = get_schema_filter_sql("schema_name")
            query = base_query + schema_filter + " ORDER BY schema_name"
            
            result = conn.execute(text(query))
            
            schemas = []
            for row in result.mappings():
                schema_dict = {
                    'schema_name': row['schema_name'],
                    'schema_owner': row['schema_owner']
                }
                schemas.append(schema_dict)
            
            result = {
                "total_schemas": len(schemas),
                "schemas": schemas
            }
            
            # Add filtering information
            if ALLOWED_SCHEMAS_LIST:
                result["filtering_applied"] = {
                    "filter_type": "allowed_schemas",
                    "allowed_schemas": ALLOWED_SCHEMAS_LIST
                }
            else:
                result["filtering_applied"] = {
                    "filter_type": "none",
                    "note": "All schemas are accessible"
                }
            
            logger.info(f"Found {len(schemas)} available schemas")
            return result
            
    except Exception as exc:
        error_msg = f"Failed to list schemas: {str(exc)}"
        logger.error(error_msg)
        return {"error": error_msg}

@mcp.tool()
def describe_table(table_name: str, schema: str = None) -> dict:
    """
    Get detailed information about a specific table including columns, types, and constraints.

    Args:
        table_name (str): The name of the table to describe. Required.
        schema (str): The schema name. Uses first allowed schema or 'public' if not specified.

    Returns:
        dict: Detailed table information including columns, data types, constraints, and row count.
    """
    # Use dynamic default schema if none provided
    if schema is None:
        schema = get_default_schema("public")
    
    # Check if schema is allowed
    if not is_schema_allowed(schema):
        available_schemas = ", ".join(ALLOWED_SCHEMAS_LIST) if ALLOWED_SCHEMAS_LIST else "all schemas"
        return {
            "error": f"Schema '{schema}' is not allowed. Available schemas: {available_schemas}",
            "allowed_schemas": ALLOWED_SCHEMAS_LIST
        }
    
    # Check if table is allowed (get list of available tables first for better error message)
    if ALLOWED_TABLES_LIST:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = :schema"), {"schema": schema})
                available_tables = [row[0] for row in result]
                
                is_allowed, error_msg = validate_table_access(table_name, available_tables)
                if not is_allowed:
                    return {"error": error_msg}
        except Exception as e:
            # If we can't check available tables, fall back to simple validation
            if not is_table_allowed(table_name):
                return {
                    "error": f"Table '{table_name}' is not in allowed tables: {', '.join(ALLOWED_TABLES_LIST)}",
                    "allowed_tables": ALLOWED_TABLES_LIST
                }
    
    logger.info(f"Describing table: {schema}.{table_name}")
    logger.info(f"Describing table: {schema}.{table_name}")
    try:
        with engine.connect() as conn:
            # Get column information
            columns_result = conn.execute(text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_schema = :schema AND table_name = :table_name
                ORDER BY ordinal_position
            """), {"schema": schema, "table_name": table_name})
            
            columns = [dict(row) for row in columns_result.mappings()]
            
            if not columns:
                return {"error": f"Table '{schema}.{table_name}' not found"}
            
            # Get constraints (primary keys, foreign keys, etc.)
            constraints_result = conn.execute(text("""
                SELECT 
                    tc.constraint_type,
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                LEFT JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                LEFT JOIN information_schema.constraint_column_usage ccu 
                    ON tc.constraint_name = ccu.constraint_name
                WHERE tc.table_schema = :schema AND tc.table_name = :table_name
            """), {"schema": schema, "table_name": table_name})
            
            constraints = [dict(row) for row in constraints_result.mappings()]
            
            # Get row count
            try:
                count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{schema}"."{table_name}"'))
                row_count = count_result.scalar()
            except:
                row_count = 'N/A'
            
            # Get table size (if available)
            try:
                size_result = conn.execute(text("""
                    SELECT pg_size_pretty(pg_total_relation_size(:full_table_name)) as table_size
                """), {"full_table_name": f"{schema}.{table_name}"})
                table_size = size_result.scalar()
            except:
                table_size = 'N/A'
            
            table_info = {
                "schema": schema,
                "table_name": table_name,
                "row_count": row_count,
                "table_size": table_size,
                "columns": columns,
                "constraints": constraints,
                "summary": {
                    "total_columns": len(columns),
                    "nullable_columns": len([c for c in columns if c['is_nullable'] == 'YES']),
                    "primary_keys": [c['column_name'] for c in constraints if c['constraint_type'] == 'PRIMARY KEY'],
                    "foreign_keys": [c for c in constraints if c['constraint_type'] == 'FOREIGN KEY']
                }
            }
            
            logger.info(f"Successfully described table {schema}.{table_name}")
            return table_info
            
    except Exception as exc:
        error_msg = f"Failed to describe table '{schema}.{table_name}': {str(exc)}"
        logger.error(error_msg)
        return {"error": error_msg}

@mcp.tool()
def get_schema_relationships(schema: str = None) -> dict:
    """
    Get foreign key relationships between tables in the schema.

    Args:
        schema (str): The schema name. Uses first allowed schema or 'public' if not specified.

    Returns:
        dict: Information about table relationships and suggested joins.
    """
    # Use dynamic default schema if none provided
    if schema is None:
        schema = get_default_schema("public")
    
    # Check if schema is allowed
    if not is_schema_allowed(schema):
        available_schemas = ", ".join(ALLOWED_SCHEMAS_LIST) if ALLOWED_SCHEMAS_LIST else "all schemas"
        return {
            "error": f"Schema '{schema}' is not allowed. Available schemas: {available_schemas}",
            "allowed_schemas": ALLOWED_SCHEMAS_LIST
        }
    
    logger.info(f"Getting schema relationships for: {schema}")
    try:
        with engine.connect() as conn:
            # Get foreign key relationships
            fk_result = conn.execute(text("""
                SELECT 
                    tc.table_name as source_table,
                    kcu.column_name as source_column,
                    ccu.table_name as target_table,
                    ccu.column_name as target_column,
                    tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON tc.constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_schema = :schema
                ORDER BY tc.table_name, kcu.column_name
            """), {"schema": schema})
            
            relationships = [dict(row) for row in fk_result.mappings()]
            
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
    Get common query patterns and examples for the PostgreSQL database.

    Returns:
        dict: Collection of useful query patterns and examples.
    """
    logger.info("Providing common query patterns")
    
    # Get dynamic default schema
    default_schema = get_default_schema("public")
    
    # Apply filtering information to query examples
    schema_filter_note = ""
    table_filter_note = ""
    
    if ALLOWED_SCHEMAS_LIST:
        schema_filter_note = f" (Filtered to schemas: {', '.join(ALLOWED_SCHEMAS_LIST)})"
    if ALLOWED_TABLES_LIST:
        table_filter_note = f" (Filtered to tables: {', '.join(ALLOWED_TABLES_LIST)})"
    
    common_queries = {
        "basic_exploration": [
            {
                "description": f"List all tables with row counts{schema_filter_note}{table_filter_note}",
                "sql": f"""
SELECT 
    schemaname,
    tablename,
    n_tup_ins as total_inserts,
    n_tup_upd as total_updates,
    n_tup_del as total_deletes
FROM pg_stat_user_tables 
WHERE schemaname = '{default_schema}'
ORDER BY tablename;
                """.strip()
            },
            {
                "description": f"Get table sizes{schema_filter_note}{table_filter_note}",
                "sql": f"""
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = '{default_schema}'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
                """.strip()
            }
        ],
        "data_quality": [
            {
                "description": "Check for duplicate records (example)",
                "sql": f"""
-- Replace 'your_table' and 'key_column' with actual names
SELECT key_column, COUNT(*) as duplicate_count
FROM "{default_schema}"."your_table"
GROUP BY key_column
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
                """.strip()
            },
            {
                "description": "Find null values in columns",
                "sql": f"""
-- Replace 'your_table' with actual table name
SELECT 
    COUNT(*) as total_rows,
    COUNT(column1) as non_null_column1,
    COUNT(column2) as non_null_column2
FROM "{default_schema}"."your_table";
                """.strip()
            }
        ],
        "performance": [
            {
                "description": "Show table statistics",
                "sql": f"""
SELECT 
    schemaname,
    tablename,
    attname as column_name,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = '{default_schema}'
ORDER BY tablename, attname;
                """.strip()
            }
        ]
    }
    
    result = {
        "database_type": "PostgreSQL",
        "default_schema": default_schema,
        "query_categories": common_queries,
        "tips": [
            f"Always specify schema in queries: \"{default_schema}\".\"table_name\"",
            "Use LIMIT when exploring large tables",
            "Use EXPLAIN ANALYZE to understand query performance",
            "Check pg_stat_user_tables for table usage statistics"
        ]
    }
    
    # Add filtering information
    if ALLOWED_SCHEMAS_LIST or ALLOWED_TABLES_LIST:
        result["filtering_active"] = {
            "allowed_schemas": ALLOWED_SCHEMAS_LIST if ALLOWED_SCHEMAS_LIST else "all",
            "allowed_tables": ALLOWED_TABLES_LIST if ALLOWED_TABLES_LIST else "all"
        }
    
    return result

@mcp.tool()
def test_connection() -> dict:
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
            
            # Get table count from default schema
            default_schema = get_default_schema("public")
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = :schema"), {"schema": default_schema})
            table_count = result.scalar()
            
            info = {
                "status": "connected",
                "user": row["current_user"],
                "database": row["current_database"],
                "version": row["version"],
                "table_count": table_count,
                "default_schema": default_schema,
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