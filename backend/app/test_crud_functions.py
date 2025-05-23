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
    CompanyCreate, CompanyUpdate,
    HRCreate, HRUpdate,
    RecruiterCompanyLinkCreate, RecruiterCompanyLinkUpdate,
    FormKeyCreate, FormKeyUpdate,
    JobFormKeyConstraintCreate, JobFormKeyConstraintUpdate,
    JobCreate, JobUpdate,
    CandidateCreate, CandidateUpdate,
    ApplicationCreate, ApplicationUpdate,
    MatchCreate, MatchUpdate
)

# CRUD functions
from crud import (
    create_company, get_company, get_company_by_name, get_companies, update_company, delete_company,
    create_hr, get_hr, get_hr_by_email, get_hrs, get_hrs_by_company, update_hr, delete_hr,
    create_recruiter_company_link, get_recruiter_company_link, get_recruiter_company_links_by_recruiter, get_recruiter_company_links_by_target_company, update_recruiter_company_link, delete_recruiter_company_link,
    create_form_key, get_form_key, get_form_keys_by_company, update_form_key, delete_form_key,
    create_job_form_key_constraint, get_job_form_key_constraint, get_job_form_key_constraints_by_job, update_job_form_key_constraint, delete_job_form_key_constraint,
    create_job, get_job, get_jobs, get_jobs_by_employer, get_jobs_by_status, update_job, delete_job,
    create_candidate, get_candidate, get_candidate_by_email, get_candidates, update_candidate, delete_candidate,
    create_application, get_application, get_applications_by_job, get_applications_by_candidate, update_application, delete_application,
    create_match, get_match, get_matches_by_application, update_match, delete_match
)

from core.database import get_session, create_db_and_tables
create_db_and_tables()
db = next(get_session())

# Test data
test_company_data_1 = {"name": "MainTestCo", "description": "A main test company", "industry": "Tech", "bio": "Main bio", "website": "http://maintestco.com", "is_owner": True}
test_company_data_2 = {"name": "TargetCo", "description": "A target company for linking", "industry": "Services", "bio": "Target bio", "website": "http://targetco.com", "is_owner": False}
test_hr_data_1 = {"email": "hr_main@testco.com", "password_hash": "hashed_password_main", "full_name": "Main Test HR", "role": "hr_manager"}
test_job_data_1 = {"job_data": {"title": "Lead Developer", "description": "Develop amazing things"}, "status": "draft", "form_key_ids": []}
test_candidate_data_1 = {"full_name": "John Doe", "email": "john.doe@example.com", "phone": "123-456-7890", "resume_url": "http://example.com/resume.pdf"}
test_form_key_data_1 = {"name": "YearsExperience", "field_type": "number", "required": True, "enum_values": None}


def test_company_crud(db: Session):
    print("\n--- Testing Company CRUD ---")
    # Create
    company_in = CompanyCreate(**test_company_data_1)
    created_company = create_company(db=db, company_in=company_in)
    assert created_company is not None
    assert created_company.name == test_company_data_1["name"]
    print(f"Created company: {created_company.name} (ID: {created_company.id})")

    # Get by ID
    retrieved_company = get_company(db=db, company_id=created_company.id)
    assert retrieved_company is not None
    assert retrieved_company.id == created_company.id
    print(f"Retrieved company by ID: {retrieved_company.name}")

    # Get by Name
    retrieved_company_by_name = get_company_by_name(db=db, name=test_company_data_1["name"])
    assert retrieved_company_by_name is not None
    assert retrieved_company_by_name.name == test_company_data_1["name"]
    print(f"Retrieved company by Name: {retrieved_company_by_name.name}")

    # Get all
    companies = get_companies(db=db, limit=5) # Limit to avoid too many if other tests run
    assert any(c.id == created_company.id for c in companies)
    print(f"Retrieved companies (first 5): {[c.name for c in companies]}")

    # Update
    update_data = CompanyUpdate(description="Updated main company description")
    # When using model_validate for db_company, SQLModel might treat it as new if ID is missing or relationships are complex.
    # It's safer to fetch the instance first if not passed directly.
    db_company_to_update = get_company(db=db, company_id=created_company.id)
    updated_company = update_company(db=db, db_company=db_company_to_update, company_in=update_data)
    assert updated_company.description == "Updated main company description"
    print(f"Updated company: {updated_company.name}, new desc: {updated_company.description}")

    return created_company

