"""
MCP SQLAlchemy Server - SQLAlchemy + RLS Version

This server provides tools to interact with the matching_db database through SQLAlchemy sessions
with Row Level Security (RLS) enabled for multi-tenant data isolation.

Key Features:
- Uses SQLAlchemy sessions instead of raw pyodbc connections
- Automatic data filtering through PostgreSQL Row Level Security (RLS)
- Multi-tenant support with employer_id-based data isolation
- Clean error handling and logging
- Comprehensive table introspection

USAGE GUIDE FOR MODELS:
1. Start by exploring the database structure using get_tables() to see all tables in matching_db
2. Use describe_table() to understand table structure before querying
3. Use filter_table_names() to find relevant tables by name
4. Execute queries with execute_query() for limited results or query_database() for all results
5. Use fuzzy_search_table() for approximate string matching
6. All queries are automatically filtered by employer_id through RLS policies

EXAMPLE WORKFLOW:
1. get_tables() -> List all tables in matching_db
2. describe_table(table="job") -> Get table structure
3. execute_query("SELECT * FROM job LIMIT 5") -> Query data (automatically filtered by RLS)

ROW LEVEL SECURITY (RLS):
- All database queries are automatically filtered based on the employer_id set in the session
- RLS policies are defined at the database level and enforce data isolation
- No manual filtering is required in queries - the database handles it automatically

NOTE: This server requires an employer_id to be set for proper RLS functionality.
"""

from collections import defaultdict
import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from core.database import get_session_rls
from sqlmodel import Session
import logging
from typing import Any, Dict, List, Optional, Tuple
import json
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from rapidfuzz import fuzz

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="app.log",
    filemode="a",
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


def get_connection():
    """
    Create a database session using SQLAlchemy with RLS (Row Level Security).

    The session automatically filters data based on the employer_id through RLS policies.
    This replaces the manual employer filtering logic.

    Returns:
        SQLAlchemy Session: Database session object with RLS enabled

    Raises:
        ValueError: If required credentials are missing
        Exception: If session creation fails
    """
    logger.info(f"Getting connection with EMPLOYER_ID_FILTER: {os.getcwd()}")

    if EMPLOYER_ID_FILTER is None:
        raise ValueError("EMPLOYER_ID_FILTER must be set before creating a session")

    logger.info(
        f"Creating SQLAlchemy session with RLS for employer_id: {EMPLOYER_ID_FILTER}"
    )

    try:
        # Return the context manager directly - it will be used in a 'with' statement
        return get_session_rls(EMPLOYER_ID_FILTER)
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
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

    NOTE: This function is now deprecated since we're using Row Level Security (RLS).
    RLS automatically filters all queries based on the session's employer_id setting.
    This function now just returns the original query unchanged.

    Args:
        query: The original SQL query

    Returns:
        str: The original query (unchanged, as RLS handles filtering)
    """
    # With RLS enabled, we don't need manual filtering
    # The database automatically applies employer_id filters through RLS policies
    return query


# MCP Server initialization
mcp = FastMCP("mcp-sqlalchemy-server", port=5437, transport="sse")


@mcp.tool(
    name="get_tables",
    description="""Retrieve and return a list containing information about all tables in the matching_db database.
    
    USAGE: Use this as the first step to explore the matching_db database structure.
    This will show you all available tables in the matching_db schema.
    
    EXAMPLE: get_tables() will return all tables in matching_db like ["company", "hr", "job", "candidate", "application", "match", etc.]
    
    NEXT STEPS: Use describe_table(table="table_name") to get detailed table structure.
    """,
)
def get_tables() -> str:
    """
    Retrieve and return a list containing information about all tables in matching_db.

    Returns:
        str: JSON string containing table information
    """
    try:
        with get_connection() as session:
            from sqlalchemy import text

            # Query to get all tables in the public schema
            query = text("""
                SELECT table_catalog, table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)

            result = session.execute(query)
            results = []
            for row in result:
                results.append(
                    {"TABLE_CAT": row[0], "TABLE_SCHEM": row[1], "TABLE_NAME": row[2]}
                )

            return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error retrieving tables: {e}")
        raise


