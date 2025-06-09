"""
MCP SQLAlchemy Server - Fixed Version

This server provides tools to interact with the matching_db database through pyodbc.
Fixed issues from original version:
- Missing constants (MAX_LONG_DATA, API_KEY)
- Inconsistent naming conventions
- Poor error handling
- Hardcoded values
- Code organization problems
- Missing type hints

USAGE GUIDE FOR MODELS:
1. Start by exploring the database structure using get_tables() to see all tables in matching_db
2. Use describe_table() to understand table structure before querying
3. Use filter_table_names() to find relevant tables by name
4. Execute queries with execute_query() for limited results or query_database() for all results
5. Use execute_query_md() for markdown-formatted results
6. Always handle errors gracefully and provide meaningful feedback

EXAMPLE WORKFLOW:
1. get_tables() -> List all tables in matching_db
2. describe_table(table="users") -> Get table structure
3. execute_query("SELECT * FROM users LIMIT 5") -> Query data

NOTE: This server is configured to work specifically with the matching_db database.
"""

from collections import defaultdict
import os
import logging
from typing import Any, Dict, List, Optional, Tuple
import json
import pyodbc
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Constants
MAX_LONG_DATA = 1000
DEFAULT_MAX_ROWS = 100
DEFAULT_TIMEOUT = 300000
DEFAULT_PORT = 5437
DEFAULT_DATABASE = "matching_db"
DEFAULT_HOST = "localhost"
DEFAULT_SCHEMA = "matching_db"

# Global variable to store the employer_id filter
EMPLOYER_ID_FILTER: Optional[int] = None

# Database configuration
DB_UID = os.getenv("ODBC_USER")
DB_PWD = os.getenv("ODBC_PASSWORD")
DB_DSN = os.getenv("ODBC_DSN")
API_KEY = os.getenv("API_KEY")

# Set custom ODBC configuration file path
odbc_ini_path = os.path.join(os.path.dirname(__file__), "odbc.ini")
os.environ["ODBCINI"] = odbc_ini_path
logger.info(f"ODBCINI set to: {odbc_ini_path}")

logger.info(f"Database configuration - UID: {DB_UID}, DSN: {DB_DSN}")


def get_connection(readonly: bool = True, uid: Optional[str] = None, pwd: Optional[str] = None, 
                   dsn: Optional[str] = None) -> pyodbc.Connection:
    """
    Create a database connection using pyodbc.
    
    Args:
        readonly: Whether the connection should be read-only
        uid: Username (defaults to DB_UID from environment)
        pwd: Password (defaults to DB_PWD from environment)
        dsn: DSN name (defaults to DB_DSN from environment)
    
    Returns:
        pyodbc.Connection: Database connection object
    
    Raises:
        ValueError: If required credentials are missing
        pyodbc.Error: If connection fails
    """
    uid = uid or DB_UID
    pwd = pwd or DB_PWD

    if not uid:
        raise ValueError("ODBC_USER environment variable is not set.")
    if not pwd:
        raise ValueError("ODBC_PASSWORD environment variable is not set.")

    # Use direct connection string instead of DSN to avoid Unix socket issues
    connection_string = (
        f"DRIVER={{PostgreSQL Unicode}};"
        f"SERVER={DEFAULT_HOST};"
        f"PORT={DEFAULT_PORT};"
        f"DATABASE={DEFAULT_DATABASE};"
        f"UID={uid};"
        f"PWD={pwd}"
    )
    
    logger.info(f"Connecting to PostgreSQL with UID: {uid}")
    
    try:
        return pyodbc.connect(connection_string, autocommit=True, readonly=readonly)
    except pyodbc.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        logger.error(f"Connection string used: {connection_string}")
        raise


def set_employer_id_filter(employer_id: int) -> None:
    """Set the global employer_id filter for all database queries."""
    global EMPLOYER_ID_FILTER
    EMPLOYER_ID_FILTER = employer_id
    logger.info(f"Employer ID filter set to: {employer_id}")


