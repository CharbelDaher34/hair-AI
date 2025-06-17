from contextlib import contextmanager
import time
from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy import inspect, text
from models.models import (
    target_metadata,
)  # Import metadata to ensure all models are registered
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_SERVER')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
print(DATABASE_URL)


def get_engine():
    return create_engine(DATABASE_URL, echo=False)


def get_admin_engine():
    DATABASE_URL = f"postgresql://charbel:charbel@{os.getenv('POSTGRES_SERVER')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    return create_engine(DATABASE_URL, echo=False)


engine = get_admin_engine()


def drop_rls_policies():
    """Drop all RLS policies to avoid dependency issues when dropping tables"""
    policies_to_drop = [
        "hr_rls ON hr",
        "job_rls ON job", 
        "candidate_rls ON candidate",
        "application_rls ON application",
        "interview_rls ON interview",
        'match_rls ON "match"',
        "recruitercompanylink_rls ON recruitercompanylink",
        "formkey_rls ON formkey",
        "jobformkeyconstraint_rls ON jobformkeyconstraint",
        "candidateemployerlink_rls ON candidateemployerlink",
        "company_rls ON company"
    ]
    
    admin_engine = get_admin_engine()
    with Session(admin_engine) as session:
        for policy in policies_to_drop:
            try:
                session.execute(text(f"DROP POLICY IF EXISTS {policy}"))
                print(f"Dropped policy: {policy}")
            except Exception as e:
                print(f"Could not drop policy {policy}: {e}")
        session.commit()


def create_db_and_tables(admin=False, drop=False):
    # Drop RLS policies first to avoid dependency issues    
    # Now drop and recreate tables
    if drop:
        print("Dropping tables...")
        drop_rls_policies()
        target_metadata.drop_all(get_admin_engine())
        print("Tables dropped")

    
    all_exist, missing_tables = check_db_tables()
    if not all_exist:
        print("Creating tables...")
        target_metadata.create_all(get_admin_engine())
        print(f"Created {len(missing_tables)} missing tables: {missing_tables}")
    else:
        print("All tables already exist")
        
    apply_rls_policies_only()


