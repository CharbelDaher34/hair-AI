from core.database import test_rls, get_admin_engine
from models.models import (
    HR,
    Company,
    Job,
    Candidate,
    Application,
    Match,
    CandidateEmployerLink,
)
from sqlmodel import Session, select
from sqlalchemy import text



def test_data_without_rls():
    """Test what data exists in the database without RLS restrictions"""
    print("=== Testing data WITHOUT RLS (using admin connection) ===")

    with Session(get_admin_engine()) as session:
        # Check companies
        stmt = select(Company)
        companies = session.exec(stmt).all()
        print(f"Found {len(companies)} Company(s) total:")
        for company in companies:
            print(f"  - Company: {company.name}, ID: {company.id}")

        # Check HRs
        stmt = select(HR)
        hrs = session.exec(stmt).all()
        print(f"Found {len(hrs)} HR(s) total:")
        for hr in hrs:
            print(f"  - HR: {hr.full_name}, Company ID: {hr.employer_id}")

        # Check jobs
        stmt = select(Job)
        jobs = session.exec(stmt).all()
        print(f"Found {len(jobs)} Job(s) total:")
        for job in jobs:
            print(f"  - Job: {job.title}, Employer ID: {job.employer_id}")

        # Check candidates
        stmt = select(Candidate)
        candidates = session.exec(stmt).all()
        print(f"Found {len(candidates)} Candidate(s) total:")
        for candidate in candidates:
            print(f"  - Candidate: {candidate.full_name}, ID: {candidate.id}")

        # Check candidate-employer links
        stmt = select(CandidateEmployerLink)
        links = session.exec(stmt).all()
        print(f"Found {len(links)} CandidateEmployerLink(s) total:")
        for link in links:
            print(
                f"  - Link: Candidate ID {link.candidate_id} -> Employer ID {link.employer_id}"
            )

        # Check applications
        stmt = select(Application)
        applications = session.exec(stmt).all()
        print(f"Found {len(applications)} Application(s) total:")
        for application in applications:
            print(
                f"  - Application: {application.id}, Candidate ID: {application.candidate_id}, Job ID: {application.job_id}"
            )


def test_rls_policies():
    """Test RLS policies for company ID 1"""
    print("\n=== Testing data WITH RLS for company ID 1 ===")
    test_rls(1)


if __name__ == "__main__":
    test_data_without_rls()
    test_rls_policies()