def get_employer_filter_clause(table_alias: str = "") -> str:
    """
    Get the WHERE clause to filter by employer_id based on table relationships.
    
    Args:
        table_alias: Optional table alias to use in the query
        
    Returns:
        str: WHERE clause string to filter by employer_id
    """
    if EMPLOYER_ID_FILTER is None:
        return ""
    
    prefix = f"{table_alias}." if table_alias else ""
    return f" AND {prefix}employer_id = {EMPLOYER_ID_FILTER}"


def apply_employer_filter_to_query(query: str) -> str:
    """
    Apply employer_id filtering to a SQL query by analyzing the tables involved.
    This function attempts to automatically add employer_id filters where appropriate.
    
    Args:
        query: The original SQL query
        
    Returns:
        str: Modified query with employer_id filters applied where possible
    """
    if EMPLOYER_ID_FILTER is None:
        return query
    
    # Convert query to lowercase for analysis
    query_lower = query.lower().strip()
    
    # Skip if it's not a SELECT query or already has employer_id filter
    if not query_lower.startswith('select') or 'employer_id' in query_lower:
        return query
    
    # Tables that have direct employer_id relationships
    employer_filtered_tables = {
        'job': 'employer_id',
        'candidate': 'employer_id', 
        'company': 'id',  # company.id = employer_id
        'hr': 'employer_id',
        'formkey': 'employer_id'
    }
    
    # Try to add filters for known tables
    modified_query = query
    
    for table, column in employer_filtered_tables.items():
        if f' {table} ' in query_lower or f' {table}.' in query_lower or query_lower.endswith(f' {table}'):
            # Add WHERE clause if none exists, or AND if WHERE already exists
            if ' where ' not in query_lower:
                if column == 'id' and table == 'company':
                    modified_query += f" WHERE {table}.{column} = {EMPLOYER_ID_FILTER}"
                else:
                    modified_query += f" WHERE {table}.{column} = {EMPLOYER_ID_FILTER}"
            else:
                if column == 'id' and table == 'company':
                    modified_query = modified_query.replace(' WHERE ', f" WHERE {table}.{column} = {EMPLOYER_ID_FILTER} AND ", 1)
                else:
                    modified_query = modified_query.replace(' WHERE ', f" WHERE {table}.{column} = {EMPLOYER_ID_FILTER} AND ", 1)
            break
    
    return modified_query


# MCP Server initialization
mcp = FastMCP('mcp-sqlalchemy-server')


@mcp.tool(
    name="get_tables",
    description="""Retrieve and return a list containing information about all tables in the matching_db database.
    
    USAGE: Use this as the first step to explore the matching_db database structure.
    This will show you all available tables in the matching_db schema.
    
    PARAMETERS:
    - user/password/dsn: Optional connection overrides
    
    EXAMPLE: get_tables() will return all tables in matching_db like ["company", "hr", "job", "candidate", "application", "match", etc.]
    
    NEXT STEPS: Use describe_table(table="table_name") to get detailed table structure.
    """
)
def get_tables(user: Optional[str] = None, password: Optional[str] = None, 
               dsn: Optional[str] = None) -> str:
    """
    Retrieve and return a list containing information about all tables in matching_db.

    Args:
        user: Optional username override
        password: Optional password override
        dsn: Optional DSN name override

    Returns:
        str: JSON string containing table information
    """
    try:
        with get_connection(True, user, password, dsn) as conn:
            cursor = conn.cursor()
            rs = cursor.tables(table=None, catalog=DEFAULT_SCHEMA, schema="%", tableType="TABLE")
            results = []
            for row in rs:
                results.append({
                    "TABLE_CAT": row[0],
                    "TABLE_SCHEM": row[1], 
                    "TABLE_NAME": row[2]
                })
                
            return json.dumps(results, indent=2)
    except pyodbc.Error as e:
        logger.error(f"Error retrieving tables: {e}")
        raise