def check_db_tables():
    """
    Checks if all tables defined in SQLModel metadata exist in the database.
    Returns a tuple: (all_exist: bool, missing_tables: list)
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    expected_tables = set(target_metadata.tables.keys())
    missing_tables = list(expected_tables - existing_tables)
    all_exist = len(missing_tables) == 0
    return all_exist, missing_tables


def get_session():
    with Session(engine) as session:
        yield session


@contextmanager
def get_session_rls(company_id: int):
    """
    Yields a SQLModel session with row-level security enabled for the provided company_id.
    It sets a session-local variable 'myapp.current_company_id' which should be used
    in RLS policies in the database. This is a context manager.
    """
    engine = get_engine()
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
    from models.models import HR, Company, Job, Candidate, Application, Match
    from sqlmodel import select
    from sqlalchemy import text

    print(f"Testing row level security with company id = {company_id}")
    with get_session_rls(company_id) as session:
        # Check if the session variable is set correctly
        session_var = session.execute(
            text("SELECT current_setting('multi_tenancy.current_company_id', TRUE)")
        ).scalar()
        print(f"Session variable value is: '{session_var}'")

        stmt = select(Company)
        companies = session.exec(stmt).all()
        print(f"Found {len(companies)} Company(s):")
        for company in companies:
            print(f"  - Company: {company.name}, ID: {company.id}")

        stmt = select(Job)
        jobs = session.exec(stmt).all()
        print(f"Found {len(jobs)} Job(s):")
        for job in jobs:
            print(f"  - Job: {job.title}, Company ID: {job.employer_id}")

        stmt = select(Candidate)
        candidates = session.exec(stmt).all()
        print(f"Found {len(candidates)} Candidate(s):")
        for candidate in candidates:
            print(f"  - Candidate: {candidate.full_name}, ID: {candidate.id}")

        stmt = select(Application)
        applications = session.exec(stmt).all()
        print(f"Found {len(applications)} Application(s):")
        for application in applications:
            print(
                f"  - Application: {application.id}, Candidate ID: {application.candidate_id}, Job ID: {application.job_id}"
            )

        stmt = select(Match)
        matches = session.exec(stmt).all()
        print(f"Found {len(matches)} Match(es):")
        # This query should only return the rows that belong to company id 1 if RLS policies are in place.
        stmt = select(HR)
        hrs = session.exec(stmt).all()
        print(f"Found {len(hrs)} HR(s) for company id {company_id}:")
        for hr in hrs:
            print(f"  - HR: {hr.full_name}, Company ID: {hr.employer_id}")



def apply_rls_policies_only():
    """Apply RLS policies without dropping existing ones first"""
    
    # check if the rls exists 
    with get_admin_engine().begin() as connection:
        result = connection.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'hr'
            )
        """))
        rls_exists = result.scalar()
    
    if rls_exists:
        print("RLS policies already exist, skipping...")
        return
    
    # RLS policies SQL (without the DROP statements at the beginning)
    rls_sql = """
-- Step 0: Drop all existing RLS policies to avoid dependency issues
DROP POLICY IF EXISTS hr_rls ON hr;
DROP POLICY IF EXISTS job_rls ON job;
DROP POLICY IF EXISTS candidate_rls ON candidate;
DROP POLICY IF EXISTS application_rls ON application;
DROP POLICY IF EXISTS interview_rls ON interview;
DROP POLICY IF EXISTS match_rls ON "match";
DROP POLICY IF EXISTS recruitercompanylink_rls ON recruitercompanylink;
DROP POLICY IF EXISTS formkey_rls ON formkey;
DROP POLICY IF EXISTS jobformkeyconstraint_rls ON jobformkeyconstraint;
DROP POLICY IF EXISTS candidateemployerlink_rls ON candidateemployerlink;
DROP POLICY IF EXISTS company_rls ON company;

-- Step 1: Revoke all table privileges from app_user (if exists)
DO $$
BEGIN
   EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM app_user';
EXCEPTION WHEN undefined_object THEN
   -- Ignore if role doesn't exist
   RAISE NOTICE 'app_user does not exist, skipping revoke tables';
END $$;

-- Step 2: Revoke all sequence privileges from app_user (if exists)
DO $$
BEGIN
   EXECUTE 'REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM app_user';
EXCEPTION WHEN undefined_object THEN
   RAISE NOTICE 'app_user does not exist, skipping revoke sequences';
END $$;

-- Step 3: Revoke all default privileges involving app_user
DO $$
BEGIN
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM app_user;
EXCEPTION WHEN undefined_object THEN
   RAISE NOTICE 'app_user does not exist, skipping revoke default privileges';
END $$;

DO $$
BEGIN
   EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM app_user';
EXCEPTION WHEN undefined_object THEN
   RAISE NOTICE 'app_user does not exist, skipping revoke default privileges';
END $$;

/* ------------------------------------------------------------------
   CREATE APP USER
-------------------------------------------------------------------*/
-- Step 4: Drop user only if exists
DROP USER IF EXISTS app_user;

-- Step 5: Recreate user
CREATE USER app_user WITH LOGIN PASSWORD 'a';

-- Step 6: Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Step 7: Set default privileges for future tables/sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public 
    GRANT USAGE, SELECT ON SEQUENCES TO app_user;    
    

/* ------------------------------------------------------------------
   CREATE SCHEMA FOR RLS
-------------------------------------------------------------------*/
CREATE SCHEMA IF NOT EXISTS multi_tenancy;

/* ------------------------------------------------------------------
   HR TABLE
-------------------------------------------------------------------*/
ALTER TABLE hr ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hr_rls ON hr;
CREATE POLICY hr_rls ON hr
    FOR ALL TO public
    USING (employer_id = current_setting('multi_tenancy.current_company_id', true)::int);

/* ------------------------------------------------------------------
   JOB TABLE
-------------------------------------------------------------------*/
ALTER TABLE job ENABLE ROW LEVEL SECURITY;
ALTER TABLE job FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS job_rls ON job;
CREATE POLICY job_rls ON job
    FOR ALL TO public
    USING (
        employer_id = current_setting('multi_tenancy.current_company_id', true)::int OR
        recruited_to_id = current_setting('multi_tenancy.current_company_id', true)::int
    );

/* ------------------------------------------------------------------
   CANDIDATE TABLE
-------------------------------------------------------------------*/
ALTER TABLE candidate ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidate FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS candidate_rls ON candidate;
CREATE POLICY candidate_rls ON candidate
    FOR ALL TO public
    USING (
        EXISTS (
            SELECT 1
            FROM candidateemployerlink cel
            WHERE cel.candidate_id = candidate.id
              AND cel.employer_id = current_setting('multi_tenancy.current_company_id', true)::int
        )
    );

/* ------------------------------------------------------------------
   APPLICATION TABLE
-------------------------------------------------------------------*/
ALTER TABLE application ENABLE ROW LEVEL SECURITY;
ALTER TABLE application FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS application_rls ON application;
CREATE POLICY application_rls ON application
    FOR ALL TO public
    USING (
        EXISTS (
            SELECT 1
            FROM candidate c
            JOIN candidateemployerlink cel ON cel.candidate_id = c.id
            WHERE c.id = application.candidate_id
              AND cel.employer_id = current_setting('multi_tenancy.current_company_id', true)::int
        )
    );

/* ------------------------------------------------------------------
   INTERVIEW TABLE
-------------------------------------------------------------------*/
ALTER TABLE interview ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS interview_rls ON interview;
CREATE POLICY interview_rls ON interview
    FOR ALL TO public
    USING (
        EXISTS (
            SELECT 1
            FROM application a
            JOIN candidate c ON c.id = a.candidate_id
            JOIN candidateemployerlink cel ON cel.candidate_id = c.id
            WHERE a.id = interview.application_id
              AND cel.employer_id = current_setting('multi_tenancy.current_company_id', true)::int
        )
    );

/* ------------------------------------------------------------------
   MATCH TABLE (quoted due to keyword usage)
-------------------------------------------------------------------*/
ALTER TABLE "match" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "match" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS match_rls ON "match";
CREATE POLICY match_rls ON "match"
    FOR ALL TO public
    USING (
        EXISTS (
            SELECT 1
            FROM application a
            JOIN candidate c ON c.id = a.candidate_id
            JOIN candidateemployerlink cel ON cel.candidate_id = c.id
            WHERE a.id = "match".application_id
              AND cel.employer_id = current_setting('multi_tenancy.current_company_id', true)::int
        )
    ); 

/* ------------------------------------------------------------------
   RECRUITERCOMPANYLINK TABLE
-------------------------------------------------------------------*/
ALTER TABLE recruitercompanylink ENABLE ROW LEVEL SECURITY;
ALTER TABLE recruitercompanylink FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS recruitercompanylink_rls ON recruitercompanylink;
CREATE POLICY recruitercompanylink_rls ON recruitercompanylink
    FOR ALL TO public
    USING (
        recruiter_id = current_setting('multi_tenancy.current_company_id', true)::int OR
        target_employer_id = current_setting('multi_tenancy.current_company_id', true)::int
    );

/* ------------------------------------------------------------------
   FORMKEY TABLE
-------------------------------------------------------------------*/
ALTER TABLE formkey ENABLE ROW LEVEL SECURITY;
ALTER TABLE formkey FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS formkey_rls ON formkey;
CREATE POLICY formkey_rls ON formkey
    FOR ALL TO public
    USING (employer_id = current_setting('multi_tenancy.current_company_id', true)::int);

/* ------------------------------------------------------------------
   JOBFORMKEYCONSTRAINT TABLE
-------------------------------------------------------------------*/
ALTER TABLE jobformkeyconstraint ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobformkeyconstraint FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS jobformkeyconstraint_rls ON jobformkeyconstraint;
CREATE POLICY jobformkeyconstraint_rls ON jobformkeyconstraint
    FOR ALL TO public
    USING (
        EXISTS (
            SELECT 1
            FROM job j
            WHERE j.id = jobformkeyconstraint.job_id
              AND j.employer_id = current_setting('multi_tenancy.current_company_id', true)::int
        )
    );

/* ------------------------------------------------------------------
   CANDIDATEEMPLOYERLINK TABLE
-------------------------------------------------------------------*/
ALTER TABLE candidateemployerlink ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidateemployerlink FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS candidateemployerlink_rls ON candidateemployerlink;
CREATE POLICY candidateemployerlink_rls ON candidateemployerlink
    FOR ALL TO public
    USING (employer_id = current_setting('multi_tenancy.current_company_id', true)::int);

-- Company table
ALTER TABLE company ENABLE ROW LEVEL SECURITY;
ALTER TABLE company FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS company_rls ON company;
CREATE POLICY company_rls ON company
    FOR ALL TO public
    USING (id = current_setting('multi_tenancy.current_company_id', true)::int);
"""
    
    print("Applying RLS policies...")
    with get_admin_engine().begin() as connection:
        connection.exec_driver_sql(rls_sql)
    print("RLS policies applied successfully!")