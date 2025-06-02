# Resume Storage Configuration

## Overview

The application now saves uploaded resume PDFs in a dedicated directory with the candidate ID as the filename. Resume parsing is handled asynchronously in the background to ensure fast candidate creation and good user experience.

## Configuration

### Environment Variable

Add the following environment variable to your `.env` file:

```bash
RESUME_STORAGE_DIR=resumes
```

If not specified, the default directory is `resumes` in the application root.

## File Structure

Resume files are stored with the following naming convention:
```
{RESUME_STORAGE_DIR}/
├── 1.pdf          # Resume for candidate ID 1
├── 2.pdf          # Resume for candidate ID 2
├── 3.pdf          # Resume for candidate ID 3
└── ...
```

## API Endpoints

### Upload Resume (during candidate creation)

```http
POST /candidates/
Content-Type: multipart/form-data

candidate_in: {"full_name": "John Doe", "email": "john@example.com", "phone": "123456789"}
resume: [PDF file]
```

**Process Flow:**
1. Candidate is created immediately in the database
2. Resume file is saved permanently as `{candidate_id}.pdf`
3. The `resume_url` field is updated with the file path
4. **Resume parsing is scheduled as a background task**
5. API returns the candidate data immediately (fast response)
6. Parsing happens asynchronously and updates the `parsed_resume` field when complete

### Download Resume

```http
GET /candidates/{candidate_id}/resume
```

Returns the resume PDF file with proper filename and content type.

### Check Parsing Status

```http
GET /candidates/{candidate_id}/parsing-status
```

Returns the current status of resume parsing:

```json
{
  "candidate_id": 123,
  "parsing_status": "completed|pending|no_resume",
  "message": "Resume parsing completed",
  "has_resume_file": true,
  "has_parsed_data": true,
  "resume_url": "/path/to/resume.pdf"
}
```

**Status Values:**
- `no_resume`: No resume file was uploaded
- `pending`: Resume file exists but parsing is still in progress
- `completed`: Resume has been parsed and data is available

## Background Processing

### Why Background Processing?

Resume parsing involves calling external AI services which can be:
- **Slow** (5-30 seconds)
- **Unreliable** (network issues, API limits)
- **Non-critical** for immediate candidate creation

By moving parsing to the background:
- ✅ **Fast API response** (candidate created immediately)
- ✅ **Better UX** (no waiting for parsing)
- ✅ **Resilient** (parsing failures don't block candidate creation)
- ✅ **Scalable** (multiple parsing tasks can run concurrently)

### Implementation Details

The background task:
1. Uses the saved resume file for parsing
2. Creates a new database session for the update
3. Handles errors gracefully (logs but doesn't crash)
4. Updates the `parsed_resume` field when successful

## Features

- **Immediate candidate creation**: Candidates are created instantly, parsing happens later
- **Background resume parsing**: AI parsing runs asynchronously without blocking the API
- **Automatic directory creation**: The resume storage directory is created automatically if it doesn't exist
- **File cleanup**: Temporary files are cleaned up after processing
- **Resume deletion**: When a candidate is deleted, their resume file is also removed
- **Permission checking**: Only authorized users can access resume files
- **Error handling**: File operations are wrapped in try-catch blocks to prevent API failures
- **Parsing status tracking**: Check if resume parsing is complete via API endpoint

## Utility Functions

The following utility functions are available in `utils/file_utils.py`:

- `save_resume_file(temp_file_path, candidate_id)`: Save a resume file permanently
- `get_resume_file_path(candidate_id)`: Get the path to a candidate's resume
- `delete_resume_file(candidate_id)`: Delete a candidate's resume file
- `get_resume_file_size(candidate_id)`: Get the size of a resume file
- `ensure_resume_directory()`: Ensure the storage directory exists

## Frontend Integration

### Recommended UX Flow

1. **Upload**: User uploads candidate + resume → immediate success response
2. **Show Status**: Display "Resume processing..." with a spinner
3. **Poll Status**: Periodically check `/candidates/{id}/parsing-status`
4. **Update UI**: Show "Resume processed!" when status becomes "completed"

### Example Frontend Code

```javascript
// After successful candidate creation
const candidate = await createCandidate(candidateData, resumeFile);

// Show processing status
showProcessingStatus(candidate.id);

// Poll for completion
const checkStatus = async () => {
  const status = await fetch(`/candidates/${candidate.id}/parsing-status`);
  const data = await status.json();
  
  if (data.parsing_status === 'completed') {
    showSuccess('Resume processed successfully!');
  } else if (data.parsing_status === 'pending') {
    setTimeout(checkStatus, 2000); // Check again in 2 seconds
  }
};

checkStatus();
```

## Security Considerations

- Resume files are stored outside the web root for security
- Access to resume files is controlled through the API endpoint
- File paths are validated to prevent directory traversal attacks
- Only PDF files are currently supported for resumes
- Background tasks use proper database sessions and error handling

## Backup and Maintenance

- The resume storage directory should be included in your backup strategy
- Consider implementing file rotation or archival for old resumes
- Monitor disk space usage as the number of candidates grows
- Background task failures are logged for monitoring and debugging 