#!/usr/bin/env python3
"""
Company Data Population Script using Faker and API endpoints
Populates the database with realistic company data via API calls.
"""

import os
import sys
from typing import List, Dict, Optional
from faker import Faker
from faker.providers import company, internet, person, lorem, date_time
import random
import requests
import json
from datetime import datetime, timedelta

# Initialize Faker
fake = Faker()
fake.add_provider(company)
fake.add_provider(internet)
fake.add_provider(person)
fake.add_provider(lorem)
fake.add_provider(date_time)

# API Configuration
API_BASE_URL = "http://localhost:8017/api/v1"  # Adjust this to your API URL
HEADERS = {"Content-Type": "application/json"}

# PDF file path for candidates (same as in backend_test.py)
CANDIDATE_PDF_PATH = (
    "/storage/hussein/matching/ai/app/services/llm/Charbel_Daher_Resume.pdf"
)

# Industry categories for realistic company data
INDUSTRIES = [
    "Technology",
    "Healthcare",
    "Finance",
    "Education",
    "Manufacturing",
    "Retail",
    "Consulting",
    "Media",
    "Transportation",
    "Energy",
    "Real Estate",
    "Hospitality",
    "Agriculture",
    "Construction",
    "Telecommunications",
]

# HR roles
HR_ROLES = [
    "HR Manager",
    "Talent Acquisition Specialist",
    "HR Director",
    "Recruiter",
    "HR Business Partner",
    "People Operations Manager",
    "Talent Manager",
    "HR Coordinator",
    "Chief People Officer",
]

# Form field types for company forms
FORM_FIELD_NAMES = [
    "Years of Experience",
    "Education Level",
    "Preferred Location",
    "Salary Expectation",
    "Notice Period",
    "Availability",
    "Portfolio URL",
    "LinkedIn Profile",
    "GitHub Profile",
    "Certifications",
    "Languages Spoken",
    "Visa Status",
]

FIELD_TYPES = ["text", "number", "email", "date", "select", "textarea", "checkbox"]

# Job categories and types
JOB_CATEGORIES = [
    "software_engineering",
    "data_science",
    "product_management",
    "ux_design",
    "sales",
    "marketing",
    "finance",
    "operations",
]

JOB_TYPES = ["full_time", "part_time", "contract", "internship"]
EXPERIENCE_LEVELS = [
    "no_experience",
    "1-3_years",
    "3-5_years",
    "5-7_years",
    "7-10_years",
    "10_plus_years",
]
SENIORITY_LEVELS = ["entry", "mid", "senior"]
JOB_STATUSES = ["draft", "published"]

# Application statuses
APPLICATION_STATUSES = [
    "pending",
    "reviewing",
    "interviewing",
    "offer_sent",
    "rejected",
]


def create_company_data() -> Dict:
    """Create realistic company data for API call."""
    company_name = fake.company()

    # Generate a realistic domain based on company name
    domain_base = (
        company_name.lower().replace(" ", "").replace(",", "").replace(".", "")[:10]
    )
    domain = f"@{domain_base}.com"

    # Create company bio and description
    description = fake.text(max_nb_chars=200)
    bio = fake.text(max_nb_chars=150)

    # Generate website URL
    website = f"https://www.{domain_base}.com"

    # Generate logo URL (placeholder)
    logo_url = f"https://logo.clearbit.com/{domain_base}.com"

    company_data = {
        "name": company_name,
        "description": description,
        "industry": random.choice(INDUSTRIES),
        "bio": bio,
        "website": website,
        "logo_url": logo_url,
        "is_owner": random.choice([True, False]),
        "domain": domain,
    }

    return company_data


def create_hr_data(company_id: int) -> Dict:
    """Create HR user data for API call."""
    full_name = fake.name()
    email = fake.email()

    # Generate a simple password
    password = fake.password(
        length=12, special_chars=True, digits=True, upper_case=True, lower_case=True
    )

    hr_data = {
        "email": "charbeldaher34@gmail.com",
        "password": "a",
        "full_name": full_name,
        "employer_id": company_id,
        "role": random.choice(HR_ROLES),
    }

    return hr_data


