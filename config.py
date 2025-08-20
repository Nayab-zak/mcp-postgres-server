"""
config.py

Central configuration module for the FastMCP servers:
- Loads environment variables from a .env file
- Exposes application settings (DB_URL, LOG_PATH)
- Sets up structured, file‑based logging via dictConfig
"""
import os
from dotenv import load_dotenv
import logging
from logging.config import dictConfig
import re

# --- Load environment variables ---
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# --- Application settings ---
DB_URL = os.getenv("DB_URL")  # e.g. postgresql://user:pass@host:port/dbname

# Vertica configuration
VERTICA_HOST = os.getenv("VERTICA_HOST", "localhost")
VERTICA_PORT = os.getenv("VERTICA_PORT", "5433")
VERTICA_DB = os.getenv("VERTICA_DB", "VMart")
VERTICA_USER = os.getenv("VERTICA_USER", "dbadmin")
VERTICA_PASSWORD = os.getenv("VERTICA_PASSWORD", "")

# Construct Vertica connection URL
VERTICA_URL = f"vertica+vertica_python://{VERTICA_USER}:{VERTICA_PASSWORD}@{VERTICA_HOST}:{VERTICA_PORT}/{VERTICA_DB}"

# Schema and table filtering configuration
ALLOWED_SCHEMAS = os.getenv("ALLOWED_SCHEMAS", "").strip()  # Comma-separated list: "schema1,schema2"
ALLOWED_TABLES = os.getenv("ALLOWED_TABLES", "").strip()   # Comma-separated list: "table1,table2"

# Parse allowed schemas and tables into lists
def parse_filter_list(filter_string):
    """Parse comma-separated filter string into a list, removing empty strings"""
    if not filter_string:
        return []
    return [item.strip() for item in filter_string.split(",") if item.strip()]

ALLOWED_SCHEMAS_LIST = parse_filter_list(ALLOWED_SCHEMAS)
ALLOWED_TABLES_LIST = parse_filter_list(ALLOWED_TABLES)

# Helper functions for filtering
def is_schema_allowed(schema_name):
    """Check if a schema is allowed. If no schemas specified, allow all."""
    if not ALLOWED_SCHEMAS_LIST:
        return True
    return schema_name in ALLOWED_SCHEMAS_LIST

def is_table_allowed(table_name):
    """Check if a table is allowed. If no tables specified, allow all."""
    if not ALLOWED_TABLES_LIST:
        return True
    return table_name in ALLOWED_TABLES_LIST

def get_schema_filter_sql(schema_column_name="table_schema"):
    """Get SQL WHERE clause for schema filtering"""
    if not ALLOWED_SCHEMAS_LIST:
        return ""
    schemas_sql = ", ".join([f"'{schema}'" for schema in ALLOWED_SCHEMAS_LIST])
    return f" AND {schema_column_name} IN ({schemas_sql})"

def get_table_filter_sql(table_column_name="table_name"):
    """Get SQL WHERE clause for table filtering"""
    if not ALLOWED_TABLES_LIST:
        return ""
    tables_sql = ", ".join([f"'{table}'" for table in ALLOWED_TABLES_LIST])
    return f" AND {table_column_name} IN ({tables_sql})"

def filter_tables_list(tables_list, table_name_key="table_name"):
    """Filter a list of table dictionaries based on allowed tables"""
    if not ALLOWED_TABLES_LIST:
        return tables_list
    return [table for table in tables_list if table.get(table_name_key) in ALLOWED_TABLES_LIST]

def get_default_schema(fallback_schema="public"):
    """
    Get the default schema to use.
    Returns the first allowed schema if configured, otherwise the fallback.
    """
    if ALLOWED_SCHEMAS_LIST:
        return ALLOWED_SCHEMAS_LIST[0]
    return fallback_schema

def validate_table_access(table_name, available_tables=None):
    """
    Validate if a specific table can be accessed.
    Returns True if accessible, False with reason if not.
    Only restricts access if the table is specifically excluded, not if it's missing.
    """
    if not ALLOWED_TABLES_LIST:
        return True, None
    
    if table_name in ALLOWED_TABLES_LIST:
        return True, None
    
    # If table is not in allowed list but available_tables is provided,
    # check if any allowed tables exist
    if available_tables is not None:
        available_allowed = [t for t in ALLOWED_TABLES_LIST if t in available_tables]
        if available_allowed:
            return False, f"Table '{table_name}' is not in allowed tables. Available allowed tables: {', '.join(available_allowed)}"
        else:
            return False, f"None of the allowed tables ({', '.join(ALLOWED_TABLES_LIST)}) exist in this schema"
    
    return False, f"Table '{table_name}' is not in allowed tables: {', '.join(ALLOWED_TABLES_LIST)}"

