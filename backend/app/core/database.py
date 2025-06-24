from contextlib import contextmanager
import time # Keep for now, might be used by other parts of app implicitly or later
import logging # Added
from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy import inspect, text
from models.models import (
    target_metadata,
)  # Import metadata to ensure all models are registered
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__) # Added logger

# --- Database URL for Application User (app_user) ---
APP_DB_USER = os.getenv("POSTGRES_USER", "app_user") # Default to app_user if not set
APP_DB_PASSWORD = os.getenv("POSTGRES_PASSWORD") # Password for app_user
APP_DB_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
APP_DB_PORT = os.getenv("POSTGRES_PORT", "5432")
APP_DB_NAME = os.getenv("POSTGRES_DB", "mydatabase")

if not APP_DB_PASSWORD:
    logger.critical("POSTGRES_PASSWORD environment variable not set for application user.")
    # Consider raising an error or exiting if this is critical for app startup
    # For now, it will likely fail at engine creation if password is None

APPLICATION_DATABASE_URL = f"postgresql://{APP_DB_USER}:{APP_DB_PASSWORD}@{APP_DB_SERVER}:{APP_DB_PORT}/{APP_DB_NAME}"
# DO NOT PRINT APPLICATION_DATABASE_URL - It contains credentials.
# logger.debug(f"Application Database URL configured for user: {APP_DB_USER}") # Safe to log user, not full URL

# --- Database URL for Admin Operations ---
# These should be distinct from the application user, used for setup/migrations.
POSTGRES_ADMIN_USER = os.getenv("POSTGRES_ADMIN_USER", "postgres") # Default to 'postgres' or a specific admin user
POSTGRES_ADMIN_PASSWORD = os.getenv("POSTGRES_ADMIN_PASSWORD")

if not POSTGRES_ADMIN_PASSWORD:
    logger.critical("POSTGRES_ADMIN_PASSWORD environment variable not set.")
    # This is critical for admin operations like table creation / RLS setup

ADMIN_DATABASE_URL = f"postgresql://{POSTGRES_ADMIN_USER}:{POSTGRES_ADMIN_PASSWORD}@{APP_DB_SERVER}:{APP_DB_PORT}/{APP_DB_NAME}"
# DO NOT PRINT ADMIN_DATABASE_URL
# logger.debug(f"Admin Database URL configured for user: {POSTGRES_ADMIN_USER}")


def get_engine(echo=False):
    # This engine is for the application's regular user (app_user)
    return create_engine(APPLICATION_DATABASE_URL, echo=echo)


def get_admin_engine(echo=False):
    # This engine is for admin tasks (migrations, RLS setup, etc.)
    if not POSTGRES_ADMIN_PASSWORD: # Added check before use
        raise ValueError("POSTGRES_ADMIN_PASSWORD is not set, cannot create admin engine.")
    return create_engine(ADMIN_DATABASE_URL, echo=echo)


# Global engine for the application, using app_user credentials
engine = get_engine()


def drop_rls_policies():
    """Drop all RLS policies to avoid dependency issues when dropping tables. Uses admin engine."""
    policies_to_drop = [
        "hr_rls ON hr", "job_rls ON job", "candidate_rls ON candidate",
        "application_rls ON application", "interview_rls ON interview",
        'match_rls ON "match"', "recruitercompanylink_rls ON recruitercompanylink",
        "formkey_rls ON formkey", "jobformkeyconstraint_rls ON jobformkeyconstraint",
        "candidateemployerlink_rls ON candidateemployerlink", "company_rls ON company"
    ]
    
    try:
        admin_engine_instance = get_admin_engine()
        with Session(admin_engine_instance) as session:
            for policy in policies_to_drop:
                try:
                    session.execute(text(f"DROP POLICY IF EXISTS {policy}"))
                    logger.info(f"Dropped policy: {policy}")
                except Exception as e:
                    logger.error(f"Could not drop policy {policy}: {e}", exc_info=True)
            session.commit()
    except ValueError as e: # Catch if admin password wasn't set
        logger.critical(f"Cannot drop RLS policies: {e}")
    except Exception as e:
        logger.critical(f"Unexpected error during RLS policy drop: {e}", exc_info=True)


