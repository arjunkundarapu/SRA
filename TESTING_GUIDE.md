# SRA System Testing Guide

This comprehensive guide covers testing the complete Smart Recruiting Assistant (SRA) system, including authentication, resume parsing, database operations, and AI interview functionality.

## Prerequisites

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory with the following:
   ```env
   # Supabase Configuration
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_KEY=your_supabase_service_role_key
   
   # AI Configuration
   GEMINI_API_KEY=your_google_gemini_api_key
   
   # Optional: Development Settings
   DEBUG=True
   LOG_LEVEL=INFO
   ```

3. **Set up Supabase database:**
   - Follow the `DATABASE_SCHEMA.md` instructions
   - Create all required tables: `profiles`, `interview_sessions`, `interview_messages`, `interview_reports`, `resume_uploads`
   - Set up Row Level Security (RLS) policies as specified
   - Verify both anon and service keys are configured

4. **Verify database setup:**
   Check that all tables exist in your Supabase dashboard:
   - profiles
   - interview_sessions 
   - interview_messages
   - interview_reports
   - resume_uploads

## Running the System

1. **Start the FastAPI server:**
   ```bash
   uvicorn backend.app.main:app --reload
   ```

2. **Verify server startup:**
   - Check console output for Supabase URL confirmation
   - No environment variable errors should appear
   - Server should start on http://127.0.0.1:8000

3. **Access the API documentation:**
   - Open http://127.0.0.1:8000/docs
   - This shows all available endpoints with interactive testing

## Testing Workflow

### Step 1: Test Authentication

#### 1.1 Register New User (Applicant)
```bash
curl -X POST "http://127.0.0.1:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "applicant@test.com",
       "password": "testpass123",
       "user_type": "applicant"
     }'
```

**Expected Response:**
```json
{
  "message": "User registered successfully",
  "user_id": "uuid-string"
}
```

#### 1.2 Register Recruiter
```bash
curl -X POST "http://127.0.0.1:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "recruiter@test.com",
       "password": "testpass123",
       "user_type": "recruiter"
     }'
```

#### 1.3 User Login
```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "applicant@test.com",
       "password": "testpass123"
     }'
```

**Expected Response:**
```json
{
  "access_token": "jwt-token",
  "refresh_token": "refresh-token",
  "user": {...}
}
```

### Step 2: Test Resume Upload and Management

#### 2.1 Upload Resume (with Database Storage)
```bash
curl -X POST "http://127.0.0.1:8000/applicant/upload_resume" \
     -H "Content-Type: multipart/form-data" \
     -F "applicant_id=your-user-id-from-step-1" \
     -F "file=@sample_resume.pdf"
```

**Expected Response:**
```json
{
  "upload_id": "uuid-string",
  "message": "Resume uploaded and parsed successfully",
  "parsed_resume": {
    "raw_text": "extracted text...",
    "contact_info": {"email": "john@example.com", "phone": "(555) 123-4567"},
    "skills": ["Python", "FastAPI", "Machine Learning"],
    "experience": [{"period": "2022-2024", "context": "Senior Developer..."}],
    "education": ["Bachelor's in Computer Science"],
    "summary": "Resume contains X words and Y characters..."
  },
  "file_name": "sample_resume.pdf",
  "file_size": 12345,
  "upload_timestamp": "2025-09-15T14:26:43.123456"
}
```

#### 2.2 Get All Resumes for Applicant
```bash
curl -X GET "http://127.0.0.1:8000/applicant/resumes/your-user-id"
```

#### 2.3 Get Specific Resume by Upload ID
```bash
curl -X GET "http://127.0.0.1:8000/applicant/resume/upload-id-from-upload"
```

#### 2.4 Delete Resume
```bash
curl -X DELETE "http://127.0.0.1:8000/applicant/resume/upload-id-from-upload"
```

### Step 3: Test Interview Management

#### 3.1 Start Interview Session
```bash
curl -X POST "http://127.0.0.1:8000/applicant/start_interview" \
     -H "Content-Type: application/json" \
     -d '{
       "applicant_id": "your-user-id",
       "resume_data": {
         "skills": ["Python", "FastAPI", "Machine Learning"],
         "experience": [{"period": "2022-2024", "context": "Senior Developer at Tech Corp"}],
         "summary": "Experienced software developer with 5 years experience"
       }
     }'
```

#### 3.2 Check Interview Status
```bash
curl -X GET "http://127.0.0.1:8000/applicant/interview_status/session-id"
```