# --- SQL validation helpers ---
# Match qualified identifiers: schema.table following SQL clauses
_SQL_SCHEMA_TABLE_PATTERN = re.compile(
    r'(?i)(?:from|join|update|into|delete\s+from)\s+'
    r'(?:\n|\r|\t|\s)*'
    r'(?:"(?P<schema_q>[^"]+)"|(?P<schema>[A-Za-z_][\w$]*))\s*\.\s*'
    r'(?:"(?P<table_q>[^"]+)"|(?P<table>[A-Za-z_][\w$]*))'
)
# Match unqualified table names after the same clauses, but NOT if followed by a dot (to avoid capturing schema part of schema.table)
_SQL_UNQUALIFIED_TABLE_PATTERN = re.compile(
    r'(?i)(?:from|join|update|into|delete\s+from)\s+'
    r'(?:"(?P<table_q>[^"]+)"|(?P<table>[A-Za-z_][\w$]*))'
    r'(?!\s*\.)'
)

_RESTRICTED_START_VERBS = re.compile(r'(?is)^\s*(?:;|--.*?$|/\*.*?\*/)*\s*(?!select\b)')


def extract_sql_references(sql: str) -> dict:
    """Extract referenced schemas and tables from SQL using simple regex heuristics.
    Returns a dict with keys: 'schemas' (set), 'tables' (set).
    Conservative: best-effort extraction; may miss edge cases but catches common FROM/JOIN/UPDATE/INSERT/DELETE.
    """
    if not sql:
        return {"schemas": set(), "tables": set()}
    schemas = set()
    tables = set()

    for m in _SQL_SCHEMA_TABLE_PATTERN.finditer(sql):
        schema = m.group('schema_q') or m.group('schema')
        table = m.group('table_q') or m.group('table')
        if schema:
            schemas.add(schema)
        if table:
            tables.add(table)

    for m in _SQL_UNQUALIFIED_TABLE_PATTERN.finditer(sql):
        table = m.group('table_q') or m.group('table')
        if table and table.upper() not in {"SELECT", "VALUES"}:
            tables.add(table)

    return {"schemas": schemas, "tables": tables}


def validate_sql_access(sql: str, default_schema: str | None = None) -> tuple[bool, str | None]:
    """Validate a SQL statement against configured allowed schemas/tables.
    - If no filters configured, allow all.
    - If filters are configured, only allow SELECT statements.
    - If schemas are configured, any referenced qualified schema must be in the allowed list.
    - If tables are configured, any referenced table name must be in the allowed list.
    - If the SQL has no table refs (e.g., SELECT 1), allow it.
    Returns (is_allowed, error_message_or_none).
    """
    if not ALLOWED_SCHEMAS_LIST and not ALLOWED_TABLES_LIST:
        return True, None

    # Only allow SELECT statements when restrictions are active
    if _RESTRICTED_START_VERBS.search(sql or ""):
        return False, "Only SELECT statements are allowed when scope restrictions are active"

    refs = extract_sql_references(sql)
    ref_schemas = refs["schemas"]
    ref_tables = refs["tables"]

    if ALLOWED_SCHEMAS_LIST and ref_schemas:
        disallowed_schemas = [s for s in ref_schemas if s not in ALLOWED_SCHEMAS_LIST]
        if disallowed_schemas:
            return False, (
                "Schema access blocked. Disallowed schemas referenced: "
                + ", ".join(sorted(disallowed_schemas))
                + ". Allowed schemas: " + ", ".join(ALLOWED_SCHEMAS_LIST)
            )

    if ALLOWED_TABLES_LIST and ref_tables:
        disallowed_tables = [t for t in ref_tables if t not in ALLOWED_TABLES_LIST]
        if disallowed_tables:
            return False, (
                "Table access blocked. Disallowed tables referenced: "
                + ", ".join(sorted(disallowed_tables))
                + ". Allowed tables: " + ", ".join(ALLOWED_TABLES_LIST)
            )

    return True, None

LOG_PATH = os.getenv(
    "LOG_PATH",
    os.path.join(os.path.dirname(__file__), "logs", "app.log")
)

# --- Centralized logging configuration ---
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s:%(lineno)d - %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': LOG_PATH,
            'mode': 'a',
        }
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    }
}

# Apply logging configuration
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger()