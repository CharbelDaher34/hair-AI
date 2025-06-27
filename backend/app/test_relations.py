import time
import logging
from sqlmodel import Session

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from core.database import get_session, create_db_and_tables

# Models (needed for type hinting and accessing attributes)
from models.models import (
    Company,
    HR,
    Job,
    Application,
    Match,
    FormKey,
    JobFormKeyConstraint,
    RecruiterCompanyLink,
    Candidate,
)

# CRUD functions (for fetching data)
from crud import (
    get_company,
    get_company_by_name,
    get_companies,
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
    get_recruiter_company_links_by_target_company,
)


def display_company_relations(db: Session, employer_id: int):
    company = get_company(db, employer_id=employer_id)
    if not company:
        logger.warning(f"Company with ID {employer_id} not found.")
        return

    logger.info(f"--- Relations for Company: {company.name} (ID: {company.id}) ---")
    logger.info(f"Description: {company.description}")
    logger.info(f"Industry: {company.industry}")
    logger.info(f"Is Owner: {company.is_owner}")

    # HRs
    logger.info("\n  HRs:")
    hrs = get_hrs_by_company(db, employer_id=company.id)
    if hrs:
        for hr_obj in hrs:  # Renamed to avoid conflict with crud.get_hr
            logger.info(
                f"    - HR ID: {hr_obj.id}, Name: {hr_obj.full_name}, Email: {hr_obj.email}, Role: {hr_obj.role}"
            )
    else:
        logger.info("    No HRs found for this company.")

    # FormKeys owned by this Company
    logger.info("\n  FormKeys Owned:")
    form_keys_owned = get_form_keys_by_company(db, employer_id=company.id)
    if form_keys_owned:
        for fk in form_keys_owned:
            logger.info(
                f"    - FormKey ID: {fk.id}, Name: {fk.name}, Type: {fk.field_type}"
            )
    else:
        logger.info("    No FormKeys owned by this company.")

    # Jobs posted by this Company (as employer)
    logger.info("\n  Jobs Posted (as Employer):")
    jobs_posted = get_jobs_by_employer(db, employer_id=company.id)
    if jobs_posted:
        for job in jobs_posted:
            logger.info(
                f"    - Job ID: {job.id}, Title: '{job.title}', Status: {job.status}"
            )
            hr_creator = get_hr(db, hr_id=job.created_by_hr_id)
            if hr_creator:
                logger.info(
                    f"      Created By HR: {hr_creator.full_name} (ID: {hr_creator.id})"
                )

            if job.recruited_to_id:
                recruited_to_company = get_company(db, employer_id=job.recruited_to_id)
                if recruited_to_company:
                    logger.info(
                        f"      Recruited For (Client): {recruited_to_company.name} (ID: {recruited_to_company.id})"
                    )

            # Applications for this Job
            logger.info("      Applications:")
            applications = get_applications_by_job(db, job_id=job.id)
            if applications:
                for app in applications:
                    candidate = get_candidate(db, candidate_id=app.candidate_id)
                    candidate_info = f"Candidate ID: {app.candidate_id}"
                    if candidate:
                        candidate_info += f", Name: {candidate.full_name}, Email: {candidate.email}, Phone: {candidate.phone}, Resume URL: {candidate.resume_url}"
                    logger.info(f"        - App ID: {app.id}, {candidate_info}")
                    logger.info(f"          Form Responses: {app.form_responses}")

                    # Matches for this Application
                    logger.info("          Matches:")
                    matches = get_matches_by_application(db, application_id=app.id)
                    if matches:
                        for match_obj in matches:  # Renamed to avoid conflict
                            logger.info(
                                f"            - Match ID: {match_obj[0].id}, Match Score: {match_obj[0].score}"
                            )
                            logger.info(
                                f"            - Candidate: {match_obj[1].full_name}"
                            )
                    else:
                        logger.info("            No matches for this application.")
            else:
                logger.info("        No applications for this job.")

            # JobFormKeyConstraints for this Job
            logger.info("      Form Key Constraints:")
            constraints = get_job_form_key_constraints_by_job(db, job_id=job.id)
            if constraints:
                for constraint in constraints:
                    fk_detail = get_form_key(db, form_key_id=constraint.form_key_id)
                    fk_info = f"FormKey ID: {constraint.form_key_id}"
                    if fk_detail:
                        fk_info += f" (Name: {fk_detail.name})"
                    logger.info(
                        f"        - Constraint ID: {constraint.id}, Links to {fk_info}, Constraints: {constraint.constraints}"
                    )
            else:
                logger.info("        No form key constraints for this job.")
    else:
        logger.info(
            "    No jobs posted by this company where this company is the direct employer."
        )

    # Jobs where this company is `recruited_to` (i.e., this company is the client for a recruiter)
    # This is accessed via the company.recruited_jobs relationship.
    logger.info("\n  Jobs Recruited For This Company (this company is the client):")
    if company.recruited_jobs:  # SQLAlchemy relationship
        for job in company.recruited_jobs:
            employer_company = get_company(
                db, employer_id=job.employer_id
            )  # This is the recruiter company
            employer_info = (
                f"Recruiter: {employer_company.name} (ID: {employer_company.id})"
                if employer_company
                else "Unknown Recruiter"
            )
            hr_creator = get_hr(db, hr_id=job.created_by_hr_id)
            creator_info = (
                f"Created by HR: {hr_creator.full_name} (ID: {hr_creator.id}) at {employer_company.name}"
                if hr_creator and employer_company
                else ""
            )

            logger.info(
                f"    - Job ID: {job.id}, Title: '{job.title}', Status: {job.status}"
            )
            logger.info(f"      {employer_info}")
            if creator_info:
                logger.info(f"      {creator_info}")
            # Could also list applications, matches for these jobs if needed
    else:
        logger.info(
            "    No jobs where this company is the client (being recruited for)."
        )

    # Recruiter Links (Company is Recruiter)
    logger.info(
        "\n  Recruiter Links (this company is the recruiter, linking to target clients):"
    )
    recruiter_links = get_recruiter_company_links_by_recruiter(
        db, recruiter_id=company.id
    )
    if recruiter_links:
        for link in recruiter_links:
            target_co = get_company(db, employer_id=link.target_employer_id)
            target_info = f"Target/Client Company ID: {link.target_employer_id}"
            if target_co:
                target_info += f" (Name: {target_co.name})"
            logger.info(f"    - Link ID: {link.id}, Links to: {target_info}")
    else:
        logger.info("    No recruiter links where this company is the recruiter.")

    # Recruited-To Links (Company is Target/Client for a recruiter)
    logger.info(
        "\n  Recruited-To Links (this company is the target/client of a recruiter):"
    )
    recruited_to_links = get_recruiter_company_links_by_target_company(
        db, target_employer_id=company.id
    )
    if recruited_to_links:
        for link in recruited_to_links:
            recruiter_co = get_company(db, employer_id=link.recruiter_id)
            recruiter_info = f"Recruiter Company ID: {link.recruiter_id}"
            if recruiter_co:
                recruiter_info += f" (Name: {recruiter_co.name})"
            logger.info(f"    - Link ID: {link.id}, Recruited by: {recruiter_info}")
    else:
        logger.info("    No links where this company is the target/client.")