def create_form_key_data() -> Dict:
    """Create form key data for API call."""
    field_name = random.choice(FORM_FIELD_NAMES)
    field_type = random.choice(FIELD_TYPES)

    # Generate enum values for SELECT fields
    enum_values = None
    if field_type == "select":
        if "Experience" in field_name:
            enum_values = [
                "0-1 years",
                "1-3 years",
                "3-5 years",
                "5-10 years",
                "10+ years",
            ]
        elif "Education" in field_name:
            enum_values = ["High School", "Bachelor's", "Master's", "PhD", "Other"]
        elif "Location" in field_name:
            enum_values = ["Remote", "On-site", "Hybrid", "Flexible"]
        else:
            enum_values = [fake.word() for _ in range(3, 6)]

    form_key_data = {
        "name": field_name,
        "enum_values": enum_values,
        "required": random.choice([True, False]),
        "field_type": field_type,
    }

    return form_key_data


def create_job_data() -> Dict:
    """Create job data for API call."""
    job_data = {
        "title": fake.job(),
        "description": fake.paragraph(nb_sentences=5),
        "location": fake.city(),
        "department": fake.word().capitalize() + " Department",
        "compensation": {
            "base_salary": fake.random_int(min=50000, max=200000, step=10000),
            "benefits": fake.random_elements(
                elements=[
                    "Health Insurance",
                    "401(k) Matching",
                    "Remote Work",
                    "Paid Time Off",
                    "Stock Options",
                    "Gym Membership",
                    "Professional Development",
                    "Flexible Hours",
                ],
                length=fake.random_int(min=2, max=5),
                unique=True,
            ),
        },
        "experience_level": random.choice(EXPERIENCE_LEVELS),
        "seniority_level": random.choice(SENIORITY_LEVELS),
        "status": random.choice(JOB_STATUSES),
        "job_type": random.choice(JOB_TYPES),
        "job_category": random.choice(JOB_CATEGORIES),
        "responsibilities": [fake.sentence() for _ in range(3, 6)],
        "skills": {
            "hard_skills": [fake.word() for _ in range(3, 7)],
            "soft_skills": [fake.word() for _ in range(2, 5)],
        },
        "recruited_to_id": None,
    }

    return job_data


def create_candidate_data() -> Dict:
    """Create candidate data for API call."""
    candidate_data = {
        "full_name": fake.name(),
        "email": fake.unique.email(),
        "phone": fake.phone_number(),
        "resume_url": fake.url(),
    }

    return candidate_data


def create_application_data(candidate_id: int, job_id: int) -> Dict:
    """Create application data for API call."""
    application_data = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "form_responses": {
            "experience_years": fake.random_element(
                elements=["1-2 years", "3-5 years", "6-10 years", "10+ years"]
            ),
            "availability": fake.random_element(
                elements=["Immediate", "2 weeks", "1 month", "Flexible"]
            ),
            "salary_expectation": fake.random_int(min=40000, max=180000, step=5000),
            "remote_preference": fake.random_element(
                elements=["Remote", "On-site", "Hybrid", "No preference"]
            ),
        },
        "status": random.choice(APPLICATION_STATUSES),
    }

    return application_data


def create_company_via_api(company_data: Dict) -> Optional[Dict]:
    """Create a company via API call."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/companies/", headers=HEADERS, json=company_data
        )

        if response.status_code == 201:
            return response.json()
        else:
            print(
                f"Error creating company {company_data['name']}: {response.status_code} - {response.text}"
            )
            return None

    except Exception as e:
        print(f"Exception creating company {company_data['name']}: {e}")
        return None


def create_hr_via_api(hr_data: Dict) -> Optional[Dict]:
    """Create an HR user via API call."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register", headers=HEADERS, json=hr_data
        )

        if response.status_code == 201:
            return response.json()
        else:
            print(
                f"Error creating HR user {hr_data['email']}: {response.status_code} - {response.text}"
            )
            return None

    except Exception as e:
        print(f"Exception creating HR user {hr_data['email']}: {e}")
        return None


def create_form_key_via_api(form_key_data: Dict, auth_token: str) -> Optional[Dict]:
    """Create a form key via API call."""
    try:
        headers_with_auth = {**HEADERS, "Authorization": f"Bearer {auth_token}"}

        response = requests.post(
            f"{API_BASE_URL}/form_keys/", headers=headers_with_auth, json=form_key_data
        )

        if response.status_code == 201:
            return response.json()
        else:
            print(
                f"Error creating form key {form_key_data['name']}: {response.status_code} - {response.text}"
            )
            return None

    except Exception as e:
        print(f"Exception creating form key {form_key_data['name']}: {e}")
        return None