@mcp.tool(
    name="describe_table",
    description="""Retrieve and return a dictionary containing the definition of a table in matching_db, including column names, data types, nullable, primary key, and foreign keys.
    
    USAGE: Use this to understand the structure of a specific table before querying it.
    This is essential for writing correct SQL queries.
    
    PARAMETERS:
    - table: The table name in matching_db (REQUIRED)
    - user/password/dsn: Optional connection overrides
    
    EXAMPLE: describe_table(table="job")
    
    RETURNS: Detailed table structure including:
    - Column names, types, sizes, nullable status
    - Primary key columns
    - Foreign key relationships
    - Default values
    
    NEXT STEPS: Use this information to write proper SQL queries with execute_query() or query_database().
    """
)
def describe_table(table: str, user: Optional[str] = None, 
                   password: Optional[str] = None, dsn: Optional[str] = None) -> str:
    """
    Retrieve and return a dictionary containing the definition of a table in matching_db.

    Args:
        table: The name of the table to retrieve the definition for
        user: Optional username override
        password: Optional password override
        dsn: Optional DSN name override

    Returns:
        str: JSON string containing the table definition
    """
    try:
        with get_connection(True, user, password, dsn) as conn:
            has_table, table_info = _has_table(conn, catalog=DEFAULT_SCHEMA, table=table)
            if not has_table:
                return json.dumps({"error": f"Table {table} not found in matching_db"}, indent=2)
            
            table_definition = _get_table_info(
                conn, 
                cat=table_info.get("cat"), 
                sch=table_info.get("sch"), 
                table=table_info.get("name")
            )
            return json.dumps(table_definition, indent=2)

    except pyodbc.Error as e:
        logger.error(f"Error retrieving table definition: {e}")
        raise


@mcp.tool(
    name="filter_table_names",
    description="""Retrieve and return a list containing information about tables in matching_db whose names contain the specified substring.
    
    USAGE: Use this to find tables by name when you know part of the table name.
    This is helpful for discovering relevant tables in the matching_db database.
    
    PARAMETERS:
    - query: The substring to search for in table names (REQUIRED)
    - user/password/dsn: Optional connection overrides
    
    EXAMPLES:
    - filter_table_names(query="candidate") - Find all tables with "candidate" in the name
    - filter_table_names(query="job") - Find all tables with "job" in the name
    - filter_table_names(query="application") - Find all tables with "application" in the name
    - filter_table_names(query="company") - Find all tables with "company" in the name
    
    NEXT STEPS: Use describe_table(table="found_table_name") to understand the structure of found tables.
    """
)
def filter_table_names(query: str, user: Optional[str] = None, 
                       password: Optional[str] = None, dsn: Optional[str] = None) -> str:
    """
    Retrieve and return a list containing information about tables whose names contain the substring.

    Args:
        query: The substring to filter table names by
        user: Optional username override
        password: Optional password override
        dsn: Optional DSN name override

    Returns:
        str: JSON string containing filtered table information
    """
    try:
        with get_connection(True, user, password, dsn) as conn:
            cursor = conn.cursor()
            rs = cursor.tables(table=None, catalog=DEFAULT_SCHEMA, schema='%', tableType="TABLE")
            results = []
            for row in rs:
                if query.lower() in row[2].lower():
                    results.append({
                        "TABLE_CAT": row[0],
                        "TABLE_SCHEM": row[1],
                        "TABLE_NAME": row[2]
                    })

            return json.dumps(results, indent=2)
    except pyodbc.Error as e:
        logger.error(f"Error filtering table names: {e}")
        raise


