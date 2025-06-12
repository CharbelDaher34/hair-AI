from sqlmodel import create_engine, Session, SQLModel
from datetime import datetime
import os

# Models
from models.models import (
    Company,
    HR,
    RecruiterCompanyLink,
    FormKey,
    JobFormKeyConstraint,
    Job,
    Candidate,
    Application,
    Match,
)

# Schemas
from schemas import (
    CompanyCreate,
    CompanyUpdate,
    HRCreate,
    HRUpdate,
    RecruiterCompanyLinkCreate,
    RecruiterCompanyLinkUpdate,
    FormKeyCreate,
    FormKeyUpdate,
    JobFormKeyConstraintCreate,
    JobFormKeyConstraintUpdate,
    JobCreate,
    JobUpdate,
    CandidateCreate,
    CandidateUpdate,
    ApplicationCreate,
    ApplicationUpdate,
    MatchCreate,
    MatchUpdate,
)

# CRUD functions
from crud import (
    create_company,
    get_company,
    get_company_by_name,
    get_companies,
    update_company,
    delete_company,
    create_hr,
    get_hr,
    get_hr_by_email,
    get_hrs,
    get_hrs_by_company,
    update_hr,
    delete_hr,
    create_recruiter_company_link,
    get_recruiter_company_link,
    get_recruiter_company_links_by_recruiter,
    get_recruiter_company_links_by_target_company,
    update_recruiter_company_link,
    delete_recruiter_company_link,
    create_form_key,
    get_form_key,
    get_form_keys_by_company,
    update_form_key,
    delete_form_key,
    create_job_form_key_constraint,
    get_job_form_key_constraint,
    get_job_form_key_constraints_by_job,
    update_job_form_key_constraint,
    delete_job_form_key_constraint,
    create_job,
    get_job,
    get_jobs,
    get_jobs_by_employer,
    get_jobs_by_status,
    update_job,
    delete_job,
    create_candidate,
    get_candidate,
    get_candidate_by_email,
    get_candidates,
    update_candidate,
    delete_candidate,
    create_application,
    get_application,
    get_applications_by_job,
    get_applications_by_candidate,
    update_application,
    delete_application,
    create_match,
    get_match,
    get_matches_by_application,
    update_match,
    delete_match,
)

from core.database import get_session, create_db_and_tables

# Add import for AgentClient
from services.resume_upload import AgentClient

from pydantic import BaseModel
from typing import Optional


# Define the Resume_Data class inheriting from BaseModel
class Resume_Data(BaseModel):
    """
    A Pydantic model to represent basic resume data,
    starting with just the name.
    """

    name: str
    # You can add more fields as needed, for example:
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None