def create_job_via_api(job_data: Dict, auth_token: str) -> Optional[Dict]:
    """Create a job via API call."""
    try:
        headers_with_auth = {**HEADERS, "Authorization": f"Bearer {auth_token}"}

        response = requests.post(
            f"{API_BASE_URL}/jobs/", headers=headers_with_auth, json=job_data
        )

        if response.status_code == 201:
            return response.json()
        else:
            print(
                f"Error creating job {job_data['title']}: {response.status_code} - {response.text}"
            )
            return None

    except Exception as e:
        print(f"Exception creating job {job_data['title']}: {e}")
        return None


def create_candidate_via_api(candidate_data: Dict, auth_token: str) -> Optional[Dict]:
    """Create a candidate via API call with PDF upload."""
    try:
        headers_with_auth = {"Authorization": f"Bearer {auth_token}"}

        # Check if PDF file exists
        if not os.path.exists(CANDIDATE_PDF_PATH):
            print(
                f"Warning: PDF file not found at {CANDIDATE_PDF_PATH}, creating candidate without resume"
            )
            response = requests.post(
                f"{API_BASE_URL}/candidates/",
                headers={**HEADERS, **headers_with_auth},
                json=candidate_data,
            )
        else:
            # Upload with PDF file
            with open(CANDIDATE_PDF_PATH, "rb") as resume_file:
                files = {
                    "resume": (
                        "Charbel_Daher_Resume.pdf",
                        resume_file,
                        "application/pdf",
                    )
                }
                data = {"candidate_in": json.dumps(candidate_data)}
                response = requests.post(
                    f"{API_BASE_URL}/candidates/",
                    headers=headers_with_auth,
                    data=data,
                    files=files,
                    timeout=30,
                )

        if response.status_code == 201:
            return response.json()
        else:
            print(
                f"Error creating candidate {candidate_data['full_name']}: {response.status_code} - {response.text}"
            )
            return None

    except Exception as e:
        print(f"Exception creating candidate {candidate_data['full_name']}: {e}")
        return None


def create_application_via_api(
    application_data: Dict, auth_token: str
) -> Optional[Dict]:
    """Create an application via API call."""
    try:
        headers_with_auth = {**HEADERS, "Authorization": f"Bearer {auth_token}"}

        response = requests.post(
            f"{API_BASE_URL}/applications/",
            headers=headers_with_auth,
            json=application_data,
            timeout=30,
        )

        if response.status_code == 201:
            return response.json()
        else:
            print(
                f"Error creating application: {response.status_code} - {response.text}"
            )
            return None

    except Exception as e:
        print(f"Exception creating application: {e}")
        return None


def get_existing_companies() -> List[Dict]:
    """Get existing companies via API."""
    try:
        response = requests.get(f"{API_BASE_URL}/companies/")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching companies: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception fetching companies: {e}")
        return []


def populate_companies_via_api(num_companies: int = 20) -> List[Dict]:
    """Populate companies via API calls."""
    companies = []

    print(f"Creating {num_companies} companies via API...")

    for i in range(num_companies):
        company_data = create_company_data()
        company = create_company_via_api(company_data)

        if company:
            companies.append(company)
            print(f"✓ Created company: {company['name']} (ID: {company['id']})")
        else:
            print(f"✗ Failed to create company: {company_data['name']}")

        if (i + 1) % 5 == 0:
            print(f"Progress: {i + 1}/{num_companies} companies created...")

    print(f"Successfully created {len(companies)} companies!")
    return companies


def populate_hr_users_via_api(
    companies: List[Dict], hr_per_company: int = 2
) -> List[Dict]:
    """Populate HR users via API calls."""
    hr_users = []
    auth_tokens = {}  # Store auth tokens for each company

    print(f"Creating HR users for companies via API...")

    for company in companies:
        company_id = company["id"]
        company_name = company["name"]

        # Create 1-3 HR users per company
        num_hr = random.randint(1, hr_per_company)

        for j in range(num_hr):
            hr_data = create_hr_data(company_id)
            hr_result = create_hr_via_api(hr_data)

            if hr_result:
                hr_users.append(
                    {
                        "company_id": company_id,
                        "company_name": company_name,
                        "email": hr_data["email"],
                        "full_name": hr_data["full_name"],
                        "role": hr_data["role"],
                    }
                )

                # Store the first HR user's token for creating form keys
                if company_id not in auth_tokens:
                    auth_tokens[company_id] = hr_result.get("access_token")

                print(f"✓ Created HR user: {hr_data['full_name']} for {company_name}")
            else:
                print(f"✗ Failed to create HR user for {company_name}")

    print(f"Successfully created {len(hr_users)} HR users!")
    return hr_users, auth_tokens