@mcp.tool(
    name="execute_query",
    description="""Execute a SQL query on the matching_db database and return results in JSONL format with row limit.
    
    USAGE: Use this for exploratory queries or when you want to limit the number of results.
    This is the primary tool for running SELECT queries and getting data from matching_db.
    
    PARAMETERS:
    - query: The SQL query to execute (REQUIRED)
    - max_rows: Maximum number of rows to return (default: 100)
    - params: Optional dictionary of parameters for parameterized queries
    - user/password/dsn: Optional connection overrides
    
    EXAMPLES:
    - execute_query("SELECT * FROM candidate LIMIT 5") - Get first 5 candidates
    - execute_query("SELECT * FROM job WHERE status = 'published' LIMIT 10") - Filter for published jobs
    - execute_query("SELECT title, location FROM job WHERE experience_level = '5-7_years'") - Find jobs for a specific experience level
    - execute_query("SELECT c.full_name, j.title FROM application a JOIN candidate c ON a.candidate_id = c.id JOIN job j ON a.job_id = j.id LIMIT 10") - Get candidates and the jobs they applied for
    
    BEST PRACTICES:
    - Always use LIMIT in your queries for large tables
    - Use parameterized queries to prevent SQL injection
    - Check table structure with describe_table() first
    - Use appropriate WHERE clauses to filter data
    - All queries run against the matching_db database
    
    NEXT STEPS: Use query_database() if you need all results without row limit.
    """
)
def execute_query(query: str, max_rows: int = DEFAULT_MAX_ROWS, 
                  params: Optional[Dict[str, Any]] = None, user: Optional[str] = None, 
                  password: Optional[str] = None, dsn: Optional[str] = None) -> str:
    """
    Execute a SQL query and return results in JSONL format.

    Args:
        query: The SQL query to execute
        max_rows: Maximum number of rows to return
        params: Optional dictionary of parameters to pass to the query
        user: Optional username override
        password: Optional password override
        dsn: Optional DSN name override

    Returns:
        str: Results in JSONL format
    """
    try:
        # Apply employer filter to the query
        filtered_query = apply_employer_filter_to_query(query)
        logger.info(f"Original query: {query}")
        if filtered_query != query:
            logger.info(f"Filtered query: {filtered_query}")
        
        with get_connection(True, user, password, dsn) as conn:
            cursor = conn.cursor()
            rs = cursor.execute(filtered_query, params) if params else cursor.execute(filtered_query)
            
            if not rs.description:
                return json.dumps({"message": "Query executed successfully", "affected_rows": rs.rowcount})
            
            columns = [column[0] for column in rs.description]
            results = []
            
            for row in rs:
                row_dict = dict(zip(columns, row))
                # Truncate long string values
                truncated_row = {
                    key: (str(value)[:MAX_LONG_DATA] if value is not None else None) 
                    for key, value in row_dict.items()
                }
                results.append(truncated_row)
                
                if len(results) >= max_rows:
                    break
                
            # Convert the results to JSONL format
            jsonl_results = "\n".join(json.dumps(row) for row in results)
            return jsonl_results
            
    except pyodbc.Error as e:
        logger.error(f"Error executing query: {e}")
        raise


@mcp.tool(
    name="execute_query_md",
    description="""Execute a SQL query on the matching_db database and return results in Markdown table format.
    
    USAGE: Use this when you want results formatted as a nice markdown table for display.
    This is great for reports, documentation, or when you want to show results in a readable format.
    
    PARAMETERS:
    - query: The SQL query to execute (REQUIRED)
    - max_rows: Maximum number of rows to return (default: 100)
    - params: Optional dictionary of parameters for parameterized queries
    - user/password/dsn: Optional connection overrides
    
    EXAMPLES:
    - execute_query_md("SELECT title, location, job_type FROM job WHERE status = 'published' LIMIT 10") - Nicely formatted table of published jobs
    - execute_query_md("SELECT status, COUNT(*) as count FROM job GROUP BY status") - Summary table of jobs by status
    - execute_query_md("SELECT c.full_name, j.title FROM application a JOIN candidate c ON a.candidate_id = c.id JOIN job j ON a.job_id = j.id LIMIT 5") - Show which candidates applied to which jobs
    
    RETURNS: Markdown-formatted table that can be directly displayed or included in documents.
    
    NEXT STEPS: Use execute_query() if you need JSONL format for further processing.
    """
)
def execute_query_md(query: str, max_rows: int = DEFAULT_MAX_ROWS, 
                     params: Optional[Dict[str, Any]] = None, user: Optional[str] = None, 
                     password: Optional[str] = None, dsn: Optional[str] = None) -> str:
    """
    Execute a SQL query and return results in Markdown table format.

    Args:
        query: The SQL query to execute
        max_rows: Maximum number of rows to return
        params: Optional dictionary of parameters to pass to the query
        user: Optional username override
        password: Optional password override
        dsn: Optional DSN name override

    Returns:
        str: Results in Markdown table format
    """
    try:
        # Apply employer filter to the query
        filtered_query = apply_employer_filter_to_query(query)
        logger.info(f"Original query: {query}")
        if filtered_query != query:
            logger.info(f"Filtered query: {filtered_query}")
        
        with get_connection(True, user, password, dsn) as conn:
            cursor = conn.cursor()
            rs = cursor.execute(filtered_query, params) if params else cursor.execute(filtered_query)
            
            if not rs.description:
                return f"**Query executed successfully**\n\nAffected rows: {rs.rowcount}"
            
            columns = [column[0] for column in rs.description]
            results = []
            
            for row in rs:
                row_dict = dict(zip(columns, row))
                # Truncate long string values
                truncated_row = {
                    key: (str(value)[:MAX_LONG_DATA] if value is not None else None) 
                    for key, value in row_dict.items()
                }
                results.append(truncated_row)
                
                if len(results) >= max_rows:
                    break
                
            # Create the Markdown table header
            md_table = "| " + " | ".join(columns) + " |\n"
            md_table += "| " + " | ".join(["---"] * len(columns)) + " |\n"

            # Add rows to the Markdown table
            for row in results:
                md_table += "| " + " | ".join(str(row[col]) for col in columns) + " |\n"

            return md_table

    except pyodbc.Error as e:
        logger.error(f"Error executing query: {e}")
        raise