def run_sequential_crud_tests():
    print("=== Starting Sequential CRUD Tests ===")
    create_db_and_tables()
    db: Session = next(get_session())

    try:
        # Test data
        company_data = {
            "name": "TestCo",
            "description": "A test company",
            "industry": "Tech",
            "is_owner": True,
        }
        hr_data = {
            "email": "hr@testco.com",
            "password": "hashed_password",
            "full_name": "Test HR",
            "role": "hr_manager",
        }
        form_key_data = {
            "name": "ExperienceYears",
            "field_type": "number",
            "required": True,
        }
        job_data = {
            "job_data": {
                "title": "Software Engineer",
                "description": "Develop software",
            },
            "status": "open",
            "form_key_ids": [],
        }
        candidate_data = {
            "full_name": "Test Candidate",
            "email": "candidate@example.com",
            "phone": "1234567890",
        }
        application_data = {"form_responses": {"experience": "3 years"}}
        match_data = {}
        company_data_target = {
            "name": "TargetLinkCo",
            "description": "A target company for linking",
            "is_owner": False,
        }

        # --- 1. Company ---
        print("\\n--- Testing Company ---")
        company_in = CompanyCreate(**company_data)
        created_company = create_company(db=db, company_in=company_in)
        assert (
            created_company
            and created_company.name == company_data["name"]
            and created_company.is_owner == company_data["is_owner"]
        )
        print(f"CREATE Company: {created_company.name} (ID: {created_company.id})")
        employer_id = created_company.id

        retrieved_company = get_company(db=db, employer_id=employer_id)
        assert retrieved_company and retrieved_company.id == employer_id
        print(f"READ Company: {retrieved_company.name}")

        company_update_data = CompanyUpdate(description="Updated company description.")
        updated_company = update_company(
            db=db, db_company=retrieved_company, company_in=company_update_data
        )
        assert (
            updated_company
            and updated_company.description == "Updated company description."
        )
        print(
            f"UPDATE Company: {updated_company.name}, New Description: {updated_company.description}"
        )
        # delete_company is tested at the end after all dependent entities are cleaned up.

        # --- 2. HR ---
        print("\\n--- Testing HR ---")
        hr_in_data = {**hr_data, "employer_id": employer_id}
        hr_in = HRCreate(**hr_in_data)
        created_hr = create_hr(db=db, hr_in=hr_in)
        assert created_hr and created_hr.email == hr_data["email"]
        print(
            f"CREATE HR: {created_hr.full_name} (ID: {created_hr.id}) for Company ID: {employer_id}"
        )
        hr_id = created_hr.id

        retrieved_hr = get_hr(db=db, hr_id=hr_id)
        assert retrieved_hr and retrieved_hr.id == hr_id
        print(f"READ HR: {retrieved_hr.full_name}")

        hr_update_data = HRUpdate(full_name="Updated Test HR Name")
        updated_hr = update_hr(db=db, db_hr=retrieved_hr, hr_in=hr_update_data)
        assert updated_hr and updated_hr.full_name == "Updated Test HR Name"
        print(f"UPDATE HR: {updated_hr.full_name}")
        # delete_hr is tested at the end.

        # --- 3. FormKey ---
        print("\\n--- Testing FormKey ---")
        form_key_in_data = {**form_key_data, "employer_id": employer_id}
        form_key_in = FormKeyCreate(**form_key_in_data)
        created_form_key = create_form_key(db=db, form_key_in=form_key_in)
        assert created_form_key and created_form_key.name == form_key_data["name"]
        print(
            f"CREATE FormKey: {created_form_key.name} (ID: {created_form_key.id}) for Company ID: {employer_id}"
        )
        form_key_id = created_form_key.id

        retrieved_form_key = get_form_key(db=db, form_key_id=form_key_id)
        assert retrieved_form_key and retrieved_form_key.id == form_key_id
        print(f"READ FormKey: {retrieved_form_key.name}")

        form_key_update_data = FormKeyUpdate(field_type="text")
        updated_form_key = update_form_key(
            db=db, db_form_key=retrieved_form_key, form_key_in=form_key_update_data
        )
        assert updated_form_key and updated_form_key.field_type == "text"
        print(
            f"UPDATE FormKey: {updated_form_key.name}, New Field Type: {updated_form_key.field_type}"
        )
        # delete_form_key is tested at the end.

        # --- 4. Job ---
        print("\\n--- Testing Job ---")
        job_in_data = {**job_data, "employer_id": employer_id, "created_by": hr_id}
        job_in = JobCreate(**job_in_data)
        created_job = create_job(db=db, job_in=job_in)
        assert (
            created_job
            and created_job.job_data["title"] == job_data["job_data"]["title"]
        )
        print(
            f"CREATE Job: '{created_job.job_data['title']}' (ID: {created_job.id}) for Company ID: {employer_id}, HR ID: {hr_id}"
        )
        job_id = created_job.id

        retrieved_job = get_job(db=db, job_id=job_id)
        assert retrieved_job and retrieved_job.id == job_id
        print(f"READ Job: '{retrieved_job.job_data['title']}'")

        job_update_data = JobUpdate(status="closed")
        updated_job = update_job(db=db, db_job=retrieved_job, job_in=job_update_data)
        assert updated_job and updated_job.status == "closed"
        print(
            f"UPDATE Job: '{updated_job.job_data['title']}', New Status: {updated_job.status}"
        )
        # delete_job is tested at the end.

        # --- 5. JobFormKeyConstraint ---
        print("\\n--- Testing JobFormKeyConstraint ---")
        constraint_data = {
            "job_id": job_id,
            "form_key_id": form_key_id,
            "constraints": {"min_value": 1},
        }
        constraint_in = JobFormKeyConstraintCreate(**constraint_data)
        created_constraint = create_job_form_key_constraint(
            db=db, constraint_in=constraint_in
        )
        assert created_constraint and created_constraint.constraints["min_value"] == 1
        print(
            f"CREATE JobFormKeyConstraint (ID: {created_constraint.id}) for Job ID: {job_id}, FormKey ID: {form_key_id}"
        )
        constraint_id = created_constraint.id

        retrieved_constraint = get_job_form_key_constraint(
            db=db, constraint_id=constraint_id
        )
        assert retrieved_constraint and retrieved_constraint.id == constraint_id
        print(f"READ JobFormKeyConstraint: ID {retrieved_constraint.id}")

        constraint_update_data = JobFormKeyConstraintUpdate(
            constraints={"min_value": 2, "max_value": 5}
        )
        updated_constraint = update_job_form_key_constraint(
            db=db,
            db_constraint=retrieved_constraint,
            constraint_in=constraint_update_data,
        )
        assert updated_constraint and updated_constraint.constraints["max_value"] == 5
        print(
            f"UPDATE JobFormKeyConstraint: ID {updated_constraint.id}, New Constraints: {updated_constraint.constraints}"
        )

        # deleted_constraint = delete_job_form_key_constraint(db=db, constraint_id=constraint_id)
        # assert deleted_constraint and deleted_constraint.id == constraint_id
        # assert get_job_form_key_constraint(db=db, constraint_id=constraint_id) is None
        # print(f"DELETE JobFormKeyConstraint: ID {deleted_constraint.id}")

        # --- 6. Candidate ---
        print("\n--- Testing Candidate ---")
        # Use AgentClient to parse the candidate's resume text
        resume_text = (
            candidate_data["full_name"]
            + "\n"
            + candidate_data["email"]
            + "\n"
            + candidate_data["phone"]
        )
        pdf = "/storage/hussein/matching/ai/app/services/llm/Charbel_Daher_Resume.pdf"
        system_prompt = "Extract structured information from resumes. Focus on contact details, skills, and work experience."
        # Use the Candidates schema from resume_upload.py
        schema = Resume_Data.model_json_schema()
        parser_client = AgentClient(system_prompt, schema, [pdf])
        parsed_result = parser_client.parse()
        # Store the parsed result in parsed_resume field
        candidate_data["parsed_resume"] = parsed_result
        candidate_in = CandidateCreate(**candidate_data)
        created_candidate = create_candidate(db=db, candidate_in=candidate_in)
        assert created_candidate and created_candidate.email == candidate_data["email"]
        print(
            f"CREATE Candidate: {created_candidate.full_name} (ID: {created_candidate.id})"
        )
        candidate_id = created_candidate.id

        retrieved_candidate = get_candidate(db=db, candidate_id=candidate_id)
        assert retrieved_candidate and retrieved_candidate.id == candidate_id
        print(f"READ Candidate: {retrieved_candidate.full_name}")

        candidate_update_data = CandidateUpdate(phone="0987654321")
        updated_candidate = update_candidate(
            db=db, db_candidate=retrieved_candidate, candidate_in=candidate_update_data
        )
        assert updated_candidate and updated_candidate.phone == "0987654321"
        print(
            f"UPDATE Candidate: {updated_candidate.full_name}, New Phone: {updated_candidate.phone}"
        )
        # delete_candidate is tested at the end.

        # --- 7. Application ---
        print("\\n--- Testing Application ---")
        application_in_data = {
            **application_data,
            "candidate_id": candidate_id,
            "job_id": job_id,
        }
        application_in = ApplicationCreate(**application_in_data)
        created_application = create_application(db=db, application_in=application_in)
        assert created_application and created_application.candidate_id == candidate_id
        print(
            f"CREATE Application (ID: {created_application.id}) for Candidate ID: {candidate_id}, Job ID: {job_id}"
        )
        application_id = created_application.id

        retrieved_application = get_application(db=db, application_id=application_id)
        assert retrieved_application and retrieved_application.id == application_id
        print(f"READ Application: ID {retrieved_application.id}")

        application_update_data = ApplicationUpdate(
            form_responses={"experience": "4 years", "status": "interview"}
        )
        updated_application = update_application(
            db=db,
            db_application=retrieved_application,
            application_in=application_update_data,
        )
        assert (
            updated_application
            and updated_application.form_responses["status"] == "interview"
        )
        print(
            f"UPDATE Application: ID {updated_application.id}, New Form Responses: {updated_application.form_responses}"
        )
        # delete_application is tested at the end.

        # --- 8. Match ---
        print("\\n--- Testing Match ---")
        match_in_data = {**match_data, "application_id": application_id}
        match_in = MatchCreate(**match_in_data)
        created_match, ai_response = create_match(db=db, match_in=match_in)
        assert created_match and created_match.match_result == ai_response
        print(
            f"CREATE Match (ID: {created_match.id}) for Application ID: {application_id}"
        )
        match_id = created_match.id

        retrieved_match = get_match(db=db, match_id=match_id)
        assert retrieved_match and retrieved_match.id == match_id
        print(
            f"READ Match: ID {retrieved_match.id}, Score: {retrieved_match.match_result}"
        )

        match_update_data = MatchUpdate(match_result=ai_response)
        updated_match = update_match(
            db=db, db_match=retrieved_match, match_in=match_update_data
        )
        assert updated_match and updated_match.match_result == ai_response
        print(
            f"UPDATE Match: ID {updated_match.id}, New Score: {updated_match.match_result}"
        )

        # deleted_match = delete_match(db=db, match_id=match_id)
        # assert deleted_match and deleted_match.id == match_id
        # assert get_match(db=db, match_id=match_id) is None
        # print(f"DELETE Match: ID {deleted_match.id}")

        # --- 9. RecruiterCompanyLink ---
        print("\n--- Testing RecruiterCompanyLink ---")
        # Create a second company to be the recruiter (TargetLinkCo)
        recruiter_company_in = CompanyCreate(**company_data_target)
        created_recruiter_company = create_company(
            db=db, company_in=recruiter_company_in
        )
        assert (
            created_recruiter_company
            and created_recruiter_company.name == company_data_target["name"]
        )
        print(
            f"CREATE Recruiter Company: {created_recruiter_company.name} (ID: {created_recruiter_company.id})"
        )
        recruiter_employer_id = created_recruiter_company.id

        # Create HR for the recruiter company
        recruiter_hr_data = {
            **hr_data,
            "email": "hr@targetlinkco.com",
            "full_name": "Recruiter HR",
        }
        recruiter_hr_in_data = {
            **recruiter_hr_data,
            "employer_id": recruiter_employer_id,
        }
        recruiter_hr_in = HRCreate(**recruiter_hr_in_data)
        created_recruiter_hr = create_hr(db=db, hr_in=recruiter_hr_in)
        assert (
            created_recruiter_hr
            and created_recruiter_hr.email == recruiter_hr_data["email"]
        )
        print(
            f"CREATE Recruiter HR: {created_recruiter_hr.full_name} (ID: {created_recruiter_hr.id})"
        )
        recruiter_hr_id = created_recruiter_hr.id

        # Create link where TargetLinkCo is the recruiter and TestCo is the target
        link_data = {
            "recruiter_id": recruiter_employer_id,
            "target_employer_id": employer_id,
        }
        link_in = RecruiterCompanyLinkCreate(**link_data)
        created_link = create_recruiter_company_link(db=db, link_in=link_in)
        assert created_link and created_link.target_employer_id == employer_id
        print(
            f"CREATE RecruiterCompanyLink (ID: {created_link.id}) from Recruiter {recruiter_employer_id} to Target {employer_id}"
        )
        link_id = created_link.id

        # Create a job through the recruiter for the target company
        recruiter_job_data = {
            "job_data": {
                "title": "Senior Software Engineer",
                "description": "Recruited position for TestCo",
            },
            "status": "open",
            "form_key_ids": [],
        }
        recruiter_job_in_data = {
            **recruiter_job_data,
            "employer_id": recruiter_employer_id,  # Recruiter company creates the job
            "recruited_to_id": employer_id,  # But it's for TestCo
            "created_by": recruiter_hr_id,  # Created by recruiter's HR
        }
        recruiter_job_in = JobCreate(**recruiter_job_in_data)
        created_recruiter_job = create_job(db=db, job_in=recruiter_job_in)
        assert (
            created_recruiter_job
            and created_recruiter_job.job_data["title"]
            == recruiter_job_data["job_data"]["title"]
        )
        print(
            f"CREATE Recruited Job: '{created_recruiter_job.job_data['title']}' (ID: {created_recruiter_job.id})"
        )
        print(f"  - Created by Recruiter Company: {created_recruiter_company.name}")
        print(f"  - For Target Company: {created_company.name}")
        print(f"  - Created by HR: {created_recruiter_hr.full_name}")

        retrieved_link = get_recruiter_company_link(db=db, link_id=link_id)
        assert retrieved_link and retrieved_link.id == link_id
        print(f"READ RecruiterCompanyLink: ID {retrieved_link.id}")

        # RecruiterCompanyLinkUpdate schema does not exist / model has no updatable fields other than FKs.
        # Update test for RecruiterCompanyLink is skipped. If model changes, add this.
        print(
            "UPDATE RecruiterCompanyLink: Skipped (no updatable fields in current model/schema)"
        )

        # deleted_link = delete_recruiter_company_link(db=db, link_id=link_id)
        # assert deleted_link and deleted_link.id == link_id
        # assert get_recruiter_company_link(db=db, link_id=link_id) is None
        # print(f"DELETE RecruiterCompanyLink: ID {deleted_link.id}")

        # # Clean up the target company created for the link
        # deleted_target_company = delete_company(db=db, employer_id=target_employer_id)
        # assert deleted_target_company and deleted_target_company.id == target_employer_id
        # assert get_company(db=db, employer_id=target_employer_id) is None
        # print(f"DELETE Target Company for Link: {deleted_target_company.name} (ID: {target_employer_id})")

        # --- Final Cleanup (in reverse order of creation due to dependencies) ---
        print("\\n--- Final Cleanup ---")

        # Match already deleted in its section
        # JobFormKeyConstraint already deleted in its section
        # RecruiterCompanyLink already deleted in its section & its target company

        # if 'application_id' in locals() and get_application(db=db, application_id=application_id):
        #     deleted_application = delete_application(db=db, application_id=application_id)
        #     assert deleted_application and deleted_application.id == application_id
        #     assert get_application(db=db, application_id=application_id) is None
        #     print(f"DELETE Application: ID {application_id}")

        # if 'candidate_id' in locals() and get_candidate(db=db, candidate_id=candidate_id):
        #     deleted_candidate = delete_candidate(db=db, candidate_id=candidate_id)
        #     assert deleted_candidate and deleted_candidate.id == candidate_id
        #     assert get_candidate(db=db, candidate_id=candidate_id) is None
        #     print(f"DELETE Candidate: ID {candidate_id}")

        # # JobFormKeyConstraint depends on Job and FormKey (deleted above)

        # if 'job_id' in locals() and get_job(db=db, job_id=job_id):
        #     deleted_job = delete_job(db=db, job_id=job_id)
        #     assert deleted_job and deleted_job.id == job_id
        #     assert get_job(db=db, job_id=job_id) is None
        #     print(f"DELETE Job: ID {job_id}")

        # if 'form_key_id' in locals() and get_form_key(db=db, form_key_id=form_key_id):
        #     deleted_form_key = delete_form_key(db=db, form_key_id=form_key_id)
        #     assert deleted_form_key and deleted_form_key.id == form_key_id
        #     assert get_form_key(db=db, form_key_id=form_key_id) is None
        #     print(f"DELETE FormKey: ID {form_key_id}")

        # if 'hr_id' in locals() and get_hr(db=db, hr_id=hr_id):
        #     deleted_hr = delete_hr(db=db, hr_id=hr_id)
        #     assert deleted_hr and deleted_hr.id == hr_id
        #     assert get_hr(db=db, hr_id=hr_id) is None
        #     print(f"DELETE HR: ID {hr_id}")

        # if 'employer_id' in locals() and get_company(db=db, employer_id=employer_id):
        #     deleted_company = delete_company(db=db, employer_id=employer_id)
        #     assert deleted_company and deleted_company.id == employer_id
        #     assert get_company(db=db, employer_id=employer_id) is None
        #     print(f"DELETE Company: ID {employer_id}")

        print("\\n=== Sequential CRUD Tests Completed Successfully! ===")

    except AssertionError as e:
        print(f"\\nXXX ASSERTION FAILED XXX: {e}")
    except Exception as e:
        print(f"\\nXXX AN ERROR OCCURRED XXX: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()
        print("Database session closed.")


if __name__ == "__main__":
    run_sequential_crud_tests()
