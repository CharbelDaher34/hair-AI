import logging
from sqlalchemy import text
from core.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_rls_policies():
    db = next(get_db())
    try:
        # Get all RLS policies
        policies_query = text("SELECT * FROM pg_policies")
        policies = db.execute(policies_query).fetchall()

        if policies:
            logger.info("Current RLS Policies:")
            for policy in policies:
                logger.info(
                    f"  Table: {policy[1]}, Policy: {policy[2]}, Command: {policy[5]}, Condition: {policy[6]}"
                )
        else:
            logger.info("No RLS policies found!")

        # Get all tables and their RLS status
        tables_query = text("""
            SELECT 
                c.relname,
                c.relrowsecurity,
                c.relforcerowsecurity
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind = 'r' AND n.nspname = 'public'
        """)
        tables = db.execute(tables_query).fetchall()

        if tables:
            logger.info("\nTables with RLS enabled:")
            for table in tables:
                logger.info(
                    f"  {table[1]}: rowsecurity={table[2]}, forcerowsecurity={table[3]}"
                )
        else:
            logger.info("No tables have RLS enabled!")

        # Test setting and getting a session variable
        logger.info("\nTesting session variable:")
        db.execute(text("SET app.current_user_id = 123"))
        result = db.execute(text("SELECT current_setting('app.current_user_id')"))
        logger.info(f"Session variable value: {result.scalar()}")
    finally:
        db.close()


if __name__ == "__main__":
    check_rls_policies()