def populate_form_keys_via_api(
    companies: List[Dict], auth_tokens: Dict, keys_per_company: int = 5
) -> List[Dict]:
    """Populate form keys via API calls."""
    form_keys = []

    print(f"Creating form keys for companies via API...")

    for company in companies:
        company_id = company["id"]
        company_name = company["name"]

        # Skip if no auth token available for this company
        if company_id not in auth_tokens:
            print(f"⚠ No auth token available for {company_name}, skipping form keys")
            continue

        auth_token = auth_tokens[company_id]

        # Create 3-7 form keys per company
        num_keys = random.randint(3, keys_per_company)
        used_names = set()

        for _ in range(num_keys):
            # Avoid duplicate field names for the same company
            attempts = 0
            while attempts < 10:
                form_key_data = create_form_key_data()
                if form_key_data["name"] not in used_names:
                    used_names.add(form_key_data["name"])

                    form_key = create_form_key_via_api(form_key_data, auth_token)
                    if form_key:
                        form_keys.append(
                            {
                                "company_id": company_id,
                                "company_name": company_name,
                                "name": form_key_data["name"],
                                "field_type": form_key_data["field_type"],
                            }
                        )
                        print(
                            f"✓ Created form key: {form_key_data['name']} for {company_name}"
                        )
                    else:
                        print(
                            f"✗ Failed to create form key: {form_key_data['name']} for {company_name}"
                        )
                    break
                attempts += 1

    print(f"Successfully created {len(form_keys)} form keys!")
    return form_keys


def populate_jobs_via_api(
    companies: List[Dict], auth_tokens: Dict, jobs_per_company: int = 3
) -> List[Dict]:
    """Populate jobs via API calls."""
    jobs = []

    print(f"Creating jobs for companies via API...")

    for company in companies:
        company_id = company["id"]
        company_name = company["name"]

        # Skip if no auth token available for this company
        if company_id not in auth_tokens:
            print(f"⚠ No auth token available for {company_name}, skipping jobs")
            continue

        auth_token = auth_tokens[company_id]

        # Create 1-5 jobs per company
        num_jobs = random.randint(1, jobs_per_company)

        for _ in range(num_jobs):
            job_data = create_job_data()
            job = create_job_via_api(job_data, auth_token)

            if job:
                jobs.append(
                    {
                        "id": job["id"],
                        "company_id": company_id,
                        "company_name": company_name,
                        "title": job["title"],
                        "status": job["status"],
                        "job_type": job["job_type"],
                    }
                )
                print(f"✓ Created job: {job['title']} for {company_name}")
            else:
                print(f"✗ Failed to create job for {company_name}")

    print(f"Successfully created {len(jobs)} jobs!")
    return jobs


def populate_candidates_via_api(
    companies: List[Dict], auth_tokens: Dict, candidates_per_company: int = 5
) -> List[Dict]:
    """Populate candidates via API calls."""
    candidates = []

    print(f"Creating candidates via API...")

    for company in companies:
        company_id = company["id"]
        company_name = company["name"]

        # Skip if no auth token available for this company
        if company_id not in auth_tokens:
            print(f"⚠ No auth token available for {company_name}, skipping candidates")
            continue

        auth_token = auth_tokens[company_id]

        # Create 3-8 candidates per company
        num_candidates = random.randint(3, candidates_per_company)

        for _ in range(num_candidates):
            candidate_data = create_candidate_data()
            candidate = create_candidate_via_api(candidate_data, auth_token)

            if candidate:
                candidates.append(
                    {
                        "id": candidate["id"],
                        "company_id": company_id,
                        "company_name": company_name,
                        "full_name": candidate["full_name"],
                        "email": candidate["email"],
                    }
                )
                print(
                    f"✓ Created candidate: {candidate['full_name']} for {company_name}"
                )
            else:
                print(f"✗ Failed to create candidate for {company_name}")

    print(f"Successfully created {len(candidates)} candidates!")
    return candidates


