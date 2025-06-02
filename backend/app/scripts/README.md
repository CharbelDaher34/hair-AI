# Resume Parser Batch Script

This script processes all candidates in the database that don't have parsed resume data. It can be run manually via script or triggered via API endpoints.

## Features

- ✅ **Batch Processing**: Processes all candidates without parsed resumes
- ✅ **API Integration**: Can be triggered via FastAPI endpoints
- ✅ **Retry Logic**: Automatically retries failed parsing attempts
- ✅ **File Validation**: Checks if resume files exist before processing
- ✅ **Progress Tracking**: Shows detailed progress and results
- ✅ **Error Handling**: Graceful error handling with detailed logging

## Usage

### Option 1: Via API Endpoints (Recommended)

#### Start Batch Processing
```bash
curl -X POST "http://localhost:8017/api/v1/admin/batch-parse-resumes"
```

#### Check Status
```bash
curl -X GET "http://localhost:8017/api/v1/admin/batch-parse-resumes/status"
```

### Option 2: Direct Script Execution

#### Run Once (Manual)
```bash
cd backend/app/scripts
python3 resume_parser_batch.py
```

## API Endpoints

### POST `/api/v1/admin/batch-parse-resumes`
- **Description**: Starts batch processing in the background
- **Response**: Immediate confirmation that processing has started
- **Background**: Processes all candidates without parsed resumes

### GET `/api/v1/admin/batch-parse-resumes/status`
- **Description**: Check how many candidates need parsing
- **Response**: 
  ```json
  {
    "candidates_needing_parsing": 5,
    "status": "ready"
  }
  ```

## How It Works

### 1. **Candidate Selection**
The script queries the database for candidates that:
- Have `parsed_resume` field that is `None` or empty (`{}`)
- Have a `resume_url` (indicating a resume was uploaded)
- Have an actual resume file on disk

### 2. **Processing Flow**
For each candidate:
1. **File Check**: Verifies the resume file exists
2. **AI Parsing**: Sends the PDF to the AI parsing service
3. **Retry Logic**: Retries up to 3 times if parsing fails
4. **Database Update**: Updates the `parsed_resume` field with results
5. **Progress Logging**: Shows detailed progress and results

### 3. **Background Processing**
When triggered via API:
- Runs in FastAPI background tasks
- Returns immediately to the caller
- Processes candidates asynchronously
- Logs progress to server console

## Example Output

```
[Batch] Starting batch resume parsing at 2024-01-15 14:30:00
[Batch] Found 5 candidates that need resume parsing

[Batch] Processing candidate 1/5: John Doe (ID: 123)
[Batch] Processing candidate 123 (attempt 1/3)
[Batch] Absolute resume file path: /app/resumes/123.pdf
[Batch] Creating parser client for candidate 123
[Batch] Starting parsing for candidate 123
[Batch] Parsing completed for candidate 123
[Batch] Parsed result type: <class 'dict'>
[Batch] Parsed resume result keys for candidate 123: ['name', 'email', 'skills', 'education']
[Batch] Updating database for candidate 123
[Batch] Successfully updated candidate 123 with parsed resume data
[Batch] ✅ Successfully processed candidate 123

[Batch] Batch processing completed at 2024-01-15 14:32:15
[Batch] Results: 4 successful, 1 failed
```

## Configuration

### Environment Variables
The script uses the same configuration as your main application:
- `RESUME_STORAGE_DIR`: Directory where resume files are stored
- Database connection settings from your `.env` file

## Scheduling with Cron (Optional)

If you want to schedule the script to run automatically:

```bash
# Edit crontab
crontab -e

# Add entry to run daily at 2:30 PM
30 14 * * * cd /path/to/backend/app/scripts && python3 resume_parser_batch.py

# Add entry to run multiple times daily
0 9,15,21 * * * cd /path/to/backend/app/scripts && python3 resume_parser_batch.py
```

## Monitoring

### API Monitoring
Check the status via API:
```bash
# Check how many candidates need parsing
curl -X GET "http://localhost:8017/api/v1/admin/batch-parse-resumes/status"

# Trigger batch processing
curl -X POST "http://localhost:8017/api/v1/admin/batch-parse-resumes"
```

### Log Files
When running via script, you can redirect logs to a file:
```bash
python3 resume_parser_batch.py > batch_parser.log 2>&1
```

### Database Monitoring
Check parsing status in your application:
```sql
-- Count candidates without parsed resumes
SELECT COUNT(*) FROM candidate 
WHERE (parsed_resume IS NULL OR parsed_resume::text = '{}' OR parsed_resume::text = 'null') 
AND resume_url IS NOT NULL;

-- Check recent parsing activity
SELECT id, full_name, created_at, 
       CASE 
         WHEN parsed_resume IS NULL OR parsed_resume::text = '{}' OR parsed_resume::text = 'null' THEN 'Not Parsed'
         ELSE 'Parsed'
       END as status
FROM candidate 
WHERE resume_url IS NOT NULL 
ORDER BY created_at DESC;
```

## Troubleshooting

### Common Issues

1. **"No candidates to process"**
   - All candidates already have parsed resumes
   - No candidates have resume files

2. **"Resume file not found"**
   - Resume files may have been moved or deleted
   - Check `RESUME_STORAGE_DIR` configuration

3. **"API may have failed"**
   - AI parsing service is down or slow
   - Check if `http://localhost:8011/parser/parse` is accessible

4. **Permission errors**
   - Ensure script has read access to resume files
   - Check database connection permissions

### Debug Mode
Check the FastAPI server logs when running via API endpoints for detailed debugging information.

## Integration with Main Application

The batch script is fully integrated with your FastAPI application:
- **Shared Database**: Uses the same database and models
- **Shared File Storage**: Uses the same resume storage directory
- **Shared AI Service**: Uses the same parsing service
- **API Endpoints**: Can be triggered via HTTP requests
- **Background Processing**: Runs asynchronously without blocking the API

This ensures consistency and allows you to process historical data without affecting real-time operations. 