### Step 5: Test WebSocket Interview (using JavaScript)
```html
<!DOCTYPE html>
<html>
<head>
    <title>AI Interview Test</title>
</head>
<body>
    <div id="messages"></div>
    <input type="text" id="messageInput" placeholder="Type your answer...">
    <button onclick="sendMessage()">Send</button>

    <script>
        const sessionId = "your-session-id-here";
        const ws = new WebSocket(`ws://localhost:8000/ws/interview/${sessionId}`);
        
        ws.onmessage = function(event) {
            const message = JSON.parse(event.data);
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML += `<div><strong>${message.type}:</strong> ${message.content}</div>`;
        };

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = {
                type: "user_message",
                content: input.value,
                user_id: "test-applicant"
            };
            ws.send(JSON.stringify(message));
            input.value = '';
        }

        function endInterview() {
            const message = {
                type: "end_interview"
            };
            ws.send(JSON.stringify(message));
        }
    </script>
    
    <button onclick="endInterview()">End Interview</button>
</body>
</html>
```

### Step 6: View Reports (Recruiter)
```bash
curl -X GET "http://localhost:8000/recruiter/applicant_reports"
```

## API Endpoints Summary

### Authentication Endpoints
- `POST /auth/register` - Register new user (applicant/recruiter)
- `POST /auth/login` - Login user

### Applicant Endpoints  
- `GET /applicant/` - Applicant dashboard
- `POST /applicant/upload_resume` - Upload and parse resume (saves to database)
- `GET /applicant/resumes/{applicant_id}` - Get all resumes for applicant
- `GET /applicant/resume/{upload_id}` - Get specific resume by ID
- `DELETE /applicant/resume/{upload_id}` - Delete resume
- `POST /applicant/start_interview` - Start interview session
- `GET /applicant/interview_status/{session_id}` - Check interview status

### Interview API
- `GET /api/questions` - Get AI questions
- `POST /api/next_question` - Process answer and get next question
- `POST /api/finish_interview` - Generate final report

### Recruiter Endpoints
- `GET /recruiter/` - Dashboard  
- `GET /recruiter/applicant_reports` - View all reports
- `GET /recruiter/report/{report_id}` - View specific report
- `GET /recruiter/applicant/{applicant_id}/reports` - View applicant history
- `GET /recruiter/statistics` - Interview statistics
- `GET /recruiter/search_reports` - Search/filter reports

### WebSocket Endpoints
- `ws://127.0.0.1:8000/ws/interview/{session_id}` - Real-time interview chat
- `ws://127.0.0.1:8000/ws/recruiter/{recruiter_id}` - Recruiter monitoring

## Expected Workflow

1. **Applicant registers** and logs in
2. **Uploads resume** → System parses and extracts skills/experience  
3. **Starts interview** → AI generates initial questions based on resume
4. **Real-time chat** → Applicant and AI have natural conversation
5. **Interview ends** → AI generates comprehensive report
6. **Recruiter views** → Report appears in recruiter dashboard

## Troubleshooting

### Common Issues:

1. **Import errors**: Make sure all dependencies are installed
2. **Database errors**: Verify Supabase setup and environment variables
3. **AI API errors**: Check your Gemini API key is valid
4. **WebSocket issues**: Ensure browser supports WebSockets

### Debug Tips:

- Check server logs for detailed error messages
- Use the FastAPI docs at `/docs` to test endpoints
- Verify database tables exist using Supabase dashboard
- Test API endpoints individually before testing full workflow

## Sample Resume Data

For testing, you can use this sample resume data:

```json
{
  "skills": ["Python", "JavaScript", "React", "FastAPI", "Machine Learning", "SQL"],
  "experience": [
    {
      "period": "2022-2024",
      "context": "Senior Software Developer at Tech Corp, leading AI projects"
    }
  ],
  "education": ["Bachelor's in Computer Science from State University"],
  "summary": "Experienced full-stack developer with 5 years in software development and 2 years in AI/ML projects."
}
```

This will help the AI generate relevant interview questions!

## Additional Testing Sections

### Database Verification
To verify resume data is properly stored:
1. Upload a resume using the endpoint
2. Check Supabase dashboard > resume_uploads table
3. Verify parsed_data JSON field contains extracted information
4. Use GET endpoints to retrieve stored data

### Authentication Flow Verification
1. Register user - check profiles table for new entry
2. Login - verify JWT tokens are returned
3. Test with both applicant and recruiter user types

### Error Handling Verification
1. Test with invalid file types (.txt, .jpg)
2. Test with missing required fields
3. Test with invalid user_type values
4. Verify proper HTTP status codes (400, 422, 500)

### Performance Testing
1. Upload large resume files (within limits)
2. Test concurrent user registrations
3. Monitor database response times

This comprehensive guide ensures all SRA functionality works correctly!