@mcp.tool(
    name="query_database",
    description="""Execute a SQL query on the matching_db database and return all results in JSONL format (no row limit).
    
    USAGE: Use this when you need all results from a query without any row limit.
    Be careful with large tables - this can return a lot of data!
    
    PARAMETERS:
    - query: The SQL query to execute (REQUIRED)
    - user/password/dsn: Optional connection overrides
    
    EXAMPLES:
    - query_database("SELECT * FROM company") - Get all companies
    - query_database("SELECT email FROM hr") - Get all HR emails
    - query_database("SELECT DISTINCT location FROM job") - Get all unique job locations
    - query_database("SELECT * FROM application WHERE job_id = 1") - Get all applications for a specific job
    
    WARNING: Use with caution on large tables. Consider using execute_query() with LIMIT for exploration.
    
    NEXT STEPS: Use execute_query() for limited results or execute_query_md() for formatted output.
    """
)
def query_database(query: str, user: Optional[str] = None, password: Optional[str] = None, 
                   dsn: Optional[str] = None) -> str:
    """
    Execute a SQL query and return all results in JSONL format.

    Args:
        query: The SQL query to execute
        user: Optional username override
        password: Optional password override
        dsn: Optional DSN name override

    Returns:
        str: All results in JSONL format
    """
    try:
        # Apply employer filter to the query
        filtered_query = apply_employer_filter_to_query(query)
        logger.info(f"Original query: {query}")
        if filtered_query != query:
            logger.info(f"Filtered query: {filtered_query}")
        
        with get_connection(True, user, password, dsn) as conn:
            cursor = conn.cursor()
            rs = cursor.execute(filtered_query)
            
            if not rs.description:
                return json.dumps({"message": "Query executed successfully", "affected_rows": rs.rowcount})
            
            columns = [column[0] for column in rs.description]
            results = []
            
            for row in rs:
                row_dict = dict(zip(columns, row))
                # Truncate long string values
                truncated_row = {
                    key: (str(value)[:MAX_LONG_DATA] if value is not None else None) 
                    for key, value in row_dict.items()
                }
                results.append(truncated_row)
                
            # Convert the results to JSONL format
            jsonl_results = "\n".join(json.dumps(row) for row in results)
            return jsonl_results
            
    except pyodbc.Error as e:
        logger.error(f"Error executing query: {e}")
        raise


