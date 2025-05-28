from sqlmodel import Session

from core.database import get_session, create_db_and_tables

# Models (needed for type hinting and accessing attributes)
from models.models import (
    Company, HR, Job, Application, Match, FormKey, JobFormKeyConstraint, RecruiterCompanyLink, Candidate
)

# CRUD functions (for fetching data)
from crud import (
    get_company, get_company_by_name, get_companies,
    get_hrs_by_company,
    get_jobs_by_employer,
    get_hr, 
    get_applications_by_job,
    get_candidate,
    get_matches_by_application,
    get_form_keys_by_company,
    get_job_form_key_constraints_by_job,
    get_form_key,
    get_recruiter_company_links_by_recruiter,
    get_recruiter_company_links_by_target_company
)

def display_company_relations(db: Session, employer_id: int):
    company = get_company(db, employer_id=employer_id)
    if not company:
        print(f"Company with ID {employer_id} not found.")
        return

    print(f"--- Relations for Company: {company.name} (ID: {company.id}) ---")
    print(f"Description: {company.description}")
    print(f"Industry: {company.industry}")
    print(f"Is Owner: {company.is_owner}")

    # HRs
    print("\n  HRs:")
    hrs = get_hrs_by_company(db, employer_id=company.id)
    if hrs:
        for hr_obj in hrs: # Renamed to avoid conflict with crud.get_hr
            print(f"    - HR ID: {hr_obj.id}, Name: {hr_obj.full_name}, Email: {hr_obj.email}, Role: {hr_obj.role}")
    else:
        print("    No HRs found for this company.")

    # FormKeys owned by this Company
    print("\n  FormKeys Owned:")
    form_keys_owned = get_form_keys_by_company(db, employer_id=company.id)
    if form_keys_owned:
        for fk in form_keys_owned:
            print(f"    - FormKey ID: {fk.id}, Name: {fk.name}, Type: {fk.field_type}")
    else:
        print("    No FormKeys owned by this company.")

    # Jobs posted by this Company (as employer)
    print("\n  Jobs Posted (as Employer):")
    jobs_posted = get_jobs_by_employer(db, employer_id=company.id)
    if jobs_posted:
        for job in jobs_posted:
            print(f"    - Job ID: {job.id}, Title: '{job.job_data.get('title', 'N/A')}', Status: {job.status}")
            hr_creator = get_hr(db, hr_id=job.created_by)
            if hr_creator:
                print(f"      Created By HR: {hr_creator.full_name} (ID: {hr_creator.id})")
            
            if job.recruited_to_id:
                recruited_to_company = get_company(db, employer_id=job.recruited_to_id)
                if recruited_to_company:
                    print(f"      Recruited For (Client): {recruited_to_company.name} (ID: {recruited_to_company.id})")


            # Applications for this Job
            print("      Applications:")
            applications = get_applications_by_job(db, job_id=job.id)
            if applications:
                for app in applications:
                    candidate = get_candidate(db, candidate_id=app.candidate_id)
                    candidate_info = f"Candidate ID: {app.candidate_id}"
                    if candidate:
                        candidate_info += f", Name: {candidate.full_name}, Email: {candidate.email}, Phone: {candidate.phone}, Resume URL: {candidate.resume_url}"
                    print(f"        - App ID: {app.id}, {candidate_info}")
                    print(f"          Form Responses: {app.form_responses}")

                    # Matches for this Application
                    print("          Matches:")
                    matches = get_matches_by_application(db, application_id=app.id)
                    if matches:
                        for match_obj in matches: # Renamed to avoid conflict
                            print(f"            - Match ID: {match_obj.id}, Match Result: {match_obj.match_result}")
                    else:
                        print("            No matches for this application.")
            else:
                print("        No applications for this job.")

            # JobFormKeyConstraints for this Job
            print("      Form Key Constraints:")
            constraints = get_job_form_key_constraints_by_job(db, job_id=job.id)
            if constraints:
                for constraint in constraints:
                    fk_detail = get_form_key(db, form_key_id=constraint.form_key_id)
                    fk_info = f"FormKey ID: {constraint.form_key_id}"
                    if fk_detail:
                        fk_info += f" (Name: {fk_detail.name})"
                    print(f"        - Constraint ID: {constraint.id}, Links to {fk_info}, Constraints: {constraint.constraints}")
            else:
                print("        No form key constraints for this job.")
    else:
        print("    No jobs posted by this company where this company is the direct employer.")

    # Jobs where this company is `recruited_to` (i.e., this company is the client for a recruiter)
    # This is accessed via the company.recruited_jobs relationship.
    print("\n  Jobs Recruited For This Company (this company is the client):")
    if company.recruited_jobs: # SQLAlchemy relationship
        for job in company.recruited_jobs:
            employer_company = get_company(db, employer_id=job.employer_id) # This is the recruiter company
            employer_info = f"Recruiter: {employer_company.name} (ID: {employer_company.id})" if employer_company else "Unknown Recruiter"
            hr_creator = get_hr(db, hr_id=job.created_by)
            creator_info = f"Created by HR: {hr_creator.full_name} (ID: {hr_creator.id}) at {employer_company.name}" if hr_creator and employer_company else ""

            print(f"    - Job ID: {job.id}, Title: '{job.job_data.get('title', 'N/A')}', Status: {job.status}")
            print(f"      {employer_info}")
            if creator_info:
                print(f"      {creator_info}")
            # Could also list applications, matches for these jobs if needed
    else:
        print("    No jobs where this company is the client (being recruited for).")


    # Recruiter Links (Company is Recruiter)
    print("\n  Recruiter Links (this company is the recruiter, linking to target clients):")
    recruiter_links = get_recruiter_company_links_by_recruiter(db, recruiter_id=company.id)
    if recruiter_links:
        for link in recruiter_links:
            target_co = get_company(db, employer_id=link.target_employer_id)
            target_info = f"Target/Client Company ID: {link.target_employer_id}"
            if target_co:
                target_info += f" (Name: {target_co.name})"
            print(f"    - Link ID: {link.id}, Links to: {target_info}")
    else:
        print("    No recruiter links where this company is the recruiter.")

    # Recruited-To Links (Company is Target/Client for a recruiter)
    print("\n  Recruited-To Links (this company is the target/client of a recruiter):")
    recruited_to_links = get_recruiter_company_links_by_target_company(db, target_employer_id=company.id)
    if recruited_to_links:
        for link in recruited_to_links:
            recruiter_co = get_company(db, employer_id=link.recruiter_id)
            recruiter_info = f"Recruiter Company ID: {link.recruiter_id}"
            if recruiter_co:
                recruiter_info += f" (Name: {recruiter_co.name})"
            print(f"    - Link ID: {link.id}, Recruited by: {recruiter_info}")
    else:
        print("    No links where this company is the target/client.")


def main():
    print("=== Testing Company Relations ===")
    # create_db_and_tables() # Ensures tables exist. Usually not needed if DB is already set up.
    db: Session = next(get_session())

    try:
        company_name_to_test = "TestCo" # From test_crud_functions.py
        company_name_to_test = "ApiTestCo" # From test_crud_functions.py
        test_company = get_company_by_name(db, name=company_name_to_test)

        if test_company:
            print(f"Found company '{test_company.name}' with ID {test_company.id}. Fetching relations...")
            display_company_relations(db, employer_id=test_company.id)
        else:
            print(f"Company with name '{company_name_to_test}' not found.")
            print("Attempting to fetch the first available company...")
            all_companies = get_companies(db, limit=1) 
            if all_companies:
                first_company = all_companies[0]
                print(f"Found first company: {first_company.name} (ID: {first_company.id}). Fetching relations...")
                display_company_relations(db, employer_id=first_company.id)
            else:
                print("No companies found in the database. Please ensure test data exists (e.g., by running test_crud_functions.py).")

    except Exception as e:
        print(f"\nXXX AN ERROR OCCURRED XXX: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\nDatabase session closed.")

if __name__ == "__main__":
    main()
