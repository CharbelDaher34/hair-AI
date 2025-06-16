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


def create_db_and_tables(admin=False):
    # Drop RLS policies first to avoid dependency issues
    print("Dropping RLS policies...")
    drop_rls_policies()
    
    # Now drop and recreate tables
    # print("Dropping tables...")
    # target_metadata.drop_all(get_admin_engine())
    
    all_exist, missing_tables = check_db_tables()
    if not all_exist:
        print("Creating tables...")
        target_metadata.create_all(get_admin_engine())
        print(f"Created {len(missing_tables)} missing tables: {missing_tables}")
    else:
        print("All tables already exist")


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