@mcp.tool(
    name="fuzzy_search_table",
    description="""Search for a value in a table's column using fuzzy matching. 
    This is useful when the user's input might have typos or is not an exact match.
    NOTE: This feature relies on the pg_trgm extension in PostgreSQL. It must be enabled on your database.
    
    USAGE: Use this to find records when you are not sure about the exact spelling. 
    For example, finding a candidate named 'Jon Doe' when the user asks for 'John Doe'.
    
    PARAMETERS:
    - table: The table name to search in (e.g., 'candidate', 'job'). (REQUIRED)
    - column: The column name to search on (e.g., 'full_name', 'title'). (REQUIRED)
    - query: The value to search for. (REQUIRED)
    - limit: Maximum number of rows to return (default: 5)
    - min_similarity: The minimum similarity threshold (0.0 to 1.0) for a match (default: 0.3)
    
    EXAMPLE: fuzzy_search_table(table="candidate", column="full_name", query="Jonh Doe")
    
    RETURNS: A list of matching rows from the table in JSONL format, ordered by similarity.
    """
)
def fuzzy_search_table(table: str, column: str, query: str, limit: int = 5, min_similarity: float = 0.3, 
                       user: Optional[str] = None, password: Optional[str] = None, dsn: Optional[str] = None) -> str:
    """
    Performs a fuzzy search on a table column using trigram similarity.
    """
    
    # We use f-strings for table and column names, but validate them against the schema first to prevent injection.
    base_sql_query = f"""
        SELECT *, similarity("{column}", ?) AS similarity
        FROM "{table}"
        WHERE similarity("{column}", ?) > ?
    """
    
    # Add employer filter if applicable
    employer_filter_tables = {'job': 'employer_id', 'candidate': 'employer_id', 'hr': 'employer_id', 'formkey': 'employer_id'}
    if EMPLOYER_ID_FILTER is not None and table in employer_filter_tables:
        base_sql_query += f" AND {employer_filter_tables[table]} = {EMPLOYER_ID_FILTER}"
    elif EMPLOYER_ID_FILTER is not None and table == 'company':
        base_sql_query += f" AND id = {EMPLOYER_ID_FILTER}"
    
    sql_query = base_sql_query + """
        ORDER BY similarity DESC
        LIMIT ?
    """
    params = (query, query, min_similarity, limit)
    
    try:
        with get_connection(True, user, password, dsn) as conn:
            cursor = conn.cursor()

            # Validate table and column to prevent SQL injection
            has_table, table_info = _has_table(conn, catalog=DEFAULT_SCHEMA, table=table)
            if not has_table:
                return json.dumps({"error": f"Table '{table}' not found in database."})
            
            table_columns = [c['name'] for c in _get_columns(conn, cat=table_info.get("cat"), sch=table_info.get("sch"), table=table_info.get("name"))]
            if column not in table_columns:
                return json.dumps({"error": f"Column '{column}' not found in table '{table}'."})

            # Check if pg_trgm is enabled by trying a simple query
            try:
                cursor.execute("SELECT similarity('test', 'test')")
                cursor.fetchone()
            except pyodbc.ProgrammingError:
                 return json.dumps({"error": "The 'pg_trgm' extension is not enabled in the database. Fuzzy search is not available."})

            rs = cursor.execute(sql_query, params)
            
            if not rs.description:
                return json.dumps({"message": "No fuzzy matches found.", "results": []})
            
            columns = [col[0] for col in rs.description]
            results = []
            
            for row in rs:
                row_dict = dict(zip(columns, row))
                # Truncate long string values
                truncated_row = {
                    key: (str(value)[:MAX_LONG_DATA] if value is not None else None) 
                    for key, value in row_dict.items()
                }
                results.append(truncated_row)
                
            jsonl_results = "\n".join(json.dumps(row) for row in results)
            return jsonl_results
            
    except pyodbc.Error as e:
        logger.error(f"Error executing fuzzy search query: {e}")
        raise