def create_db_and_tables(drop=False): # Removed unused 'admin' parameter
    """Creates database tables and applies RLS policies. Uses admin engine."""
    try:
        admin_engine_instance = get_admin_engine() # Use admin engine for DDL
        if drop:
            logger.info("Dropping tables and RLS policies as requested...")
            drop_rls_policies() # Uses admin engine internally
            target_metadata.drop_all(admin_engine_instance)
            logger.info("Tables dropped.")
        
        # Check and create tables using the main application engine (app_user)
        # This ensures app_user can see the tables. However, create_all usually needs more privileges.
        # For safety and consistency, DDL operations like create_all should use admin_engine.
        # The check_db_tables also needs to use an engine that can see all tables (admin or initial setup).

        # Let's use admin_engine for checking and creating tables for simplicity and privilege.
        # The app_user will get permissions via GRANT statements in RLS setup.
        inspector = inspect(admin_engine_instance)
        existing_tables_check = set(inspector.get_table_names())
        expected_tables_check = set(target_metadata.tables.keys())
        missing_tables_check = list(expected_tables_check - existing_tables_check)

        if missing_tables_check:
            logger.info(f"Missing tables found: {missing_tables_check}. Creating them...")
            target_metadata.create_all(admin_engine_instance)
            logger.info(f"Created {len(missing_tables_check)} missing tables.")
        else:
            logger.info("All tables already exist according to admin engine inspection.")

        apply_rls_policies_only() # Uses admin engine internally
    except ValueError as e: # Catch if admin password wasn't set for get_admin_engine
        logger.critical(f"Cannot create DB and tables: {e}")
    except Exception as e:
        logger.critical(f"Unexpected error during DB and table creation: {e}", exc_info=True)


def check_db_tables(engine_to_inspect) -> Tuple[bool, List[str]]:
    """
    Checks if all tables defined in SQLModel metadata exist in the database using the provided engine.
    Returns a tuple: (all_exist: bool, missing_tables: list)
    """
    try:
        logger.debug(f"Checking DB tables using engine for DB: {engine_to_inspect.url.database}")
        inspector = inspect(engine_to_inspect)
        existing_tables = set(inspector.get_table_names())
        expected_tables = set(target_metadata.tables.keys())
        missing_tables = list(expected_tables - existing_tables)
        all_exist = len(missing_tables) == 0
        if not all_exist:
            logger.warning(f"check_db_tables found missing tables: {missing_tables} (Engine DB: {engine_to_inspect.url.database})")
        else:
            logger.info(f"check_db_tables confirmed all expected tables exist (Engine DB: {engine_to_inspect.url.database}).")
        return all_exist, missing_tables
    except Exception as e:
        logger.error(f"Error in check_db_tables using engine {engine_to_inspect.url.database}: {e}", exc_info=True)
        return False, list(target_metadata.tables.keys()) # Assume all missing on error


def get_session():
    # Uses the global 'engine' which is configured for app_user
    with Session(engine) as session:
        yield session


@contextmanager
def get_session_rls(company_id: int):
    """
    Yields a SQLModel session with row-level security enabled for the provided company_id.
    It sets a session-local variable 'multi_tenancy.current_company_id' which should be used
    in RLS policies in the database. This is a context manager.
    Uses the global 'engine' (app_user engine).
    """
    # engine = get_engine() # This would create a new engine instance; use the global one.
    with Session(engine) as session:
        try:
            # Use query parameters to prevent SQL injection
            session.execute(
                text("SET LOCAL multi_tenancy.current_company_id = :company_id"),
                {
                    "company_id": str(company_id)
                },  # The value is cast to string here to match the RLS policy's expectation
            )
            yield session
        finally:
            # The 'with' block ensures the session is properly closed, and the
            # transaction-local setting is discarded automatically.
            pass


def test_rls(company_id: int):
    from models.models import HR, Company, Job, Candidate, Application, Match # Local import for test function
    from sqlmodel import select # Local import for test function
    # from sqlalchemy import text # Already imported at module level

    logger.info(f"Testing row level security with company id = {company_id}")
    with get_session_rls(company_id) as session:
        session_var = session.execute(
            text("SELECT current_setting('multi_tenancy.current_company_id', TRUE)")
        ).scalar()
        logger.info(f"RLS test: Session variable 'multi_tenancy.current_company_id' value is: '{session_var}'")

        # Test queries (logging counts and some details)
        for model_class, model_name in [
            (Company, "Company"), (Job, "Job"), (Candidate, "Candidate"),
            (Application, "Application"), (Match, "Match"), (HR, "HR")
        ]:
            stmt = select(model_class)
            items = session.exec(stmt).all()
            logger.info(f"RLS test: Found {len(items)} {model_name}(s) for company_id {company_id}.")
            # Optionally log a few item details for verification if needed, e.g., item.id
            # for item in items[:3]: logger.debug(f"  - {model_name} ID: {item.id}")


