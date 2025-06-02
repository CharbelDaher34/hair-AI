# Resume Parser & Application Matcher Batch Scripts

This directory contains scripts that process data in the database in batch mode. These scripts can be run manually via script execution or triggered via API endpoints.

## Scripts Available

### 1. Resume Parser Batch Script
Processes all candidates in the database that don't have parsed resume data.

### 2. Application Matcher Batch Script  
Processes all applications in the database that don't have matches and creates matches using the AI matching service.

## Features

- ✅ **Batch Processing**: Processes all records without required data
- ✅ **API Integration**: Can be triggered via FastAPI endpoints
- ✅ **Retry Logic**: Automatically retries failed processing attempts
- ✅ **Data Validation**: Checks if required data exists before processing
- ✅ **Progress Tracking**: Shows detailed progress and results
- ✅ **Error Handling**: Graceful error handling with detailed logging

## Usage

### Option 1: Via API Endpoints (Recommended)

#### Resume Parsing

**Start Batch Resume Parsing**
```bash
curl -X POST "http://localhost:8017/api/v1/admin/scripts/batch-parse-resumes"
```

**Check Resume Parsing Status**
```bash
curl -X GET "http://localhost:8017/api/v1/admin/scripts/batch-parse-resumes/status"
```

#### Application Matching

**Start Batch Application Matching**
```bash
curl -X POST "http://localhost:8017/api/v1/admin/scripts/batch-match-applications"
```

**Check Application Matching Status**
```bash
curl -X GET "http://localhost:8017/api/v1/admin/scripts/batch-match-applications/status"
```

### Option 2: Direct Script Execution

#### Resume Parsing
```bash
cd backend/app/scripts
python3 resume_parser_batch.py
```

#### Application Matching
```bash
cd backend/app/scripts
python3 application_matcher_batch.py
```

## API Endpoints

### Resume Parsing Endpoints

#### POST `/api/v1/admin/scripts/batch-parse-resumes`
- **Description**: Starts batch resume parsing in the background
- **Response**: Immediate confirmation that processing has started
- **Background**: Processes all candidates without parsed resumes

#### GET `/api/v1/admin/scripts/batch-parse-resumes/status`
- **Description**: Check how many candidates need resume parsing
- **Response**: 
  ```json
  {
    "candidates_needing_parsing": 5,
    "status": "ready"
  }
  ```

### Application Matching Endpoints

#### POST `/api/v1/admin/scripts/batch-match-applications`
- **Description**: Starts batch application matching in the background
- **Response**: Immediate confirmation that processing has started
- **Background**: Processes all applications without matches

#### GET `/api/v1/admin/scripts/batch-match-applications/status`
- **Description**: Check how many applications need matching
- **Response**: 
  ```json
  {
    "applications_needing_matching": 12,
    "status": "ready"
  }
  ```

## How It Works

### Resume Parser Script

#### 1. **Candidate Selection**
The script queries the database for candidates that:
- Have `parsed_resume` field that is `None` or empty (`{}`)
- Have a `resume_url` (indicating a resume was uploaded)
- Have an actual resume file on disk

#### 2. **Processing Flow**
For each candidate:
1. **File Check**: Verifies the resume file exists
2. **AI Parsing**: Sends the PDF to the AI parsing service
3. **Retry Logic**: Retries up to 3 times if parsing fails
4. **Database Update**: Updates the `parsed_resume` field with results
5. **Progress Logging**: Shows detailed progress and results

### Application Matcher Script

#### 1. **Application Selection**
The script queries the database for applications that:
- Don't have any associated matches in the `Match` table
- Have candidates with parsed resume data
- Have jobs with descriptions

#### 2. **Processing Flow**
For each application:
1. **Data Validation**: Verifies candidate has parsed resume and job has description
2. **AI Matching**: Calls the matching service via CRUD function
3. **Retry Logic**: Retries up to 3 times if matching fails
4. **Database Update**: Creates a new match record with results
5. **Progress Logging**: Shows detailed progress and results

### 3. **Background Processing**
When triggered via API:
- Runs in FastAPI background tasks
- Returns immediately to the caller
- Processes records asynchronously
- Logs progress to server console

## Example Output

### Resume Parser
```
[Batch] Starting batch resume parsing at 2024-01-15 14:30:00
[Batch] Found 5 candidates that need resume parsing

[Batch] Processing candidate 1/5: John Doe (ID: 123)
[Batch] ✅ Successfully processed candidate 123

[Batch] Batch processing completed at 2024-01-15 14:32:15
[Batch] Results: 4 successful, 1 failed
```