@mcp.tool(
    name="describe_table",
    description="""Retrieve and return a dictionary containing the definition of a table in matching_db, including column names, data types, nullable, primary key, and foreign keys.
    
    USAGE: Use this to understand the structure of a specific table before querying it.
    This is essential for writing correct SQL queries.
    
    PARAMETERS:
    - table: The table name in matching_db (REQUIRED)
    
    EXAMPLE: describe_table(table="job")
    
    RETURNS: Detailed table structure including:
    - Column names, types, sizes, nullable status
    - Primary key columns
    - Foreign key relationships
    - Default values
    
    NEXT STEPS: Use this information to write proper SQL queries with execute_query() or query_database().
    """,
)
def describe_table(table: str) -> str:
    """
    Retrieve and return a dictionary containing the definition of a table in matching_db.

    Args:
        table: The name of the table to retrieve the definition for

    Returns:
        str: JSON string containing the table definition
    """
    try:
        with get_connection() as session:
            from sqlalchemy import text

            # Check if table exists
            table_exists_query = text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            """)

            result = session.execute(table_exists_query, {"table_name": table})
            if result.scalar() == 0:
                return json.dumps(
                    {"error": f"Table {table} not found in matching_db"}, indent=2
                )

            # Get table definition using SQLAlchemy inspection
            table_definition = _get_table_info_sqlalchemy(session, table)
            return json.dumps(table_definition, indent=2)

    except Exception as e:
        logger.error(f"Error retrieving table definition: {e}")
        raise


def fuzzy_match(query: str, table_name: str) -> bool:
    """
    Check if the query matches the table name using fuzzy matching.
    """
    return fuzz.partial_ratio(query, table_name) > 80


@mcp.tool(
    name="filter_table_names",
    description="""Retrieve and return a list containing information about tables in matching_db whose names contain the specified substring.
    
    USAGE: Use this to find tables by name when you know part of the table name.
    This is helpful for discovering relevant tables in the matching_db database.
    
    PARAMETERS:
    - query: The substring to search for in table names (REQUIRED)
    
    EXAMPLES:
    - filter_table_names(query="candidate") - Find all tables with "candidate" in the name
    - filter_table_names(query="job") - Find all tables with "job" in the name
    - filter_table_names(query="application") - Find all tables with "application" in the name
    - filter_table_names(query="company") - Find all tables with "company" in the name
    
    NEXT STEPS: Use describe_table(table="found_table_name") to understand the structure of found tables.
    """,
)
def filter_table_names(query: str) -> str:
    """
    Retrieve and return a list containing information about tables whose names contain the substring.

    Args:
        query: The substring to filter table names by

    Returns:
        str: JSON string containing filtered table information
    """
    try:
        with get_connection() as session:
            from sqlalchemy import text

            # Query to get all tables in the public schema
            table_query = text("""
                SELECT table_catalog, table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)

            result = session.execute(table_query)
            results = []
            for row in result:
                if fuzzy_match(query, row[2]):
                    results.append(
                        {
                            "TABLE_CAT": row[0],
                            "TABLE_SCHEM": row[1],
                            "TABLE_NAME": row[2],
                        }
                    )
            logger.info(f"Results of fuzzy_match: {results}")
            return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error filtering table names: {e}")
        raise


# @mcp.tool(
#     name="execute_query",
#     description="""Execute a SQL query on the matching_db database and return results in JSONL format with row limit.

#     USAGE: Use this for exploratory queries or when you want to limit the number of results.
#     This is the primary tool for running SELECT queries and getting data from matching_db.

#     PARAMETERS:
#     - query: The SQL query to execute (REQUIRED)
#     - max_rows: Maximum number of rows to return (default: 100)
#     - params: Optional dictionary of parameters for parameterized queries
#     - user/password/dsn: Optional connection overrides

