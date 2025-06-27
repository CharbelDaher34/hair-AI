import os
import sys
from dataclasses import dataclass
from datetime import date
from typing import Annotated, Any, Union, List, Dict
import asyncio
import logging
import csv
from io import StringIO

from devtools import debug
from pydantic import BaseModel, Field
from typing_extensions import TypeAlias

from pydantic_ai import Agent, ModelRetry, RunContext, format_as_xml

from core.database import engine, create_db_and_tables
from models.models import *  # Import all models
from sqlmodel import Session, select
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example SQL_EXAMPLES for the agent
SQL_EXAMPLES = [
    {
        "request": "show me all candidates",
        "response": "SELECT * FROM candidate",
    },
    {
        "request": "show me all jobs",
        "response": "SELECT * FROM job",
    },
    {
        "request": "show me records from yesterday",
        "response": "SELECT * FROM application WHERE created_at::date > CURRENT_TIMESTAMP - INTERVAL '1 day'",
    },
    {
        "request": 'show me error records with the tag "foobar"',
        "response": "SELECT * FROM interview WHERE status = 'error' and 'foobar' = ANY(tags)",
    },
]


@dataclass
class Deps:
    session: Session


class Success(BaseModel):
    sql_query: Annotated[str, 1]
    explanation: str = Field(
        "", description="Explanation of the SQL query, as markdown"
    )


class InvalidRequest(BaseModel):
    error_message: str


import os

os.environ["GEMINI_API_KEY"] = "AIzaSyDp8n_AmYsspADJBaNpkJvBdlch1-9vkhw"
Response: TypeAlias = Union[Success, InvalidRequest]
agent = Agent[Deps, Response](
    "gemini-2.0-flash",
    output_type=Response,  # type: ignore
    deps_type=Deps,
)


@agent.system_prompt
def system_prompt() -> str:
    return f"""\
Given the following PostgreSQL table of records, your job is to
write a SQL query that suits the user's request.

The db table:
candidate:
{Candidate.model_json_schema()}

today's date = {date.today()}

{format_as_xml(SQL_EXAMPLES)}
"""


@agent.output_validator
def validate_output(ctx: RunContext[Deps], output: Response) -> Response:
    if isinstance(output, InvalidRequest):
        return output
    # gemini often adds extraneous backslashes to SQL
    output.sql_query = output.sql_query.replace("\\", "")
    if not output.sql_query.upper().startswith("SELECT"):
        raise ModelRetry("Please create a SELECT query")
    # Validate the query using SQLModel session
    try:
        ctx.deps.session.exec(text(output.sql_query))
    except Exception as e:
        raise ModelRetry(f"Invalid query: {e}") from e
    else:
        return output


async def main():
    prompt = "show me all candidates where they were created after 2025-01-01"
    # Ensure tables exist
    # create_db_and_tables()
    with Session(engine) as session:
        deps = Deps(session)
        result = await agent.run(prompt, deps=deps)
        debug(result.output)
        # Example: Query all records (if Record model exists)
        # Replace 'Record' with your actual model name if different
        try:
            query = text(result.output.sql_query)
            records = session.exec(query).all()
            logger.info(f"Records: {records}")
        except Exception as e:
            logger.error(f"Error querying records: {e}", exc_info=True)


def query_records_from_csv(
    file_content: str, query_params: Dict[str, Any]
) -> List[Dict[str, Any]]:
    # ... (rest of the function is unchanged)
    # ...
    pass


def test_query_from_csv():
    # ... (setup code for test_data and other variables)
    # ...

    try:
        records = query_records_from_csv(csv_content, query)
        logger.info(f"Records: {records}")
        # Add assertions here to verify the records
    except Exception as e:
        logger.error(f"Error querying records: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