### Application Matcher
```
[Matcher] Starting batch application matching at 2024-01-15 15:00:00
[Matcher] Found 12 applications that need matching

[Matcher] Processing application 1/12: ID 456
[Matcher] Job: Senior Python Developer
[Matcher] Candidate: Jane Smith
[Matcher] ✅ Successfully processed application 456

[Matcher] Batch matching completed at 2024-01-15 15:05:30
[Matcher] Results: 11 successful, 1 failed
```

## Configuration

### Environment Variables
The scripts use the same configuration as your main application:
- `RESUME_STORAGE_DIR`: Directory where resume files are stored
- Database connection settings from your `.env` file
- Matching service URL: `http://localhost:8011/matcher/match_candidates`

## Scheduling with Cron (Optional)

If you want to schedule the scripts to run automatically:

```bash
# Edit crontab
crontab -e

# Resume parsing daily at 2:30 PM
30 14 * * * cd /path/to/backend/app/scripts && python3 resume_parser_batch.py

# Application matching daily at 3:00 PM  
0 15 * * * cd /path/to/backend/app/scripts && python3 application_matcher_batch.py

# Both scripts multiple times daily
0 9,15,21 * * * cd /path/to/backend/app/scripts && python3 resume_parser_batch.py
30 9,15,21 * * * cd /path/to/backend/app/scripts && python3 application_matcher_batch.py
```

## Monitoring

### API Monitoring
Check the status via API:
```bash
# Check resume parsing status
curl -X GET "http://localhost:8017/api/v1/admin/scripts/batch-parse-resumes/status"

# Check application matching status
curl -X GET "http://localhost:8017/api/v1/admin/scripts/batch-match-applications/status"

# Trigger both processes
curl -X POST "http://localhost:8017/api/v1/admin/scripts/batch-parse-resumes"
curl -X POST "http://localhost:8017/api/v1/admin/scripts/batch-match-applications"
```

### Log Files
When running via script, you can redirect logs to a file:
```bash
python3 resume_parser_batch.py > resume_parser.log 2>&1
python3 application_matcher_batch.py > application_matcher.log 2>&1
```

### Database Monitoring
Check processing status in your application:

**Resume Parsing Status:**
```sql
-- Count candidates without parsed resumes
SELECT COUNT(*) FROM candidate 
WHERE (parsed_resume IS NULL OR parsed_resume::text = '{}' OR parsed_resume::text = 'null') 
AND resume_url IS NOT NULL;
```

**Application Matching Status:**
```sql
-- Count applications without matches
SELECT COUNT(*) FROM application a
LEFT JOIN match m ON a.id = m.application_id
WHERE m.id IS NULL;

-- Check recent matching activity
SELECT a.id, c.full_name, j.title, 
       CASE WHEN m.id IS NOT NULL THEN 'Matched' ELSE 'Not Matched' END as status
FROM application a
JOIN candidate c ON a.candidate_id = c.id
JOIN job j ON a.job_id = j.id
LEFT JOIN match m ON a.id = m.application_id
ORDER BY a.created_at DESC;
```

## Troubleshooting

### Common Issues

1. **"No candidates/applications to process"**
   - All records already have required data
   - No records meet the criteria

2. **"Resume file not found"**
   - Resume files may have been moved or deleted
   - Check `RESUME_STORAGE_DIR` configuration

3. **"No parsed resume data"**
   - Run resume parsing first before application matching
   - Check if resume parsing completed successfully

4. **"API may have failed"**
   - AI services are down or slow
   - Check if services are accessible:
     - Resume parser: `http://localhost:8011/parser/parse`
     - Matcher: `http://localhost:8011/matcher/match_candidates`

5. **Permission errors**
   - Ensure scripts have read access to resume files
   - Check database connection permissions

### Debug Mode
Check the FastAPI server logs when running via API endpoints for detailed debugging information.

## Integration with Main Application

Both batch scripts are fully integrated with your FastAPI application:
- **Shared Database**: Uses the same database and models
- **Shared File Storage**: Uses the same resume storage directory
- **Shared AI Services**: Uses the same parsing and matching services
- **API Endpoints**: Can be triggered via HTTP requests
- **Background Processing**: Runs asynchronously without blocking the API

This ensures consistency and allows you to process historical data without affecting real-time operations. 