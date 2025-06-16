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

-- Step 8: Create schema for RLS
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