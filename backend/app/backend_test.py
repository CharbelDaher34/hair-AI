import os
import uuid
from fastapi.testclient import TestClient
from datetime import datetime # Import datetime
import base64
import httpx
import json
from core.database import create_db_and_tables
from models.candidate_pydantic import CandidateResume
create_db_and_tables()
# Import main directly since it's in the same directory
# from main import app  # Direct import from same directory
API_V1_PREFIX = "http://localhost:8017/api/v1"
client = httpx.Client(base_url=API_V1_PREFIX)
# client = TestClient(app)
# create_db_and_tables()


def run_api_tests():
    print("=== Starting API Endpoint Tests ===")

    # To store IDs of created resources
    employer_id: uuid.UUID | None = None
    hr_id: uuid.UUID | None = None
    form_key_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    constraint_id: uuid.UUID | None = None
    candidate_id: uuid.UUID | None = None
    application_id: uuid.UUID | None = None
    match_id: uuid.UUID | None = None
    recruiter_employer_id: uuid.UUID | None = None
    recruiter_hr_id: uuid.UUID | None = None
    link_id: uuid.UUID | None = None
    created_recruiter_job_id: uuid.UUID | None = None

    # Test data (mirrors test_crud_functions.py)
    company_data = {
        "name": "ApiTestCo",
        "description": "A test company via API",
        "industry": "Tech",
        "is_owner": True,
        "bio": "This is a test bio for ApiTestCo.",
        "website": "https://apitestco.example.com",
        "logo_url": "https://apitestco.example.com/logo.png"
    }
    hr_data = {
        "email": "hr.api@testco.com",
        "password": "hashed_password_api",
        "full_name": "Api Test HR",
        "role": "hr_manager"
        # employer_id will be added dynamically
    }
    form_key_data = {
        "name": "ExperienceYearsApi",
        "field_type": "number",
        "required": True,
        "enum_values": ["1-2", "3-5", "5+"],
        # employer_id will be added dynamically
    }
    job_data_payload = {
        "title": "API Software Engineer",
        "description": "Develop software via API",
        "location": "Remote",
        "salary_min": 100000,
        "salary_max": 150000,
        "experience_level": "1-3_years",
        "seniority_level": "entry",
        "status": "published",
        "job_type": "full_time",
        "job_category": "software_engineering",
        "recruited_to_id": None,
        "job_data": {}
    }
    candidate_resume_data = {
        "full_name": "Api Test Candidate",
        "email": "candidate.api@example.com",
        "phone": "1234567890",
        "work_history": [
            {
                "job_title": "Software Engineer",
                "employer": "ApiTestCo",
                "location": "Remote",
                "employment_type": "Full-time",
                "start_date": "2021-01-01",
                "end_date": None,
                "summary": "Worked on API development."
            }
        ],
        "education": [
            {
                "level": "Bachelor’s",
                "degree_type": "Bachelor’s",
                "subject": "Computer Science",
                "start_date": "2017-09-01",
                "end_date": "2021-06-01",
                "institution": "Test University",
                "gpa": 3.8,
                "summary": "Graduated with honors."
            }
        ],
        "skills": [
            {"name": "Python", "category": "Programming Language", "level": "Expert"}
        ],
        "certifications": [
            {"certification": "AWS Certified Developer", "certification_group": "Cloud", "issued_by": "Amazon", "issue_date": "2022-05-01"}
        ]
    }
    candidate_data = {
        "full_name": "Api Test Candidate",
        "email": "candidate.api@example.com",
        "phone": "1234567890",
        "resume_url": "https://example.com/resume1.pdf",
    }
    application_data_payload = {
        "form_responses": {"experience_api": "3 years", "status": "applied", "extra_field": "extra_value"}
        # candidate_id, job_id will be added dynamically
    }
    match_data_payload = {
        "score": 0.85,
        "embedding_similarity": 0.828,
        "match_percentage": 50,
        "matching_skills": ["python"],
        "missing_skills": ["software engineer"],
        "extra_skills": [],
        "total_required_skills": 2,
        "matching_skills_count": 1,
        "missing_skills_count": 1,
        "extra_skills_count": 0,
        "skill_weight": 0.4,
        "embedding_weight": 0.6,
        "status": "pending"
        # application_id will be added dynamically
    }
    company_data_target = {
        "name": "ApiTargetLinkCo",
        "description": "A target company for linking via API",
        "is_owner": False,
        "bio": "Bio for the target link company.",
        "website": "https://apitargetlinkco.example.com",
        "logo_url": "https://apitargetlinkco.example.com/logo.png",
        "industry": "Recruitment"
    }
    # RecruiterCompanyLink data will be created dynamically with recruiter_id and target_employer_id
    # JobFormKeyConstraint data will be created dynamically with job_id, form_key_id, constraints

    # --- 1. Company ---
    print("\n--- Testing Company API ---")
    response = client.post(f"{API_V1_PREFIX}/companies/", json=company_data)
    assert response.status_code == 201, f"Failed to create company: {response.text}"
    created_company = response.json()
    assert created_company["name"] == company_data["name"]
    assert created_company["bio"] == company_data["bio"]
    employer_id = created_company["id"]
    print(f"CREATE Company: {created_company['name']} (ID: {employer_id})")

    response = client.get(f"{API_V1_PREFIX}/companies/{employer_id}")
    assert response.status_code == 200, response.text
    retrieved_company = response.json()
    assert retrieved_company["id"] == employer_id
    print(f"READ Company: {retrieved_company['name']}")

    company_update_data = {"description": "Updated API company description."}
    response = client.patch(f"{API_V1_PREFIX}/companies/{employer_id}", json=company_update_data)
    assert response.status_code == 200, response.text
    updated_company_res = response.json()
    assert updated_company_res["description"] == company_update_data["description"]
    print(f"UPDATE Company: {updated_company_res['name']}, New Description: {updated_company_res['description']}")

    # Test GET all companies
    response = client.get(f"{API_V1_PREFIX}/companies/")
    assert response.status_code == 200, response.text
    companies_list = response.json()
    assert isinstance(companies_list, list)
    assert any(c["id"] == employer_id for c in companies_list)
    print(f"READ Companies: Found {len(companies_list)} companies.")

    # --- 2. HR ---
    print("\n--- Testing HR API ---")
    
    hr_create_data = {**hr_data, "employer_id": employer_id}
    response = client.post(f"{API_V1_PREFIX}/auth/register", json=hr_create_data)
    assert response.status_code == 201, f"Failed to create HR: {response.text}"
   
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    response = client.get(f"{API_V1_PREFIX}/hrs/")
    assert response.status_code == 200, response.text
    retrieved_hr = response.json()
    print(retrieved_hr)
    hr_id = retrieved_hr["id"]
    print(f"READ HR: {retrieved_hr['full_name']}")

    # hr_update_data = {"full_name": "Updated Api Test HR Name"}
    # response = client.patch(f"{API_V1_PREFIX}/hrs/{hr_id}", json=hr_update_data)
    # assert response.status_code == 200, response.text
    # updated_hr_res = response.json()
    # assert updated_hr_res["full_name"] == hr_update_data["full_name"]
    # print(f"UPDATE HR: {updated_hr_res['full_name']}")

   
    # --- 3. FormKey ---
    print("\n--- Testing FormKey API ---")
    form_key_create_data = {**form_key_data, "employer_id": employer_id}
    response = client.post(f"{API_V1_PREFIX}/form_keys/", json=form_key_create_data)
    print(response)
    assert response.status_code == 201, f"Failed to create FormKey: {response.text}"
    created_form_key = response.json()
    assert created_form_key["name"] == form_key_data["name"]
    assert created_form_key["enum_values"] == form_key_data["enum_values"]
    form_key_id = created_form_key["id"]
    print(f"CREATE FormKey: {created_form_key['name']} (ID: {form_key_id}) for Company ID: {employer_id}")

    response = client.get(f"{API_V1_PREFIX}/form_keys/{form_key_id}")
    assert response.status_code == 200, response.text
    retrieved_form_key = response.json()
    assert retrieved_form_key["id"] == form_key_id
    print(f"READ FormKey: {retrieved_form_key['name']}")

    form_key_update_data = {"field_type": "text"}
    response = client.patch(f"{API_V1_PREFIX}/form_keys/{form_key_id}", json=form_key_update_data)
    assert response.status_code == 200, response.text
    updated_form_key_res = response.json()
    assert updated_form_key_res["field_type"] == "text"
    print(f"UPDATE FormKey: {updated_form_key_res['name']}, New Field Type: {updated_form_key_res['field_type']}")

    # --- 4. Job ---
    print("\n--- Testing Job API ---")
    job_create_data = {**job_data_payload, "recruited_to_id": employer_id}
    response = client.post(f"{API_V1_PREFIX}/jobs/", json=job_create_data)
    assert response.status_code == 201, f"Failed to create Job: {response.text}"
    created_job = response.json()
    assert created_job["title"] == job_data_payload["title"]
    assert created_job["description"] == job_data_payload["description"]
    assert created_job["location"] == job_data_payload["location"]
    assert created_job["salary_min"] == job_data_payload["salary_min"]
    assert created_job["salary_max"] == job_data_payload["salary_max"]
    assert created_job["experience_level"] == job_data_payload["experience_level"]
    assert created_job["seniority_level"] == job_data_payload["seniority_level"]
    assert created_job["job_type"] == job_data_payload["job_type"]
    job_id = created_job["id"]
    print(f"CREATE Job: '{created_job['title']}' (ID: {job_id}) for Company ID: {employer_id}, HR ID: {hr_id}")

    response = client.get(f"{API_V1_PREFIX}/jobs/{job_id}")
    assert response.status_code == 200, response.text
    retrieved_job = response.json()
    assert retrieved_job["id"] == job_id
    print(f"READ Job: '{retrieved_job['title']}'")

    job_update_data = {"status": "closed"}
    response = client.patch(f"{API_V1_PREFIX}/jobs/{job_id}", json=job_update_data)
    assert response.status_code == 200, response.text
    updated_job_res = response.json()
    assert updated_job_res["status"] == "closed"
    print(f"UPDATE Job: '{updated_job_res['title']}', New Status: {updated_job_res['status']}")

    # --- 5. JobFormKeyConstraint ---
    print("\n--- Testing JobFormKeyConstraint API ---")
    constraint_create_data = {"job_id": job_id, "form_key_id": form_key_id, "constraints": {"min_value": 1}}
    response = client.post(f"{API_V1_PREFIX}/job_form_key_constraints/", json=constraint_create_data)
    assert response.status_code == 201, f"Failed to create JobFormKeyConstraint: {response.text}"
    created_constraint = response.json()
    assert created_constraint["constraints"]["min_value"] == 1
    constraint_id = created_constraint["id"]
    print(f"CREATE JobFormKeyConstraint (ID: {constraint_id}) for Job ID: {job_id}, FormKey ID: {form_key_id}")

    response = client.get(f"{API_V1_PREFIX}/job_form_key_constraints/{constraint_id}")
    assert response.status_code == 200, response.text
    retrieved_constraint = response.json()
    assert retrieved_constraint["id"] == constraint_id
    print(f"READ JobFormKeyConstraint: ID {retrieved_constraint['id']}")

    constraint_update_data = {"constraints": {"min_value": 2, "max_value": 5}}
    response = client.patch(f"{API_V1_PREFIX}/job_form_key_constraints/{constraint_id}", json=constraint_update_data)
    assert response.status_code == 200, response.text
    updated_constraint_res = response.json()
    assert updated_constraint_res["constraints"]["max_value"] == 5
    print(f"UPDATE JobFormKeyConstraint: ID {updated_constraint_res['id']}, New Constraints: {updated_constraint_res['constraints']}")

    # --- 6. Candidate ---
    print("\n--- Testing Candidate API ---")
    resume_pdf_path = "/storage/hussein/matching/ai/app/services/llm/Charbel_Daher_Resume.pdf"
    with open(resume_pdf_path, "rb") as resume_file:
        files = {"resume": ("Charbel_Daher_Resume.pdf", resume_file, "application/pdf")}
        data = {"candidate_in": json.dumps(candidate_data)}
        response = client.post(
            f"{API_V1_PREFIX}/candidates/",
            data=data,
            files=files,
            timeout=None
        )
    assert response.status_code == 201, f"Failed to create Candidate: {response.text}"
    created_candidate = response.json()
    print(created_candidate)
    print(candidate_data)
    assert created_candidate["email"] == candidate_data["email"]
    candidate_id = created_candidate["id"]
    print(f"CREATE Candidate: {created_candidate['full_name']} (ID: {candidate_id})")

    response = client.get(f"{API_V1_PREFIX}/candidates/{candidate_id}")
    assert response.status_code == 200, response.text
    retrieved_candidate = response.json()
    assert retrieved_candidate["id"] == candidate_id
    print(f"READ Candidate: {retrieved_candidate['full_name']}")

    candidate_update_data = {"phone": "0987654321"}
    response = client.patch(f"{API_V1_PREFIX}/candidates/{candidate_id}", json=candidate_update_data)
    assert response.status_code == 200, response.text
    updated_candidate_res = response.json()
    assert updated_candidate_res["phone"] == "0987654321"
    print(f"UPDATE Candidate: {updated_candidate_res['full_name']}, New Phone: {updated_candidate_res['phone']}")

    # --- 7. Application ---
    print("\n--- Testing Application API ---")
    application_create_data = {**application_data_payload, "candidate_id": candidate_id, "job_id": job_id}
    response = client.post(f"{API_V1_PREFIX}/applications/", json=application_create_data,timeout=None)
    assert response.status_code == 201
    created_application = response.json()
    print(created_application)
    assert created_application["candidate_id"] == candidate_id
    application_id = created_application["id"]
    print(f"CREATE Application (ID: {application_id}) for Candidate ID: {candidate_id}, Job ID: {job_id}")

    response = client.get(f"{API_V1_PREFIX}/applications/{application_id}")
    assert response.status_code == 200, response.text
    retrieved_application = response.json()
    assert retrieved_application["id"] == application_id
    print(f"READ Application: ID {retrieved_application['id']}")

    application_update_data = {"form_responses": {"experience_api": "4 years", "status": "interview"}}
    response = client.patch(f"{API_V1_PREFIX}/applications/{application_id}", json=application_update_data)
    assert response.status_code == 200, response.text
    updated_application_res = response.json()
    assert updated_application_res["form_responses"]["status"] == "interview"
    print(f"UPDATE Application: ID {updated_application_res['id']}, New Form Responses: {updated_application_res['form_responses']}")

    # --- 8. Match ---
    try:
        
        
        response = client.get(f"{API_V1_PREFIX}/matches/by-application/{application_id}")
        assert response.status_code == 200, response.text
        retrieved_matches = response.json()
        match_id = retrieved_matches[0]["id"]
        print(f"READ Matches: ID {match_id}")
    
        
        response = client.patch(f"{API_V1_PREFIX}/matches/{match_id}", json=match_data_payload)
        assert response.status_code == 200, response.text
        updated_match_res = response.json()
        updated_results = updated_match_res["match_result"]["results"]
        assert updated_results[0]["candidate"] == "Updated candidate"
        assert updated_results[0]["score"] == 0.9
        assert updated_results[0]["skill_analysis"]["match_percentage"] == 100
        print(f"UPDATE Match: ID {updated_match_res['id']}, New Score: {updated_match_res['match_result']['results'][0]['score']}")
    except Exception as e:
        print("No match created for application",application_id)
     
    
    # --- 9. RecruiterCompanyLink ---
    print("\n--- Testing RecruiterCompanyLink API ---")
    # Create a second company to be the recruiter (ApiTargetLinkCo)
    response = client.post(f"{API_V1_PREFIX}/companies/", json=company_data_target)
    assert response.status_code == 201, f"Failed to create recruiter company: {response.text}"
    created_recruiter_company = response.json()
    assert created_recruiter_company["name"] == company_data_target["name"]
    assert created_recruiter_company["website"] == company_data_target["website"]
    recruiter_employer_id = created_recruiter_company["id"]
    print(f"CREATE Recruiter Company: {created_recruiter_company['name']} (ID: {recruiter_employer_id})")

    # Create HR for the recruiter company
    recruiter_hr_data = {**hr_data, "email": "hr.api@targetlinkco.com", "full_name": "Api Recruiter HR", "employer_id": recruiter_employer_id}
    response = client.post(f"{API_V1_PREFIX}/auth/register", json=recruiter_hr_data)
    assert response.status_code == 201, f"Failed to create recruiter HR: {response.text}"
    print(f"CREATE Recruiter HR.")

 
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    response = client.get(f"{API_V1_PREFIX}/hrs/")
    assert response.status_code == 200, response.text
    retrieved_hr = response.json()
   
    recruiter_hr_id = retrieved_hr["id"]
    print(f"READ HR: {retrieved_hr['full_name']}")
    

    # Create link where ApiTargetLinkCo is the recruiter and ApiTestCo is the target
    link_create_data = {"recruiter_id": recruiter_employer_id, "target_employer_id": employer_id}
    response = client.post(f"{API_V1_PREFIX}/recruiter_company_links/", json=link_create_data)
    assert response.status_code == 201, f"Failed to create RecruiterCompanyLink: {response.text}"
    created_link = response.json()
    assert created_link["target_employer_id"] == employer_id
    link_id = created_link["id"]
    print(f"CREATE RecruiterCompanyLink (ID: {link_id}) from Recruiter {recruiter_employer_id} to Target {employer_id}")

    response = client.get(f"{API_V1_PREFIX}/recruiter_company_links/{link_id}")
    assert response.status_code == 200, response.text
    retrieved_link = response.json()
    assert retrieved_link["id"] == link_id
    print(f"READ RecruiterCompanyLink: ID {retrieved_link['id']}")

    print("UPDATE RecruiterCompanyLink: Skipped (no updatable fields in current model/schema or not implemented)")
    
    # Create a job through the recruiter for the target company
    recruiter_job_data_payload = {
        "title": "Senior API Software Engineer",
        "description": "Recruited position for ApiTestCo",
        "location": "Remote",
        "salary_min": 100000,
        "salary_max": 150000,
        "experience_level": "1-3_years",
        "seniority_level": "entry",
        "status": "published",
        "job_type": "full_time",
        "job_category": "software_engineering",
        "recruited_to_id": employer_id,
        "job_data": {}
    }
    
    recruiter_job_create_data = {
        **recruiter_job_data_payload,
    }
    response = client.post(f"{API_V1_PREFIX}/jobs/", json=recruiter_job_create_data)
    assert response.status_code == 201, f"Failed to create recruited job: {response.text}"
    created_recruiter_job = response.json()
    created_recruiter_job_id = created_recruiter_job["id"]
    assert created_recruiter_job["title"] == recruiter_job_data_payload["title"]
    assert created_recruiter_job["description"] == recruiter_job_data_payload["description"]
    assert created_recruiter_job["location"] == recruiter_job_data_payload["location"]
    assert created_recruiter_job["salary_min"] == recruiter_job_data_payload["salary_min"]
    assert created_recruiter_job["salary_max"] == recruiter_job_data_payload["salary_max"]
    assert created_recruiter_job["experience_level"] == recruiter_job_data_payload["experience_level"]
    assert created_recruiter_job["seniority_level"] == recruiter_job_data_payload["seniority_level"]
    assert created_recruiter_job["job_type"] == recruiter_job_data_payload["job_type"]
    assert created_recruiter_job["job_category"] == recruiter_job_data_payload["job_category"]
    print(f"CREATE Recruited Job: '{created_recruiter_job['title']}' (ID: {created_recruiter_job_id}) for Target Company ID: {employer_id}")


    # --- Deletion Tests (in reverse order of dependency, or careful order) ---
    print("\n--- Testing Deletion API Endpoints ---")

    # # Matches depend on Applications
    # if match_id:
    #     response = client.delete(f"{API_V1_PREFIX}/matches/{match_id}")
    #     assert response.status_code == 200, response.text
    #     print(f"DELETE Match: ID {match_id}, response: {response.json()}")
    #     response = client.get(f"{API_V1_PREFIX}/matches/{match_id}")
    #     assert response.status_code == 404, "Match not deleted"
   
    # # Applications depend on Candidates and Jobs
    # if application_id:
    #     response = client.delete(f"{API_V1_PREFIX}/applications/{application_id}")
    #     assert response.status_code == 200, response.text
    #     print(f"DELETE Application: ID {application_id}, response: {response.json()}")
    #     response = client.get(f"{API_V1_PREFIX}/applications/{application_id}")
    #     assert response.status_code == 404, "Application not deleted"

    # # Candidates (standalone after applications)
    # if candidate_id:
    #     response = client.delete(f"{API_V1_PREFIX}/candidates/{candidate_id}")
    #     assert response.status_code == 200, response.text
    #     print(f"DELETE Candidate: ID {candidate_id}, response: {response.json()}")
    #     response = client.get(f"{API_V1_PREFIX}/candidates/{candidate_id}")
    #     assert response.status_code == 404, "Candidate not deleted"

    # # JobFormKeyConstraints depend on Jobs and FormKeys
    # if constraint_id:
    #     response = client.delete(f"{API_V1_PREFIX}/job_form_key_constraints/{constraint_id}")
    #     assert response.status_code == 200, response.text
    #     print(f"DELETE JobFormKeyConstraint: ID {constraint_id}, response: {response.json()}")
    #     response = client.get(f"{API_V1_PREFIX}/job_form_key_constraints/{constraint_id}")
    #     assert response.status_code == 404, "JobFormKeyConstraint not deleted"
    
    # # Recruited Job
    # if created_recruiter_job_id:
    #     response = client.delete(f"{API_V1_PREFIX}/jobs/{created_recruiter_job_id}")
    #     assert response.status_code == 200, response.text
    #     print(f"DELETE Recruited Job: ID {created_recruiter_job_id}, response: {response.json()}")
    #     response = client.get(f"{API_V1_PREFIX}/jobs/{created_recruiter_job_id}")
    #     assert response.status_code == 404, "Recruited Job not deleted"

    # # Jobs depend on Company (employer_id) and HR (created_by)
    # if job_id:
    #     response = client.delete(f"{API_V1_PREFIX}/jobs/{job_id}")
    #     assert response.status_code == 200, response.text
    #     print(f"DELETE Job: ID {job_id}, response: {response.json()}")
    #     response = client.get(f"{API_V1_PREFIX}/jobs/{job_id}")
    #     assert response.status_code == 404, "Job not deleted"

    # # FormKeys depend on Company
    # if form_key_id:
    #     response = client.delete(f"{API_V1_PREFIX}/form_keys/{form_key_id}")
    #     assert response.status_code == 200, response.text
    #     print(f"DELETE FormKey: ID {form_key_id}, response: {response.json()}")
    #     response = client.get(f"{API_V1_PREFIX}/form_keys/{form_key_id}")
    #     assert response.status_code == 404, "FormKey not deleted"

    # # RecruiterCompanyLinks depend on Recruiter Company and Target Company
    # if link_id:
    #     response = client.delete(f"{API_V1_PREFIX}/recruiter_company_links/{link_id}")
    #     assert response.status_code == 200, response.text
    #     print(f"DELETE RecruiterCompanyLink: ID {link_id}, response: {response.json()}")
    #     response = client.get(f"{API_V1_PREFIX}/recruiter_company_links/{link_id}")
    #     assert response.status_code == 404, "RecruiterCompanyLink not deleted"

    # # HRs depend on Company
    # if hr_id:
    #     response = client.delete(f"{API_V1_PREFIX}/hrs/{hr_id}")
    #     assert response.status_code == 200, response.text
    #     print(f"DELETE HR: ID {hr_id}, response: {response.json()}")
    #     response = client.get(f"{API_V1_PREFIX}/hrs/{hr_id}")
    #     assert response.status_code == 404, "HR not deleted"
    
    # if recruiter_hr_id:
    #     response = client.delete(f"{API_V1_PREFIX}/hrs/{recruiter_hr_id}")
    #     assert response.status_code == 200, response.text
    #     print(f"DELETE Recruiter HR: ID {recruiter_hr_id}, response: {response.json()}")
    #     response = client.get(f"{API_V1_PREFIX}/hrs/{recruiter_hr_id}")
    #     assert response.status_code == 404, "Recruiter HR not deleted"


    # # Companies (delete main company last, after its dependencies)
    # if employer_id:
    #     # Ensure all dependent entities (HR, Jobs, FormKeys, Links as target) are deleted or unlinked
    #     response = client.delete(f"{API_V1_PREFIX}/companies/{employer_id}")
    #     assert response.status_code == 200, response.text
    #     print(f"DELETE Company: ID {employer_id}, response: {response.json()}")
    #     response = client.get(f"{API_V1_PREFIX}/companies/{employer_id}")
    #     assert response.status_code == 404, "Company not deleted"

    # if recruiter_employer_id:
    #      # Ensure all dependent entities (HR, Jobs as employer, Links as recruiter) are deleted or unlinked
    #     response = client.delete(f"{API_V1_PREFIX}/companies/{recruiter_employer_id}")
    #     assert response.status_code == 200, response.text
    #     print(f"DELETE Recruiter Company: ID {recruiter_employer_id}, response: {response.json()}")
    #     response = client.get(f"{API_V1_PREFIX}/companies/{recruiter_employer_id}")
    #     assert response.status_code == 404, "Recruiter Company not deleted"


    # print("\n=== API Endpoint Tests Completed ===")


if __name__ == "__main__":
    try:
        print("Running API Endpoint Tests...")
        run_api_tests()
        print("\n=== API Endpoint Tests Succeeded! ===")
    except AssertionError as e:
        print(f"\nXXX API ASSERTION FAILED XXX: {e}")
        import traceback
    except Exception as e:
        print(f"\nXXX AN API ERROR OCCURRED XXX: {e}")
        import traceback
    finally:
        print("wowowowow")