@mcp.prompt(
    name="mcp_sqlalchemy_server",
    description="""A specialized prompt to guide the AI in querying a job matching database.
    This prompt provides context about the database schema, key relationships, and a step-by-step
    workflow for answering user requests related to jobs, candidates, and applications.
    """
)
def model_prompt(text: str) -> str:
    """Generate a comprehensive prompt for job matching database query assistance."""
    employer_filter_info = ""
    if EMPLOYER_ID_FILTER is not None:
        employer_filter_info = f"""
**IMPORTANT: EMPLOYER FILTERING ACTIVE**
All database queries are automatically filtered to show only data for employer ID: {EMPLOYER_ID_FILTER}
This means you will only see jobs, candidates, applications, and other data related to this specific employer.
"""
    
    return f"""You are an expert database assistant for a job matching platform. Your goal is to use the provided tools to answer questions about jobs, candidates, companies, and applications from the 'matching_db' database.

{employer_filter_info}

**DATABASE SCHEMA OVERVIEW:**

The database contains information about the recruitment process. Here are the key tables and their relationships:

- `company`: Stores information about companies (employers and recruiters).
- `hr`: Human resources personnel associated with a `company`.
- `job`: Job postings created by an `hr` for a `company`. It includes details like title, description, location, experience level, etc.
- `candidate`: Job seekers with their personal information and resume data.
- `application`: Links a `candidate` to a `job`, representing a job application.
- `match`: Contains match scores and skill analysis between a candidate's resume and a job description for a given `application`.
- `interview`: Stores details about interviews scheduled for an `application`.

**Key Relationships:**
- A `company` has many `job`s and `hr`s.
- An `hr` belongs to one `company` and can create many `job`s.
- A `candidate` can submit many `application`s.
- An `application` connects one `candidate` to one `job`.
- A `match` and `interview` belong to one `application`.

**COMMON USER REQUESTS & HOW TO HANDLE THEM:**

*   **"Find jobs for..."**:
    *   **Request**: "Find all published software engineer jobs in London."
    *   **Action**: `execute_query("SELECT title, location, job_type FROM job WHERE status = 'published' AND title ILIKE '%software engineer%' AND location = 'London'")`

*   **"Show me candidates for a job..."**:
    *   **Request**: "Who applied for the 'Data Scientist' job (ID 123)?"
    *   **Workflow**:
        1.  Find all `application` records where `job_id = 123`.
        2.  Extract the `candidate_id` from those applications.
        3.  Query the `candidate` table to get details for those `candidate_id`s.
    *   **Action**: `execute_query("SELECT c.* FROM candidate c JOIN application a ON c.id = a.candidate_id WHERE a.job_id = 123")`

*   **"What is the status of a candidate's application?"**:
    *   **Request**: "What is the status of John Doe's application for the 'Project Manager' role?"
    *   **Workflow**:
        1.  Find the `id` for 'John Doe' in the `candidate` table. If the name is misspelled, use `fuzzy_search_table`.
        2.  Find the `id` for the 'Project Manager' role in the `job` table.
        3.  Query the `application` table using `candidate_id` and `job_id`.
        4.  Check related `match` or `interview` tables for status details.
    *   **Action**: Start by getting IDs, then construct the final query.

*   **"Finding items with approximate names..."**:
    *   **Request**: "I'm looking for a candidate, I think their name is 'Jon Do'."
    *   **Action**: `fuzzy_search_table(table="candidate", column="full_name", query="Jon Do")`
    *   **Note**: Use `fuzzy_search_table` when the user is unsure about the exact spelling of something. It works best on text-based columns like names and titles.

**YOUR STEP-BY-STEP PROCESS:**

1.  **Understand the Goal**: Carefully analyze the user's request: {text}
2.  **Explore (If Needed)**: If you're unsure about table names or columns, use `get_tables()` and `describe_table('table_name')`. For example, to see what job statuses are available, you might query `SELECT DISTINCT status FROM job`.
3.  **Formulate the Query**: Write the SQL query to get the information. Use JOINs to connect tables. Use WHERE clauses to filter. If the user's query is fuzzy (e.g., contains a typo), use the `fuzzy_search_table` tool.
4.  **Execute and Present**: Use `execute_query()` or `execute_query_md()` to run the query. Present the results clearly to the user. Explain what you did.

You have the tools. Begin by analyzing the user's request and planning your first step.
"""