def test_hr_crud(db: Session, company_id: int):
    print("\n--- Testing HR CRUD ---")
    hr_in_data = {**test_hr_data_1, "company_id": company_id}
    hr_in = HRCreate(**hr_in_data)
    created_hr = create_hr(db=db, hr_in=hr_in)
    assert created_hr is not None and created_hr.company_id == company_id
    print(f"Created HR: {created_hr.full_name} for company ID {company_id}")

    retrieved_hr = get_hr(db=db, hr_id=created_hr.id)
    assert retrieved_hr is not None and retrieved_hr.id == created_hr.id
    print(f"Retrieved HR by ID: {retrieved_hr.full_name}")
    
    retrieved_hr_by_email = get_hr_by_email(db=db, email=test_hr_data_1["email"])
    assert retrieved_hr_by_email is not None and retrieved_hr_by_email.email == test_hr_data_1["email"]
    print(f"Retrieved HR by email: {retrieved_hr_by_email.full_name}")

    update_data = HRUpdate(full_name="Super Main Test HR")
    db_hr_to_update = get_hr(db=db, hr_id=created_hr.id)
    updated_hr = update_hr(db=db, db_hr=db_hr_to_update, hr_in=update_data)
    assert updated_hr.full_name == "Super Main Test HR"
    print(f"Updated HR: {updated_hr.full_name}")
    return created_hr

def test_job_crud(db: Session, company_id: int, hr_id: int):
    print("\n--- Testing Job CRUD ---")
    job_in_data = {**test_job_data_1, "employer_id": company_id, "created_by": hr_id}
    job_in = JobCreate(**job_in_data)
    created_job = create_job(db=db, job_in=job_in)
    assert created_job is not None and created_job.employer_id == company_id
    print(f"Created Job: {created_job.job_data['title']}")

    retrieved_job = get_job(db=db, job_id=created_job.id)
    assert retrieved_job is not None and retrieved_job.id == created_job.id
    print(f"Retrieved Job by ID: {retrieved_job.job_data['title']}")

    update_data = JobUpdate(status="published", job_data={"title": "Senior Lead Developer", "description": "Lead and develop amazing things"})
    db_job_to_update = get_job(db=db, job_id=created_job.id)
    updated_job = update_job(db=db, db_job=db_job_to_update, job_in=update_data)
    assert updated_job.status == "published" and updated_job.job_data["title"] == "Senior Lead Developer"
    print(f"Updated Job: {updated_job.job_data['title']}, new status: {updated_job.status}")
    return created_job

def test_candidate_crud(db: Session):
    print("\n--- Testing Candidate CRUD ---")
    candidate_in = CandidateCreate(**test_candidate_data_1)
    created_candidate = create_candidate(db=db, candidate_in=candidate_in)
    assert created_candidate is not None and created_candidate.email == test_candidate_data_1["email"]
    print(f"Created candidate: {created_candidate.full_name}")
    
    retrieved_candidate = get_candidate(db=db, candidate_id=created_candidate.id)
    assert retrieved_candidate is not None and retrieved_candidate.id == created_candidate.id
    print(f"Retrieved candidate by ID: {retrieved_candidate.full_name}")

    update_data = CandidateUpdate(phone="987-654-3210")
    db_candidate_to_update = get_candidate(db=db, candidate_id=created_candidate.id)
    updated_candidate = update_candidate(db=db, db_candidate=db_candidate_to_update, candidate_in=update_data)
    assert updated_candidate.phone == "987-654-3210"
    print(f"Updated candidate: {updated_candidate.full_name}")
    return created_candidate

def test_application_crud(db: Session, candidate_id: int, job_id: int):
    print("\n--- Testing Application CRUD ---")
    application_data = {"candidate_id": candidate_id, "job_id": job_id, "form_responses": {"experience": "5 years"}}
    application_in = ApplicationCreate(**application_data)
    created_application = create_application(db=db, application_in=application_in)
    assert created_application is not None and created_application.candidate_id == candidate_id
    print(f"Created application for candidate {candidate_id} to job {job_id}")

    retrieved_application = get_application(db=db, application_id=created_application.id)
    assert retrieved_application is not None and retrieved_application.id == created_application.id
    print(f"Retrieved application by ID: {retrieved_application.id}")
    
    update_data = ApplicationUpdate(form_responses={"experience": "6 years", "availability": "ASAP"})
    db_application_to_update = get_application(db=db, application_id=created_application.id)
    updated_application = update_application(db=db, db_application=db_application_to_update, application_in=update_data)
    assert updated_application.form_responses["experience"] == "6 years"
    print(f"Updated application {updated_application.id}")
    return created_application