#     EXAMPLES:
#     - execute_query("SELECT * FROM candidate LIMIT 5") - Get first 5 candidates
#     - execute_query("SELECT * FROM job WHERE status = 'published' LIMIT 10") - Filter for published jobs
#     - execute_query("SELECT title, location FROM job WHERE experience_level = '5-7_years'") - Find jobs for a specific experience level
#     - execute_query("SELECT c.full_name, j.title FROM application a JOIN candidate c ON a.candidate_id = c.id JOIN job j ON a.job_id = j.id LIMIT 10") - Get candidates and the jobs they applied for

#     BEST PRACTICES:
#     - Always use LIMIT in your queries for large tables
#     - Use parameterized queries to prevent SQL injection
#     - Check table structure with describe_table() first
#     - Use appropriate WHERE clauses to filter data
#     - All queries run against the matching_db database

#     NEXT STEPS: Use query_database() if you need all results without row limit.
#     """
# )
# def execute_query(query: str, max_rows: int = DEFAULT_MAX_ROWS,
#                   params: Optional[Dict[str, Any]] = None) -> str:
#     """
#     Execute a SQL query and return results in JSONL format.

#     Args:
#         query: The SQL query to execute
#         max_rows: Maximum number of rows to return
#         params: Optional dictionary of parameters to pass to the query


#     Returns:
#         str: Results in JSONL format
#     """
#     try:
#         # Apply employer filter to the query
#         filtered_query = apply_employer_filter_to_query(query)
#         logger.info(f"Original query: {query}")
#         if filtered_query != query:
#             logger.info(f"Filtered query: {filtered_query}")

#         with get_connection() as conn:
#             cursor = conn.cursor()
#             rs = cursor.execute(filtered_query, params) if params else cursor.execute(filtered_query)

#             if not rs.description:
#                 return json.dumps({"message": "Query executed successfully", "affected_rows": rs.rowcount})

#             columns = [column[0] for column in rs.description]
#             results = []

#             for row in rs:
#                 row_dict = dict(zip(columns, row))
#                 # Truncate long string values
#                 truncated_row = {
#                     key: (str(value)[:MAX_LONG_DATA] if value is not None else None)
#                     for key, value in row_dict.items()
#                 }
#                 results.append(truncated_row)

#                 if len(results) >= max_rows:
#                     break

#             # Convert the results to JSONL format
#             jsonl_results = "\n".join(json.dumps(row) for row in results)
#             return jsonl_results

#     except pyodbc.Error as e:
#         logger.error(f"Error executing query: {e}")
#         raise