# Helper functions
def _has_table(conn: pyodbc.Connection, catalog: str, table: str) -> Tuple[bool, Dict[str, str]]:
    """Check if a table exists and return its metadata."""
    with conn.cursor() as cursor:
        row = cursor.tables(table=table, catalog=catalog, schema=None, tableType=None).fetchone()
        if row:
            return True, {"cat": row[0], "sch": row[1], "name": row[2]}
        else:
            return False, {}


def _get_columns(conn: pyodbc.Connection, cat: str, sch: str, table: str) -> List[Dict[str, Any]]:
    """Get column information for a table."""
    with conn.cursor() as cursor:
        columns = []
        for row in cursor.columns(table=table, catalog=cat, schema=sch):
            columns.append({
                "name": row[3],
                "type": row[5],
                "column_size": row[6],
                "num_prec_radix": row[9],
                "nullable": row[10] != 0,
                "default": row[12]
            })
        return columns


def _get_pk_constraint(conn: pyodbc.Connection, cat: str, sch: str, table: str) -> Optional[Dict[str, Any]]:
    """Get primary key constraint information for a table."""
    with conn.cursor() as cursor:
        rs = cursor.primaryKeys(table=table, catalog=cat, schema=sch).fetchall()
        if rs:
            return {
                "constrained_columns": [row[3] for row in rs],
                "name": rs[0][5]
            }
        return None


def _get_foreign_keys(conn: pyodbc.Connection, cat: str, sch: str, table: str) -> List[Dict[str, Any]]:
    """Get foreign key constraint information for a table."""
    def create_fkey_record() -> Dict[str, Any]:
        return {
            "name": None,
            "constrained_columns": [],
            "referred_cat": None,
            "referred_schem": None,
            "referred_table": None,
            "referred_columns": [],
            "options": {},
        }

    fkeys = defaultdict(create_fkey_record)
    
    with conn.cursor() as cursor:
        rs = cursor.foreignKeys(foreignTable=table, foreignCatalog=cat, foreignSchema=sch)
        for row in rs:
            rec = fkeys[row[11]]  # FK_NAME
            rec["name"] = row[11]
            rec["constrained_columns"].append(row[7])  # FKCOLUMN_NAME
            rec["referred_columns"].append(row[3])     # PKCOLUMN_NAME

            if not rec["referred_table"]:
                rec["referred_table"] = row[2]   # PKTABLE_NAME
                rec["referred_schem"] = row[1]   # PKTABLE_OWNER
                rec["referred_cat"] = row[0]     # PKTABLE_CAT

    return list(fkeys.values())


def _get_table_info(conn: pyodbc.Connection, cat: str, sch: str, table: str) -> Dict[str, Any]:
    """Get comprehensive table information including columns, primary keys, and foreign keys."""
    try:
        columns = _get_columns(conn, cat=cat, sch=sch, table=table)
        pk_constraint = _get_pk_constraint(conn, cat=cat, sch=sch, table=table)
        primary_keys = pk_constraint['constrained_columns'] if pk_constraint else []
        foreign_keys = _get_foreign_keys(conn, cat=cat, sch=sch, table=table)

        table_info = {
            "TABLE_CAT": cat,
            "TABLE_SCHEM": sch,
            "TABLE_NAME": table,
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys
        }

        # Mark primary key columns
        for column in columns:
            column["primary_key"] = column['name'] in primary_keys

        return table_info

    except pyodbc.Error as e:
        logger.error(f"Error retrieving table info: {e}")
        raise


def initialize_server_with_args():
    """Initialize the server with command line arguments."""
    import sys
    
    # Parse command line arguments for employer_id
    if len(sys.argv) > 1:
        try:
            employer_id = int(sys.argv[1])
            set_employer_id_filter(employer_id)
            logger.info(f"Server initialized with employer_id filter: {employer_id}")
        except ValueError:
            logger.error(f"Invalid employer_id argument: {sys.argv[1]}. Must be an integer.")
            sys.exit(1)
    else:
        logger.warning("No employer_id provided. Server will return data for all employers.")


if __name__ == "__main__":
    initialize_server_with_args()
    logger.info("Starting MCP SQLAlchemy server for matching_db...")
    mcp.run() 