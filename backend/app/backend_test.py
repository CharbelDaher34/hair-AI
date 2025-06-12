import os
import uuid
from fastapi.testclient import TestClient
from datetime import datetime  # Import datetime
import base64
import httpx
import json
from core.database import create_db_and_tables
from models.candidate_pydantic import CandidateResume
from faker import Faker
import random
import time

# Import main directly since it's in the same directory
# from main import app  # Direct import from same directory
API_V1_PREFIX = "http://localhost:8017/api/v1"
client = httpx.Client(base_url=API_V1_PREFIX)
# client = TestClient(app)
fake = Faker()

create_db_and_tables(admin=True)
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
        "name": fake.company(),
        "description": fake.catch_phrase(),
        "industry": fake.word(ext_word_list=["Tech", "Finance", "Healthcare", "Education", "Retail"]),
        "is_owner": True,
        "bio": fake.paragraph(nb_sentences=3),
        "website": fake.url(),
        "logo_url": fake.image_url(),
    }
    hr_data_me = {
        "email": "charbeldaher34@gmail.com",
        "password": "a",
        "full_name": "Charbel Daher",
        "role": "hr_manager",
        # employer_id will be added dynamically
    }
    hr_data = {
            "email": fake.unique.email(),
            "password": fake.password(),
            "full_name": fake.name(),
            "role": fake.random_element(elements=("hr_manager", "recruiter", "admin")),
            # employer_id will be added dynamically
        }
    form_key_data = {
        "name": fake.word().capitalize() + "Years",
        "field_type": fake.random_element(elements=("text", "number", "email", "date", "select", "textarea", "checkbox")),
        "required": fake.boolean(),
        "enum_values": [fake.word(), fake.word(), fake.word()],
        # employer_id will be added dynamically
    }
    job_data_payload = {
        "title": fake.job(),
        "description": fake.paragraph(nb_sentences=5),
        "location": fake.city(),
        "department": fake.word().capitalize() + " Department",
        "compensation": {
            "base_salary": fake.random_int(min=50000, max=200000, step=10000),
            "benefits": fake.random_elements(elements=("Health Insurance", "401(k) Matching", "Remote Work", "Paid Time Off", "Stock Options"), length=fake.random_int(min=1, max=5)),
        },
        "experience_level": fake.random_element(elements=("no_experience", "1-3_years", "3-5_years", "5-7_years", "7-10_years", "10_plus_years")),
        "seniority_level": fake.random_element(elements=("entry", "mid", "senior")),
        "status": fake.random_element(elements=("published", "draft")),
        "job_type": fake.random_element(elements=("full_time", "part_time", "contract", "internship")),
        "job_category": fake.random_element(elements=("software_engineering", "data_science", "product_management", "ux_design", "sales", "marketing")),
        "responsibilities": [fake.sentence() for _ in range(3)],
        "skills": {
            "hard_skills": [fake.word() for _ in range(3)],
            "soft_skills": [fake.word() for _ in range(3)],
        },
        "recruited_to_id": None,
    }
    candidate_resume_data = {
        "full_name": fake.name(),
        "email": fake.unique.email(),
        "phone": fake.phone_number(),
        "work_history": [
            {
                "job_title": fake.job(),
                "employer": fake.company(),
                "location": fake.city(),
                "employment_type": fake.random_element(elements=("Full-time", "Part-time", "Contract")),
                "start_date": fake.date_between(start_date="-5y", end_date="-2y").isoformat(),
                "end_date": None,
                "summary": fake.paragraph(nb_sentences=2),
            }
        ],
        "education": [
            {
                "level": fake.random_element(elements=("Bachelor's", "Master's", "PhD")),
                "degree_type": fake.random_element(elements=("Bachelor's", "Master's", "PhD")),
                "subject": fake.word().capitalize() + " Science",
                "start_date": fake.date_between(start_date="-10y", end_date="-6y").isoformat(),
                "end_date": fake.date_between(start_date="-5y", end_date="-2y").isoformat(),
                "institution": f"{fake.company()} University",
                "gpa": round(random.uniform(2.0, 4.0), 1),
                "summary": fake.paragraph(nb_sentences=2),
            }
        ],
        "skills": [
            {"name": fake.word(), "category": fake.word(), "level": fake.random_element(elements=("Beginner", "Intermediate", "Expert"))}
        ],
        "certifications": [
            {
                "certification": fake.catch_phrase(),
                "certification_group": fake.word().capitalize(),
                "issued_by": fake.company(),
                "issue_date": fake.date_between(start_date="-3y", end_date="-1y").isoformat(),
            }
        ],
    }
    candidate_data = {
        "full_name": fake.name(),
        "email": fake.unique.email(),
        "phone": fake.phone_number(),
        "resume_url": fake.url(),
    }
    application_data_payload = {
        "form_responses": {
            "experience_api": fake.random_element(elements=["1-2 years", "3-5 years", "6-10 years", "10+ years"]),
            "status": fake.random_element(elements=("applied", "interviewing", "rejected", "hired", "offered", "on_hold")),
            "extra_field": fake.word(),
        },
        "status": fake.random_element(elements=("pending", "reviewing", "interviewing", "offer_sent",  "rejected")),
        # candidate_id, job_id will be added dynamically
    }
    match_data_payload = {
        "score": round(random.uniform(0.5, 0.99), 2),
        "embedding_similarity": round(random.uniform(0.5, 0.99), 3),
        "match_percentage": fake.random_int(min=30, max=99),
        "matching_skills": [fake.word() for _ in range(fake.random_int(min=1, max=3))],
        "missing_skills": [fake.word() for _ in range(fake.random_int(min=0, max=2))],
        "extra_skills": [fake.word() for _ in range(fake.random_int(min=0, max=1))],
        "total_required_skills": fake.random_int(min=2, max=5),
        "matching_skills_count": fake.random_int(min=1, max=3),
        "missing_skills_count": fake.random_int(min=0, max=2),
        "extra_skills_count": fake.random_int(min=0, max=1),
        "skill_weight": round(random.uniform(0.3, 0.7), 1),
        "embedding_weight": round(random.uniform(0.3, 0.7), 1),
        # application_id will be added dynamically
    }
    company_data_target = {
        "name": fake.company(),
        "description": fake.catch_phrase(),
        "is_owner": False,
        "bio": fake.paragraph(nb_sentences=3),
        "website": fake.url(),
        "logo_url": fake.image_url(),
        "industry": fake.word(ext_word_list=["Recruitment", "Consulting", "HR Tech"]),
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
    assert created_company["is_owner"] == company_data["is_owner"]
    employer_id = created_company["id"]
    print(f"CREATE Company: {created_company['name']} (ID: {employer_id})")

    response = client.get(f"{API_V1_PREFIX}/companies/{employer_id}")
    assert response.status_code == 200, response.text
    retrieved_company = response.json()
    assert retrieved_company["id"] == employer_id
    print(f"READ Company: {retrieved_company['name']}")

    company_update_data = {"description": fake.catch_phrase()}
    response = client.patch(
        f"{API_V1_PREFIX}/companies/{employer_id}", json=company_update_data
    )
    assert response.status_code == 200, response.text
    updated_company_res = response.json()
    assert updated_company_res["description"] == company_update_data["description"]
    print(
        f"UPDATE Company: {updated_company_res['name']}, New Description: {updated_company_res['description']}"
    )

    # Test GET all companies
    response = client.get(f"{API_V1_PREFIX}/companies/")
    assert response.status_code == 200, response.text
    companies_list = response.json()
    assert isinstance(companies_list, list)
    assert any(c["id"] == employer_id for c in companies_list)
    print(f"READ Companies: Found {len(companies_list)} companies.")

    # --- 2. HR ---
    print("\n--- Testing HR API ---")

    hr_create_data = {**hr_data_me, "employer_id": employer_id}
    try:
        response = client.post(f"{API_V1_PREFIX}/auth/register", json=hr_create_data)
        assert response.status_code == 201, f"Failed to create HR: {response.text}"
        
        
    except Exception as e:
        print("Failed to create HR", e)
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

    hr_update_data = {"role": fake.random_element(elements=("ceo", "recruiter", "admin"))}
    response = client.patch(f"{API_V1_PREFIX}/hrs/{hr_id}", json=hr_update_data)
    assert response.status_code == 200, response.text
    updated_hr_res = response.json()
    assert updated_hr_res["role"] == hr_update_data["role"]
    print(f"UPDATE HR: {updated_hr_res['role']}")

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
    print(
        f"CREATE FormKey: {created_form_key['name']} (ID: {form_key_id}) for Company ID: {employer_id}"
    )

    response = client.get(f"{API_V1_PREFIX}/form_keys/{form_key_id}")
    assert response.status_code == 200, response.text
    retrieved_form_key = response.json()
    assert retrieved_form_key["id"] == form_key_id
    print(f"READ FormKey: {retrieved_form_key['name']}")

    form_key_update_data = {"field_type": fake.random_element(elements=("text", "number", "date"))}
    response = client.patch(
        f"{API_V1_PREFIX}/form_keys/{form_key_id}", json=form_key_update_data
    )
    assert response.status_code == 200, response.text
    updated_form_key_res = response.json()
    assert updated_form_key_res["field_type"] == form_key_update_data["field_type"]
    print(
        f"UPDATE FormKey: {updated_form_key_res['name']}, New Field Type: {updated_form_key_res['field_type']}"
    )

    # --- 4. Job ---
    print("\n--- Testing Job API ---")
    job_create_data = {**job_data_payload, "recruited_to_id": employer_id}
    response = client.post(f"{API_V1_PREFIX}/jobs/", json=job_create_data)
    assert response.status_code == 201, f"Failed to create Job: {response.text}"
    created_job = response.json()
    print("GOT HERE")
    assert created_job["title"] == job_data_payload["title"]
    assert created_job["description"] == job_data_payload["description"]
    assert created_job["location"] == job_data_payload["location"]
    assert created_job["department"] == job_data_payload["department"]
    assert created_job["compensation"] == job_data_payload["compensation"]
    assert created_job["experience_level"] == job_data_payload["experience_level"]
    assert created_job["seniority_level"] == job_data_payload["seniority_level"]
    assert created_job["status"] == job_data_payload["status"]
    assert created_job["job_type"] == job_data_payload["job_type"]
    assert created_job["job_category"] == job_data_payload["job_category"]
    assert created_job["responsibilities"] == job_data_payload["responsibilities"]
    assert created_job["skills"] == job_data_payload["skills"]
    job_id = created_job["id"]
    print(
        f"CREATE Job: '{created_job['title']}' (ID: {job_id}) for Company ID: {employer_id}, HR ID: {hr_id}"
    )

    response = client.get(f"{API_V1_PREFIX}/jobs/{job_id}")
    assert response.status_code == 200, response.text
    retrieved_job = response.json()
    assert retrieved_job["id"] == job_id
    print(f"READ Job: '{retrieved_job['title']}'")

    job_update_data = {"status": fake.random_element(elements=("closed", "draft", "published"))}
    response = client.patch(f"{API_V1_PREFIX}/jobs/{job_id}", json=job_update_data)
    assert response.status_code == 200, response.text
    updated_job_res = response.json()
    assert updated_job_res["status"] == job_update_data["status"]
    print(
        f"UPDATE Job: '{updated_job_res['title']}', New Status: {updated_job_res['status']}"
    )

    # --- 5. JobFormKeyConstraint ---
    print("\n--- Testing JobFormKeyConstraint API ---")
    constraint_create_data = {
        "job_id": job_id,
        "form_key_id": form_key_id,
        "constraints": {"min_value": fake.random_int(min=0, max=5)},
    }
    response = client.post(
        f"{API_V1_PREFIX}/job_form_key_constraints/", json=constraint_create_data
    )
    assert response.status_code == 201, (
        f"Failed to create JobFormKeyConstraint: {response.text}"
    )
    created_constraint = response.json()
    assert created_constraint["constraints"]["min_value"] == constraint_create_data["constraints"]["min_value"]
    constraint_id = created_constraint["id"]
    print(
        f"CREATE JobFormKeyConstraint (ID: {constraint_id}) for Job ID: {job_id}, FormKey ID: {form_key_id}"
    )

    response = client.get(f"{API_V1_PREFIX}/job_form_key_constraints/{constraint_id}")
    assert response.status_code == 200, response.text
    retrieved_constraint = response.json()
    assert retrieved_constraint["id"] == constraint_id
    print(f"READ JobFormKeyConstraint: ID {retrieved_constraint['id']}")

    constraint_update_data = {"constraints": {"min_value": fake.random_int(min=0, max=5), "max_value": fake.random_int(min=6, max=10)}}
    response = client.patch(
        f"{API_V1_PREFIX}/job_form_key_constraints/{constraint_id}",
        json=constraint_update_data,
    )
    assert response.status_code == 200, response.text
    updated_constraint_res = response.json()
    assert updated_constraint_res["constraints"]["max_value"] == constraint_update_data["constraints"]["max_value"]
    print(
        f"UPDATE JobFormKeyConstraint: ID {updated_constraint_res['id']}, New Constraints: {updated_constraint_res['constraints']}"
    )

    # --- 6. Candidate ---
    print("\n--- Testing Candidate API ---")
    resume_pdf_path = (
        "/storage/hussein/matching/ai/app/services/llm/Charbel_Daher_Resume.pdf"
    )
    with open(resume_pdf_path, "rb") as resume_file:
        files = {"resume": ("Charbel_Daher_Resume.pdf", resume_file, "application/pdf")}
        data = {"candidate_in": json.dumps(candidate_data)}
        response = client.post(
            f"{API_V1_PREFIX}/candidates/", data=data, files=files, timeout=None
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

    candidate_update_data = {"phone": fake.phone_number(), "email": fake.unique.email()}
    response = client.patch(
        f"{API_V1_PREFIX}/candidates/{candidate_id}", json=candidate_update_data
    )
    assert response.status_code == 200, response.text
    updated_candidate_res = response.json()
    assert updated_candidate_res["phone"] == candidate_update_data["phone"]
    print(
        f"UPDATE Candidate: {updated_candidate_res['full_name']}, New Phone: {updated_candidate_res['phone']}"
    )

    # --- 7. Application ---
    print("\n--- Testing Application API ---")
    application_create_data = {
        **application_data_payload,
        "candidate_id": candidate_id,
        "job_id": job_id,
    }
    response = client.post(
        f"{API_V1_PREFIX}/applications/", json=application_create_data, timeout=None
    )
    assert response.status_code == 201
    created_application = response.json()
    print(created_application)
    assert created_application["candidate_id"] == candidate_id
    application_id = created_application["id"]
    print(
        f"CREATE Application (ID: {application_id}) for Candidate ID: {candidate_id}, Job ID: {job_id}"
    )

    response = client.get(f"{API_V1_PREFIX}/applications/{application_id}")
    assert response.status_code == 200, response.text
    retrieved_application = response.json()
    assert retrieved_application["id"] == application_id
    print(f"READ Application: ID {retrieved_application['id']}")

    application_update_data = {
        "form_responses": {"experience_api": fake.random_element(elements=["1-2 years", "3-5 years", "6-10 years", "10+ years"]), "status": fake.random_element(elements=("applied", "interviewing", "rejected", "hired", "offered", "on_hold"))}
    }
    response = client.patch(
        f"{API_V1_PREFIX}/applications/{application_id}", json=application_update_data
    )
    assert response.status_code == 200, response.text
    updated_application_res = response.json()
    assert updated_application_res["form_responses"]["status"] == application_update_data["form_responses"]["status"]
    print(
        f"UPDATE Application: ID {updated_application_res['id']}, New Form Responses: {updated_application_res['form_responses']}"
    )

    # --- 8. Match ---
    try:
        response = client.get(
            f"{API_V1_PREFIX}/matches/by-application/{application_id}"
        )
        assert response.status_code == 200, response.text
        retrieved_matches = response.json()
        match_id = retrieved_matches[0]["id"]
        print(f"READ Matches: ID {match_id}")

        response = client.patch(
            f"{API_V1_PREFIX}/matches/{match_id}", json=match_data_payload
        )
        assert response.status_code == 200, response.text
        updated_match_res = response.json()
        updated_results = updated_match_res["match_result"]["results"]
        assert isinstance(updated_results[0]["score"], float)
        assert isinstance(updated_results[0]["match_percentage"], int)
        print(
            f"UPDATE Match: ID {updated_match_res['id']}, New Score: {updated_match_res['match_result']['results'][0]['score']}"
        )
    except Exception as e:
        print("No match created for application", application_id)

    # --- 9. RecruiterCompanyLink ---
    print("\n--- Testing RecruiterCompanyLink API ---")
    # Create a second company to be the recruiter (ApiTargetLinkCo)
    response = client.post(f"{API_V1_PREFIX}/companies/", json=company_data_target)
    assert response.status_code == 201, (
        f"Failed to create recruiter company: {response.text}"
    )
    created_recruiter_company = response.json()
    assert created_recruiter_company["name"] == company_data_target["name"]
    assert created_recruiter_company["website"] == company_data_target["website"]
    recruiter_employer_id = created_recruiter_company["id"]
    print(
        f"CREATE Recruiter Company: {created_recruiter_company['name']} (ID: {recruiter_employer_id})"
    )

    # Create HR for the recruiter company
    recruiter_hr_data = {
        **hr_data,
        "email": fake.unique.email(),
        "full_name": fake.name(),
        "employer_id": recruiter_employer_id,
    }
    response = client.post(f"{API_V1_PREFIX}/auth/register", json=recruiter_hr_data)
    assert response.status_code == 201, (
        f"Failed to create recruiter HR: {response.text}"
    )
    print(f"CREATE Recruiter HR.")

    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    response = client.get(f"{API_V1_PREFIX}/hrs/")
    assert response.status_code == 200, response.text
    retrieved_hr = response.json()

    recruiter_hr_id = retrieved_hr["id"]
    print(f"READ HR: {retrieved_hr['full_name']}")

    # Create link where ApiTargetLinkCo is the recruiter and ApiTestCo is the target
    link_create_data = {
        "recruiter_id": recruiter_employer_id,
        "target_employer_id": employer_id,
    }
    response = client.post(
        f"{API_V1_PREFIX}/recruiter_company_links/", json=link_create_data
    )
    assert response.status_code == 201, (
        f"Failed to create RecruiterCompanyLink: {response.text}"
    )
    created_link = response.json()
    assert created_link["target_employer_id"] == employer_id
    link_id = created_link["id"]
    print(
        f"CREATE RecruiterCompanyLink (ID: {link_id}) from Recruiter {recruiter_employer_id} to Target {employer_id}"
    )

    response = client.get(f"{API_V1_PREFIX}/recruiter_company_links/{link_id}")
    assert response.status_code == 200, response.text
    retrieved_link = response.json()
    assert retrieved_link["id"] == link_id
    print(f"READ RecruiterCompanyLink: ID {retrieved_link['id']}")

    print(
        "UPDATE RecruiterCompanyLink: Skipped (no updatable fields in current model/schema or not implemented)"
    )

    # Create a job through the recruiter for the target company
    recruiter_job_data_payload = {
        "title": fake.job(),
        "description": fake.paragraph(nb_sentences=5),
        "location": fake.city(),
        "department": fake.word().capitalize() + " Department",
        "compensation": {
            "base_salary": fake.random_int(min=70000, max=250000, step=10000),
            "benefits": fake.random_elements(elements=("Health Insurance", "401(k) Matching", "Remote Work", "Paid Time Off", "Stock Options", "Gym Membership"), length=fake.random_int(min=1, max=6)),
        },
        "experience_level": fake.random_element(elements=("3-5_years", "5-7_years", "7-10_years", "10_plus_years")),
        "seniority_level": fake.random_element(elements=("mid", "senior", "entry")),
        "status": fake.random_element(elements=("published", "draft", "closed")),
        "job_type": fake.random_element(elements=("full_time", "contract")),
        "job_category": fake.random_element(elements=("software_engineering", "data_science", "product_management", "sales")),
        "responsibilities": [fake.sentence() for _ in range(4)],
        "skills": {
            "hard_skills": [fake.word() for _ in range(4)],
            "soft_skills": [fake.word() for _ in range(4)],
        },
        "recruited_to_id": employer_id,
    }

    recruiter_job_create_data = {
        **recruiter_job_data_payload,
    }
    response = client.post(f"{API_V1_PREFIX}/jobs/", json=recruiter_job_create_data)
    assert response.status_code == 201, (
        f"Failed to create recruited job: {response.text}"
    )
    created_recruiter_job = response.json()
    created_recruiter_job_id = created_recruiter_job["id"]
    assert created_recruiter_job["title"] == recruiter_job_data_payload["title"]
    assert (
        created_recruiter_job["description"]
        == recruiter_job_data_payload["description"]
    )
    assert created_recruiter_job["location"] == recruiter_job_data_payload["location"]
    assert (
        created_recruiter_job["compensation"]
        == recruiter_job_data_payload["compensation"]
    )
    assert (
        created_recruiter_job["experience_level"]
        == recruiter_job_data_payload["experience_level"]
    )
    assert (
        created_recruiter_job["seniority_level"]
        == recruiter_job_data_payload["seniority_level"]
    )
    assert created_recruiter_job["status"] == recruiter_job_data_payload["status"]
    assert created_recruiter_job["job_type"] == recruiter_job_data_payload["job_type"]
    assert (
        created_recruiter_job["job_category"]
        == recruiter_job_data_payload["job_category"]
    )
    assert (
        created_recruiter_job["responsibilities"]
        == recruiter_job_data_payload["responsibilities"]
    )
    assert created_recruiter_job["skills"] == recruiter_job_data_payload["skills"]
    print(
        f"CREATE Recruited Job: '{created_recruiter_job['title']}' (ID: {created_recruiter_job_id}) for Target Company ID: {employer_id}"
    )

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