@mcp.tool(
    name="execute_query",
    description="""Execute a SQL query and return results in Markdown table format.
    
    USAGE: Use this when you want results formatted as a nice markdown table for display.
    This is great for reports, documentation, or when you want to show results in a readable format.
    
    PARAMETERS:
    - query: The SQL query to execute (REQUIRED)
    - max_rows: Maximum number of rows to return (default: 100)
    - params: Optional dictionary of parameters for parameterized queries
    
    EXAMPLES:
    - execute_query("SELECT title, location, job_type FROM job WHERE status = 'published' LIMIT 10") - Nicely formatted table of published jobs
    - execute_query("SELECT status, COUNT(*) as count FROM job GROUP BY status") - Summary table of jobs by status
    - execute_query("SELECT c.full_name, j.title FROM application a JOIN candidate c ON a.candidate_id = c.id JOIN job j ON a.job_id = j.id LIMIT 5") - Show which candidates applied to which jobs
    
    RETURNS: Markdown-formatted table that can be directly displayed or included in documents.
    
    NEXT STEPS: Use execute_query() if you need JSONL format for further processing.
    """,
)
def execute_query(
    query: str,
    max_rows: int = DEFAULT_MAX_ROWS,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Execute a SQL query and return results in Markdown table format.

    Args:
        query: The SQL query to execute
        max_rows: Maximum number of rows to return
        params: Optional dictionary of parameters to pass to the query


    Returns:
        str: Results in Markdown table format
    """
    try:
        # With RLS enabled, we don't need manual employer filtering
        logger.info(f"Executing query with RLS: {query}")

        with get_connection() as session:
            from sqlalchemy import text

            if "company_id" in query:
                query = query.replace("company_id", "employer_id")
            # Execute the query using SQLAlchemy
            if params:
                result = session.execute(text(query), params)
            else:
                result = session.execute(text(query))

            # Check if this is a SELECT query (has results)
            if result.returns_rows:
                columns = list(result.keys())
                results = []

                for row in result:
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
                    md_table += (
                        "| " + " | ".join(str(row[col]) for col in columns) + " |\n"
                    )

                return md_table
            else:
                # For non-SELECT queries (INSERT, UPDATE, DELETE)
                return f"**Query executed successfully**\n\nQuery: {query}"

    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise


@mcp.tool(
    name="query_database",
    description="""Execute a SQL query on the matching_db database and return all results in JSONL format (no row limit).
    
    USAGE: Use this when you need all results from a query without any row limit.
    Be careful with large tables - this can return a lot of data!
    
    PARAMETERS:
    - query: The SQL query to execute (REQUIRED)
    
    EXAMPLES:
    - query_database("SELECT * FROM company") - Get all companies
    - query_database("SELECT email FROM hr") - Get all HR emails
    - query_database("SELECT DISTINCT location FROM job") - Get all unique job locations
    - query_database("SELECT * FROM application WHERE job_id = 1") - Get all applications for a specific job
    
    WARNING: Use with caution on large tables. Consider using execute_query() with LIMIT for exploration.
    
    NEXT STEPS: Use execute_query() for limited results or execute_query() for formatted output.
    """,
)
def query_database(query: str) -> str:
    """
    Execute a SQL query and return all results in JSONL format.

    Args:
        query: The SQL query to execute
    Returns:
        str: All results in JSONL format
    """
    try:
        # With RLS enabled, we don't need manual employer filtering
        logger.info(f"Executing query with RLS (no row limit): {query}")

        with get_connection() as session:
            from sqlalchemy import text

            # Execute the query using SQLAlchemy
            result = session.execute(text(query))

            # Check if this is a SELECT query (has results)
            if result.returns_rows:
                columns = list(result.keys())
                results = []

                for row in result:
                    row_dict = dict(zip(columns, row))
                    # Truncate long string values
                    truncated_row = {
                        key: (str(value)[:MAX_LONG_DATA] if value is not None else None)
                        for key, value in row_dict.items()
                    }
                    results.append(truncated_row)

                # Create the Markdown table header
                md_table = "| " + " | ".join(columns) + " |\n"
                md_table += "| " + " | ".join(["---"] * len(columns)) + " |\n"

                # Add rows to the Markdown table
                for row in results:
                    md_table += (
                        "| " + " | ".join(str(row[col]) for col in columns) + " |\n"
                    )

                return md_table
            else:
                # For non-SELECT queries (INSERT, UPDATE, DELETE)
                return json.dumps(
                    {
                        "message": "Query executed successfully",
                        "query": query,
                    }
                )

    except Exception as e:
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
    """,
)
def fuzzy_search_table(
    table: str, column: str, query: str, limit: int = 5, min_similarity: float = 0.3
) -> str:
    """
    Performs a fuzzy search on a table column using trigram similarity.
    """

    # We use f-strings for table and column names, but validate them against the schema first to prevent injection.
    # Note: RLS will automatically filter results based on employer_id
    sql_query = f"""
        SELECT *, similarity("{column}", :query_param) AS similarity
        FROM "{table}"
        WHERE similarity("{column}", :query_param) > :min_similarity
        ORDER BY similarity DESC
        LIMIT :limit_param
    """
    params = {
        "query_param": query,
        "min_similarity": min_similarity,
        "limit_param": limit,
    }

    try:
        with get_connection() as session:
            from sqlalchemy import text

            # Validate table exists
            table_exists_query = text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            """)

            result = session.execute(table_exists_query, {"table_name": table})
            if result.scalar() == 0:
                return json.dumps({"error": f"Table '{table}' not found in database."})

            # Validate column exists
            column_exists_query = text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = :table_name 
                AND column_name = :column_name
            """)

            result = session.execute(
                column_exists_query, {"table_name": table, "column_name": column}
            )
            if result.scalar() == 0:
                return json.dumps(
                    {"error": f"Column '{column}' not found in table '{table}'."}
                )

            # Check if pg_trgm is enabled by trying a simple query
            try:
                session.execute(text("SELECT similarity('test', 'test')"))
            except Exception:
                return json.dumps(
                    {
                        "error": "The 'pg_trgm' extension is not enabled in the database. Fuzzy search is not available."
                    }
                )

            # Execute the fuzzy search query
            # Note: RLS will automatically filter results based on employer_id
            result = session.execute(text(sql_query), params)

            if not result.returns_rows:
                return json.dumps({"message": "No fuzzy matches found.", "results": []})

            columns = list(result.keys())
            results = []

            for row in result:
                row_dict = dict(zip(columns, row))
                # Truncate long string values
                truncated_row = {
                    key: (str(value)[:MAX_LONG_DATA] if value is not None else None)
                    for key, value in row_dict.items()
                }
                results.append(truncated_row)

            jsonl_results = "\n".join(json.dumps(row) for row in results)
            return jsonl_results

    except Exception as e:
        logger.error(f"Error executing fuzzy search query: {e}")
        raise