def main():
    logger.info("=== Testing Company Relations ===")
    # create_db_and_tables() # Ensures tables exist. Usually not needed if DB is already set up.
    db: Session = next(get_session())

    try:
        company_name_to_test = "TestCo"  # From test_crud_functions.py
        company_name_to_test = "ApiTestCo"  # From test_crud_functions.py
        test_company = get_company_by_name(db, name=company_name_to_test)

        if test_company:
            logger.info(
                f"Found company '{test_company.name}' with ID {test_company.id}. Fetching relations..."
            )
            display_company_relations(db, employer_id=test_company.id)
        else:
            logger.warning(f"Company with name '{company_name_to_test}' not found.")
            logger.info("Attempting to fetch the first available company...")
            all_companies = get_companies(db, limit=1)
            if all_companies:
                first_company = all_companies[0]
                logger.info(
                    f"Found first company: {first_company.name} (ID: {first_company.id}). Fetching relations..."
                )
                display_company_relations(db, employer_id=first_company.id)
            else:
                logger.info(
                    "No companies found in the database. Please ensure test data exists (e.g., by running test_crud_functions.py)."
                )

    except Exception as e:
        logger.error(f"An error occurred during relation testing: {e}", exc_info=True)
    finally:
        db.close()
        logger.info("Database session closed.")


if __name__ == "__main__":
    main()