def apply_rls_policies_only():
    """Apply RLS policies. Uses admin engine."""
    
    APP_USER_PASSWORD_FOR_RLS = os.getenv("APP_USER_PASSWORD")
    if not APP_USER_PASSWORD_FOR_RLS:
        logger.critical("APP_USER_PASSWORD environment variable not set. Cannot create/update app_user for RLS.")
        return

    try:
        admin_engine_instance = get_admin_engine()
    except ValueError as e: # Catch if admin password wasn't set for get_admin_engine
        logger.critical(f"Cannot apply RLS policies: {e}")
        return

    # The RLS SQL script is designed to be idempotent (using DROP IF EXISTS, etc.).
    # Therefore, the check for pre-existing policies is removed to ensure it always attempts
    # to set the RLS to the defined state. This is safer for ensuring consistency if
    # the RLS state was ever manually or partially altered.
    logger.info("Proceeding to apply RLS policies (existing policies will be dropped and recreated).")

    # Using f-string for password here is a controlled risk as it's for a DDL command executed by admin.
    # Ideally, use query parameters if the DB driver supports it for DDL user creation, but often not the case.
    # Ensure APP_USER_PASSWORD_FOR_RLS is escaped if it can contain special SQL characters, though unlikely for passwords.
    # For PostgreSQL, password should be single-quoted. Python's f-string will handle that if the variable itself doesn't have single quotes.
    # A more robust way for password injection into DDL would be to use a client library function if available,
    # or ensure the password variable is clean or use `SET ROLE` if possible.
    # For now, direct injection with single quotes handled by f-string context.

    # Sanitize password for SQL literal: replace single quotes with two single quotes
    sanitized_app_user_password = APP_USER_PASSWORD_FOR_RLS.replace("'", "''")

    rls_sql = f"""
-- Step 0: Drop all existing RLS policies to ensure clean state
DO $$
DECLARE
    policy_record RECORD;
    table_record RECORD;
BEGIN
    FOR table_record IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
        FOR policy_record IN SELECT policyname FROM pg_policies WHERE schemaname = 'public' AND tablename = table_record.tablename LOOP
            EXECUTE 'DROP POLICY IF EXISTS ' || quote_ident(policy_record.policyname) || ' ON ' || quote_ident(table_record.tablename);
        END LOOP;
    END LOOP;
END;
$$;

-- Step 1: Revoke privileges from app_user if it exists, then drop.
DO $$ BEGIN
   IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
      REVOKE ALL ON ALL TABLES IN SCHEMA public FROM app_user;
      REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM app_user;
      ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM app_user;
      ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM app_user;
      DROP USER app_user;
      RAISE NOTICE 'Dropped existing app_user and its privileges.';
   END IF;
END $$;

-- Step 2: Recreate user with password from env var
CREATE USER app_user WITH LOGIN PASSWORD '{sanitized_app_user_password}';
RAISE NOTICE 'Created user app_user.';

-- Step 3: Grant necessary permissions
GRANT CONNECT ON DATABASE "{APP_DB_NAME}" TO app_user; -- Grant connect to the specific database
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
RAISE NOTICE 'Granted permissions to app_user.';

-- Step 4: Set default privileges for future tables/sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO app_user;
RAISE NOTICE 'Set default privileges for app_user.';
    
CREATE SCHEMA IF NOT EXISTS multi_tenancy;
GRANT USAGE ON SCHEMA multi_tenancy TO app_user; -- Grant usage on the RLS schema
RAISE NOTICE 'Ensured multi_tenancy schema exists and app_user has usage grant.';

-- RLS Policies (Example for HR, others follow same pattern)
ALTER TABLE hr ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr FORCE ROW LEVEL SECURITY;
-- DROP POLICY IF EXISTS hr_rls ON hr; -- Already handled by blanket drop at the start
CREATE POLICY hr_rls ON hr
    FOR ALL TO app_user -- Apply policy specifically to app_user
    USING (employer_id = current_setting('multi_tenancy.current_company_id', true)::int);
RAISE NOTICE 'Applied RLS policy for hr table.';

ALTER TABLE job ENABLE ROW LEVEL SECURITY;
ALTER TABLE job FORCE ROW LEVEL SECURITY;
CREATE POLICY job_rls ON job
    FOR ALL TO app_user
    USING (
        employer_id = current_setting('multi_tenancy.current_company_id', true)::int OR
        (recruited_to_id IS NOT NULL AND recruited_to_id = current_setting('multi_tenancy.current_company_id', true)::int)
    );
RAISE NOTICE 'Applied RLS policy for job table.';

ALTER TABLE candidate ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidate FORCE ROW LEVEL SECURITY;
CREATE POLICY candidate_rls ON candidate
    FOR ALL TO app_user
    USING (
        EXISTS (
            SELECT 1 FROM candidateemployerlink cel
            WHERE cel.candidate_id = candidate.id
              AND cel.employer_id = current_setting('multi_tenancy.current_company_id', true)::int
        )
    );
RAISE NOTICE 'Applied RLS policy for candidate table.';

ALTER TABLE application ENABLE ROW LEVEL SECURITY;
ALTER TABLE application FORCE ROW LEVEL SECURITY;
CREATE POLICY application_rls ON application
    FOR ALL TO app_user
    USING (
        EXISTS (
            SELECT 1 FROM job j
            WHERE j.id = application.job_id AND
            (
                j.employer_id = current_setting('multi_tenancy.current_company_id', true)::int OR
                (j.recruited_to_id IS NOT NULL AND j.recruited_to_id = current_setting('multi_tenancy.current_company_id', true)::int)
            )
        )
    );
RAISE NOTICE 'Applied RLS policy for application table.';

ALTER TABLE interview ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview FORCE ROW LEVEL SECURITY;
CREATE POLICY interview_rls ON interview
    FOR ALL TO app_user
    USING (
        EXISTS (
            SELECT 1 FROM application a
            JOIN job j ON a.job_id = j.id
            WHERE a.id = interview.application_id AND
            (
                j.employer_id = current_setting('multi_tenancy.current_company_id', true)::int OR
                (j.recruited_to_id IS NOT NULL AND j.recruited_to_id = current_setting('multi_tenancy.current_company_id', true)::int)
            )
        )
    );
RAISE NOTICE 'Applied RLS policy for interview table.';

ALTER TABLE "match" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "match" FORCE ROW LEVEL SECURITY;
CREATE POLICY match_rls ON "match"
    FOR ALL TO app_user
    USING (
        EXISTS (
            SELECT 1 FROM application a
            JOIN job j ON a.job_id = j.id
            WHERE a.id = "match".application_id AND
            (
                j.employer_id = current_setting('multi_tenancy.current_company_id', true)::int OR
                (j.recruited_to_id IS NOT NULL AND j.recruited_to_id = current_setting('multi_tenancy.current_company_id', true)::int)
            )
        )
    ); 
RAISE NOTICE 'Applied RLS policy for match table.';

ALTER TABLE recruitercompanylink ENABLE ROW LEVEL SECURITY;
ALTER TABLE recruitercompanylink FORCE ROW LEVEL SECURITY;
CREATE POLICY recruitercompanylink_rls ON recruitercompanylink
    FOR ALL TO app_user
    USING (
        recruiter_id = current_setting('multi_tenancy.current_company_id', true)::int OR
        target_employer_id = current_setting('multi_tenancy.current_company_id', true)::int
    );
RAISE NOTICE 'Applied RLS policy for recruitercompanylink table.';

ALTER TABLE formkey ENABLE ROW LEVEL SECURITY;
ALTER TABLE formkey FORCE ROW LEVEL SECURITY;
CREATE POLICY formkey_rls ON formkey
    FOR ALL TO app_user
    USING (employer_id = current_setting('multi_tenancy.current_company_id', true)::int);
RAISE NOTICE 'Applied RLS policy for formkey table.';

ALTER TABLE jobformkeyconstraint ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobformkeyconstraint FORCE ROW LEVEL SECURITY;
CREATE POLICY jobformkeyconstraint_rls ON jobformkeyconstraint
    FOR ALL TO app_user
    USING (
        EXISTS (
            SELECT 1 FROM job j
            WHERE j.id = jobformkeyconstraint.job_id
              AND (
                  j.employer_id = current_setting('multi_tenancy.current_company_id', true)::int OR
                  (j.recruited_to_id IS NOT NULL AND j.recruited_to_id = current_setting('multi_tenancy.current_company_id', true)::int)
                )
        )
    );
RAISE NOTICE 'Applied RLS policy for jobformkeyconstraint table.';

ALTER TABLE candidateemployerlink ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidateemployerlink FORCE ROW LEVEL SECURITY;
CREATE POLICY candidateemployerlink_rls ON candidateemployerlink
    FOR ALL TO app_user
    USING (employer_id = current_setting('multi_tenancy.current_company_id', true)::int);
RAISE NOTICE 'Applied RLS policy for candidateemployerlink table.';

ALTER TABLE company ENABLE ROW LEVEL SECURITY;
ALTER TABLE company FORCE ROW LEVEL SECURITY;
CREATE POLICY company_rls ON company
    FOR ALL TO app_user
    USING (id = current_setting('multi_tenancy.current_company_id', true)::int);
RAISE NOTICE 'Applied RLS policy for company table.';
"""
    
    logger.info("Attempting to apply RLS policies...")
    try:
        with admin_engine_instance.begin() as connection: # Use existing admin_engine_instance
            # Execute as a single multi-statement block if possible, or split if necessary
            # Some drivers/DBs might have issues with very large multi-statement SQL strings via exec_driver_sql
            # For PostgreSQL, this should generally be fine.
            connection.exec_driver_sql(rls_sql)
        logger.info("RLS policies applied successfully!")
    except Exception as e:
        logger.critical(f"Failed to apply RLS policies: {e}", exc_info=True)