def test_match_crud(db: Session, application_id: int):
    print("\n--- Testing Match CRUD ---")
    match_data = {"application_id": application_id, "match_score": 0.75, "attribute_scores": {"technical_fit": 0.8, "culture_fit": 0.7}}
    match_in = MatchCreate(**match_data)
    created_match = create_match(db=db, match_in=match_in)
    assert created_match is not None and created_match.application_id == application_id
    print(f"Created match for application {application_id} with score {created_match.match_score}")

    retrieved_match = get_match(db=db, match_id=created_match.id)
    assert retrieved_match is not None and retrieved_match.id == created_match.id
    print(f"Retrieved match by ID: {retrieved_match.id}")

    update_data = MatchUpdate(match_score=0.88, narrative_explanation="Strong candidate after interview.")
    db_match_to_update = get_match(db=db, match_id=created_match.id)
    updated_match = update_match(db=db, db_match=db_match_to_update, match_in=update_data)
    assert updated_match.match_score == 0.88
    print(f"Updated match {updated_match.id} with new score {updated_match.match_score}")
    
    deleted_match = delete_match(db=db, match_id=updated_match.id)
    assert deleted_match is not None and deleted_match.id == updated_match.id
    assert get_match(db=db, match_id=updated_match.id) is None
    print(f"Deleted match: {deleted_match.id}")

def test_form_key_crud(db: Session, company_id: int):
    print("\n--- Testing FormKey CRUD ---")
    fk_data = {**test_form_key_data_1, "company_id": company_id}
    form_key_in = FormKeyCreate(**fk_data)
    created_form_key = create_form_key(db=db, form_key_in=form_key_in)
    assert created_form_key is not None and created_form_key.company_id == company_id
    print(f"Created form key: {created_form_key.name} for company {company_id}")

    retrieved_fk = get_form_key(db=db, form_key_id=created_form_key.id)
    assert retrieved_fk is not None and retrieved_fk.id == created_form_key.id
    print(f"Retrieved form key by ID: {retrieved_fk.name}")
    
    update_data = FormKeyUpdate(name="TotalYearsExperience", field_type="integer")
    db_fk_to_update = get_form_key(db=db, form_key_id=created_form_key.id)
    updated_fk = update_form_key(db=db, db_form_key=db_fk_to_update, form_key_in=update_data)
    assert updated_fk.name == "TotalYearsExperience"
    print(f"Updated form key: {updated_fk.name}")
    return created_form_key

def test_job_form_key_constraint_crud(db: Session, job_id: int, form_key_id: int):
    print("\n--- Testing JobFormKeyConstraint CRUD ---")
    constraint_data = {"job_id": job_id, "form_key_id": form_key_id, "constraints": {"min_value": 1, "max_value": 10}}
    constraint_in = JobFormKeyConstraintCreate(**constraint_data)
    created_constraint = create_job_form_key_constraint(db=db, constraint_in=constraint_in)
    assert created_constraint is not None and created_constraint.job_id == job_id
    print(f"Created constraint for job {job_id} and form key {form_key_id}")
    
    retrieved_constraint = get_job_form_key_constraint(db=db, constraint_id=created_constraint.id)
    assert retrieved_constraint is not None and retrieved_constraint.id == created_constraint.id
    print(f"Retrieved constraint by ID: {retrieved_constraint.id}")

    update_data = JobFormKeyConstraintUpdate(constraints={"min_value": 2, "max_value": 8, "message": "Must be between 2 and 8"})
    db_constraint_to_update = get_job_form_key_constraint(db=db, constraint_id=created_constraint.id)
    updated_constraint = update_job_form_key_constraint(db=db, db_constraint=db_constraint_to_update, constraint_in=update_data)
    assert updated_constraint.constraints["min_value"] == 2
    print(f"Updated constraint {updated_constraint.id}")

    deleted_constraint = delete_job_form_key_constraint(db=db, constraint_id=updated_constraint.id)
    assert deleted_constraint is not None and deleted_constraint.id == updated_constraint.id
    assert get_job_form_key_constraint(db=db, constraint_id=updated_constraint.id) is None
    print(f"Deleted constraint: {deleted_constraint.id}")


def test_recruiter_company_link_crud(db: Session, company1_id: int):
    print("\n--- Testing RecruiterCompanyLink CRUD ---")
    company2_in = CompanyCreate(**test_company_data_2)
    company2 = create_company(db=db, company_in=company2_in)
    assert company2 is not None
    print(f"Created target company for link: {company2.name} (ID: {company2.id})")

    link_data = {"recruiter_id": company1_id, "target_company_id": company2.id}
    link_in = RecruiterCompanyLinkCreate(**link_data)
    created_link = create_recruiter_company_link(db=db, link_in=link_in)
    assert created_link is not None and created_link.recruiter_id == company1_id
    print(f"Created recruiter link between company {company1_id} and {company2.id}")

    retrieved_link = get_recruiter_company_link(db=db, link_id=created_link.id)
    assert retrieved_link is not None and retrieved_link.id == created_link.id
    print(f"Retrieved link by ID: {retrieved_link.id}")
    
    # Update for RecruiterCompanyLink is less common. If needed, it would usually involve changing one of the foreign keys.
    # For this test, we'll skip direct update and focus on create/get/delete.

    deleted_link = delete_recruiter_company_link(db=db, link_id=created_link.id)
    assert deleted_link is not None and deleted_link.id == created_link.id
    assert get_recruiter_company_link(db=db, link_id=created_link.id) is None
    print(f"Deleted recruiter link: {deleted_link.id}")

    deleted_company2 = delete_company(db=db, company_id=company2.id)
    assert deleted_company2 is not None and get_company(db=db, company_id=company2.id) is None
    print(f"Cleaned up target company: {deleted_company2.name}")