def populate_applications_via_api(
    jobs: List[Dict],
    candidates: List[Dict],
    auth_tokens: Dict,
    applications_per_job: int = 3,
) -> List[Dict]:
    """Populate applications via API calls."""
    applications = []

    print(f"Creating applications via API...")

    for job in jobs:
        job_id = job["id"]
        company_id = job["company_id"]
        company_name = job["company_name"]
        job_title = job["title"]

        # Skip if no auth token available for this company
        if company_id not in auth_tokens:
            print(
                f"⚠ No auth token available for {company_name}, skipping applications"
            )
            continue

        auth_token = auth_tokens[company_id]

        # Get candidates for this company
        company_candidates = [c for c in candidates if c["company_id"] == company_id]

        if not company_candidates:
            print(
                f"⚠ No candidates available for {company_name}, skipping applications for job {job_title}"
            )
            continue

        # Create 1-5 applications per job
        num_applications = min(
            random.randint(1, applications_per_job), len(company_candidates)
        )
        selected_candidates = random.sample(company_candidates, num_applications)

        for candidate in selected_candidates:
            application_data = create_application_data(candidate["id"], job_id)
            application = create_application_via_api(application_data, auth_token)

            if application:
                applications.append(
                    {
                        "id": application["id"],
                        "job_id": job_id,
                        "candidate_id": candidate["id"],
                        "company_name": company_name,
                        "job_title": job_title,
                        "candidate_name": candidate["full_name"],
                        "status": application["status"],
                    }
                )
                print(
                    f"✓ Created application: {candidate['full_name']} -> {job_title} ({company_name})"
                )
            else:
                print(
                    f"✗ Failed to create application: {candidate['full_name']} -> {job_title}"
                )

    print(f"Successfully created {len(applications)} applications!")
    return applications


def main():
    """Main function to populate company data via API."""
    print("Starting company data population via API...")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"PDF Path: {CANDIDATE_PDF_PATH}")

    try:
        # Check if companies already exist
        existing_companies = get_existing_companies()
        if existing_companies:
            print(f"Found {len(existing_companies)} existing companies.")
            response = input("Do you want to add more companies? (y/n): ")
            if response.lower() != "y":
                print("Exiting...")
                return

        # Get user input for number of entities
        try:
            num_companies = 1
            hr_per_company = 1
            keys_per_company = int(
                input("Enter max form keys per company (default 3): ") or "3"
            )
            jobs_per_company = int(
                input("Enter max jobs per company (default 3): ") or "3"
            )
            candidates_per_company = int(
                input("Enter max candidates per company (default 4): ") or "4"
            )
            applications_per_job = int(
                input("Enter max applications per job (default 2): ") or "2"
            )
        except ValueError:
            print("Invalid input. Using default values.")
            num_companies = 5
            hr_per_company = 2
            keys_per_company = 3
            jobs_per_company = 3
            candidates_per_company = 4
            applications_per_job = 2

        # Populate companies
        companies = populate_companies_via_api(num_companies)

        if not companies:
            print("No companies were created. Exiting...")
            return

        # Populate HR users
        hr_users, auth_tokens = populate_hr_users_via_api(companies, hr_per_company)

        # Populate form keys
        form_keys = populate_form_keys_via_api(companies, auth_tokens, keys_per_company)

        # Populate jobs
        jobs = populate_jobs_via_api(companies, auth_tokens, jobs_per_company)

        # Populate candidates
        candidates = populate_candidates_via_api(
            companies, auth_tokens, candidates_per_company
        )

        # Populate applications
        applications = populate_applications_via_api(
            jobs, candidates, auth_tokens, applications_per_job
        )

        print("\n" + "=" * 70)
        print("POPULATION SUMMARY")
        print("=" * 70)
        print(f"Companies created: {len(companies)}")
        print(f"HR users created: {len(hr_users)}")
        print(f"Form keys created: {len(form_keys)}")
        print(f"Jobs created: {len(jobs)}")
        print(f"Candidates created: {len(candidates)}")
        print(f"Applications created: {len(applications)}")
        print("=" * 70)

        # Display sample data
        if companies:
            sample_company = companies[0]
            print(f"\nSample company: {sample_company['name']}")
            print(f"Industry: {sample_company['industry']}")
            print(f"Website: {sample_company['website']}")
            print(f"Company ID: {sample_company['id']}")

        if jobs:
            sample_job = jobs[0]
            print(f"\nSample job: {sample_job['title']}")
            print(f"Company: {sample_job['company_name']}")
            print(f"Status: {sample_job['status']}")
            print(f"Type: {sample_job['job_type']}")

        if candidates:
            sample_candidate = candidates[0]
            print(f"\nSample candidate: {sample_candidate['full_name']}")
            print(f"Email: {sample_candidate['email']}")
            print(f"Company: {sample_candidate['company_name']}")

        if applications:
            sample_application = applications[0]
            print(f"\nSample application: {sample_application['candidate_name']}")
            print(f"Job: {sample_application['job_title']}")
            print(f"Company: {sample_application['company_name']}")
            print(f"Status: {sample_application['status']}")

        print("\nData population completed successfully!")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error during population: {e}")
        raise


if __name__ == "__main__":
    main()
