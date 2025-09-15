# Database Schema Setup for SRA

This document outlines the Supabase database schema required for the Smart Recruiting Assistant (SRA) system.

## Required Tables

### 1. profiles
Stores user profiles and types (applicant/recruiter)
```sql
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  user_type TEXT NOT NULL CHECK (user_type IN ('applicant', 'recruiter')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. interview_sessions  
Stores interview session information
```sql
CREATE TABLE interview_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  applicant_id TEXT NOT NULL,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
  resume_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3. interview_messages
Stores individual messages in interview conversations
```sql
CREATE TABLE interview_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4. interview_reports
Stores generated interview reports and analysis
```sql
CREATE TABLE interview_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
  applicant_id TEXT NOT NULL,
  report_content TEXT NOT NULL,
  interview_duration TEXT,
  total_questions INTEGER DEFAULT 0,
  generated_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('completed', 'draft')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 5. resume_uploads (Optional)
Stores uploaded resume metadata
```sql
CREATE TABLE resume_uploads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  applicant_id TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_size INTEGER,
  file_type TEXT,
  parsed_data JSONB,
  upload_timestamp TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Indexes for Performance

```sql
-- Index for faster session lookups
CREATE INDEX idx_interview_sessions_applicant_id ON interview_sessions(applicant_id);
CREATE INDEX idx_interview_sessions_status ON interview_sessions(status);

-- Index for faster message retrieval
CREATE INDEX idx_interview_messages_session_id ON interview_messages(session_id);
CREATE INDEX idx_interview_messages_timestamp ON interview_messages(timestamp);

-- Index for faster report queries
CREATE INDEX idx_interview_reports_applicant_id ON interview_reports(applicant_id);
CREATE INDEX idx_interview_reports_generated_at ON interview_reports(generated_at);
CREATE INDEX idx_interview_reports_status ON interview_reports(status);
```

## Row Level Security (RLS) Policies

```sql
-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE resume_uploads ENABLE ROW LEVEL SECURITY;

-- Profiles table policies
-- Allow users to insert their own profile during registration
CREATE POLICY "Users can insert own profile" ON profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

-- Users can view their own profile
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- Interview sessions policies
-- Applicants can insert their own sessions
CREATE POLICY "Applicants can create own sessions" ON interview_sessions
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM profiles 
      WHERE profiles.id = auth.uid() 
      AND profiles.user_type = 'applicant'
      AND interview_sessions.applicant_id = profiles.id::text
    )
  );

-- Applicants can view their own sessions
CREATE POLICY "Applicants can view own sessions" ON interview_sessions
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM profiles 
      WHERE profiles.id = auth.uid() 
      AND profiles.user_type = 'applicant'
      AND interview_sessions.applicant_id = profiles.id::text
    )
  );

-- Recruiters can view all sessions
CREATE POLICY "Recruiters can view all sessions" ON interview_sessions
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM profiles 
      WHERE profiles.id = auth.uid() 
      AND profiles.user_type = 'recruiter'
    )
  );

-- Recruiters can update all sessions
CREATE POLICY "Recruiters can update all sessions" ON interview_sessions
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM profiles 
      WHERE profiles.id = auth.uid() 
      AND profiles.user_type = 'recruiter'
    )
  );

-- Interview messages policies
-- Users can insert messages in their own sessions
CREATE POLICY "Users can insert messages in own sessions" ON interview_messages
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM interview_sessions s
      JOIN profiles p ON p.id = auth.uid()
      WHERE s.id = interview_messages.session_id
      AND (s.applicant_id = p.id::text OR p.user_type = 'recruiter')
    )
  );

-- Users can view messages in their accessible sessions
CREATE POLICY "Users can view messages in accessible sessions" ON interview_messages
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM interview_sessions s
      JOIN profiles p ON p.id = auth.uid()
      WHERE s.id = interview_messages.session_id
      AND (s.applicant_id = p.id::text OR p.user_type = 'recruiter')
    )
  );
```

## Environment Variables Required

Make sure these environment variables are set in your `.env` file:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
GEMINI_API_KEY=your_google_gemini_api_key
```

## Setup Instructions

1. Create a new Supabase project
2. Run the SQL commands above in the Supabase SQL editor
3. Configure authentication providers if needed
4. Set up environment variables
5. Test the connection using the database.py file

## Notes

- All timestamps use TIMESTAMPTZ for timezone awareness
- UUIDs are used for primary keys for better distribution
- JSONB is used for flexible resume data storage
- Indexes are created for common query patterns
- RLS policies ensure data security based on user roles