@mcp.prompt(
    name="mcp_sqlalchemy_server",
    description="""A specialized prompt to guide the AI in querying a job matching database.
    This prompt provides context about the database schema, key relationships, and a step-by-step
    workflow for answering user requests related to jobs, candidates, and applications.
    """,
)
def model_prompt(text: str) -> str:
    """Generate a comprehensive prompt for job matching database query assistance."""
    employer_filter_info = ""
    if EMPLOYER_ID_FILTER is not None:
        employer_filter_info = f"""
**IMPORTANT: ROW LEVEL SECURITY (RLS) ACTIVE**
All database queries are automatically filtered to show only data for employer ID: {EMPLOYER_ID_FILTER}
This filtering is handled by PostgreSQL Row Level Security policies at the database level.
You will only see jobs, candidates, applications, and other data related to this specific employer.
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
def _get_table_info_sqlalchemy(session, table: str) -> Dict[str, Any]:
    """Get comprehensive table information using SQLAlchemy."""
    from sqlalchemy import text

    # Get column information
    columns_query = text("""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = :table_name
        ORDER BY ordinal_position
    """)

    result = session.execute(columns_query, {"table_name": table})
    columns = []
    for row in result:
        columns.append(
            {
                "name": row[0],
                "type": row[1],
                "column_size": row[2],
                "nullable": row[3] == "YES",
                "default": row[4],
                "primary_key": False,  # Will be updated below
            }
        )

    # Get primary key information
    pk_query = text("""
        SELECT column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_schema = 'public'
        AND tc.table_name = :table_name
        AND tc.constraint_type = 'PRIMARY KEY'
    """)

    result = session.execute(pk_query, {"table_name": table})
    primary_keys = [row[0] for row in result]

    # Update primary key flags in columns
    for column in columns:
        if column["name"] in primary_keys:
            column["primary_key"] = True

    # Get foreign key information
    fk_query = text("""
        SELECT 
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            tc.constraint_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_schema = 'public'
        AND tc.table_name = :table_name
    """)

    result = session.execute(fk_query, {"table_name": table})
    foreign_keys = []
    for row in result:
        foreign_keys.append(
            {
                "name": row[3],
                "constrained_columns": [row[0]],
                "referred_table": row[1],
                "referred_columns": [row[2]],
            }
        )

    return {
        "TABLE_CAT": "matching_db",
        "TABLE_SCHEM": "public",
        "TABLE_NAME": table,
        "columns": columns,
        "primary_keys": primary_keys,
        "foreign_keys": foreign_keys,
    }


# Old pyodbc helper functions removed - replaced with SQLAlchemy equivalents


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
            logger.error(
                f"Invalid employer_id argument: {sys.argv[1]}. Must be an integer."
            )
            sys.exit(1)
    else:
        logger.warning(
            "No employer_id provided. Server will return data for all employers."
        )


if __name__ == "__main__":
    initialize_server_with_args()
    logger.info("Starting MCP SQLAlchemy server for matching_db...")
    mcp.run()