def run_all_tests():
    created_entities_ids = {}

    try:
        print("=== Starting CRUD Function Tests ===")
        # Company
        company1 = test_company_crud(db)
        created_entities_ids["company1"] = company1.id

        # HR
        hr1 = test_hr_crud(db, company_id=company1.id)
        created_entities_ids["hr1"] = hr1.id

        # Job
        job1 = test_job_crud(db, company_id=company1.id, hr_id=hr1.id)
        created_entities_ids["job1"] = job1.id
        
        # FormKey
        form_key1 = test_form_key_crud(db, company_id=company1.id)
        created_entities_ids["form_key1"] = form_key1.id

        # JobFormKeyConstraint (deleted within its test)
        test_job_form_key_constraint_crud(db, job_id=job1.id, form_key_id=form_key1.id)
        
        # Candidate
        candidate1 = test_candidate_crud(db)
        created_entities_ids["candidate1"] = candidate1.id

        # Application
        application1 = test_application_crud(db, candidate_id=candidate1.id, job_id=job1.id)
        created_entities_ids["application1"] = application1.id

        # Match (deleted within its test)
        test_match_crud(db, application_id=application1.id)

        # RecruiterCompanyLink (link and target company deleted within its test)
        test_recruiter_company_link_crud(db, company1_id=company1.id)

        print("\n--- Final Cleanup of Remaining Entities ---")
        
        # Order matters for foreign key constraints
        if "application1" in created_entities_ids:
            app_id = created_entities_ids["application1"]
            if get_application(db=db, application_id=app_id): # Check if not deleted by other means
                 deleted_app = delete_application(db=db, application_id=app_id)
                 assert deleted_app is not None, f"Application {app_id} should have been deleted"
                 assert get_application(db=db, application_id=app_id) is None, f"Application {app_id} still exists after delete"
                 print(f"Deleted application: {app_id}")
            else:
                print(f"Application {app_id} already deleted or not found.")


        if "candidate1" in created_entities_ids:
            cand_id = created_entities_ids["candidate1"]
            if get_candidate(db=db, candidate_id=cand_id):
                deleted_candidate = delete_candidate(db=db, candidate_id=cand_id)
                assert deleted_candidate is not None
                assert get_candidate(db=db, candidate_id=cand_id) is None
                print(f"Deleted candidate: {cand_id}")

        if "form_key1" in created_entities_ids: # JobFormKeyConstraint depends on this
            fk_id = created_entities_ids["form_key1"]
            if get_form_key(db=db, form_key_id=fk_id):
                deleted_fk = delete_form_key(db=db, form_key_id=fk_id)
                assert deleted_fk is not None
                assert get_form_key(db=db, form_key_id=fk_id) is None
                print(f"Deleted form key: {fk_id}")
        
        if "job1" in created_entities_ids: # Application depends on this
            j_id = created_entities_ids["job1"]
            if get_job(db=db, job_id=j_id):
                deleted_job = delete_job(db=db, job_id=j_id)
                assert deleted_job is not None
                assert get_job(db=db, job_id=j_id) is None
                print(f"Deleted job: {j_id}")
        
        if "hr1" in created_entities_ids: # Job depends on this
            h_id = created_entities_ids["hr1"]
            if get_hr(db=db, hr_id=h_id):
                deleted_hr = delete_hr(db=db, hr_id=h_id)
                assert deleted_hr is not None
                assert get_hr(db=db, hr_id=h_id) is None
                print(f"Deleted HR: {h_id}")

        if "company1" in created_entities_ids: # HR, Job, FormKey, RecruiterLink depend on this
            c_id = created_entities_ids["company1"]
            if get_company(db=db, company_id=c_id):
                deleted_company1 = delete_company(db=db, company_id=c_id)
                assert deleted_company1 is not None
                assert get_company(db=db, company_id=c_id) is None
                print(f"Deleted company: {c_id}")
        
        print("\n=== All tests completed and cleaned up successfully! ===")

    except AssertionError as e:
        print(f"\nXXX ASSERTION FAILED XXX: {e}")
    except Exception as e:
        print(f"\nXXX AN ERROR OCCURRED XXX: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_all_tests()
