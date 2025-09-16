# 🗄️ Database Schema Migration for Video Interview Support

## Issue
The database is missing the `interview_type` column that was added to support video interviews:

```
Error saving session to database: {'message': "Could not find the 'interview_type' column of 'interview_sessions' in the schema cache", 'code': 'PGRST204', 'hint': None, 'details': None}
```

## Required Database Updates

### 1. Add `interview_type` column to `interview_sessions` table

```sql
-- Add interview_type column to support both text and video interviews
ALTER TABLE interview_sessions 
ADD COLUMN interview_type TEXT DEFAULT 'text' 
CHECK (interview_type IN ('text', 'video'));

-- Add comment for documentation
COMMENT ON COLUMN interview_sessions.interview_type IS 'Type of interview: text or video';
```

### 2. Add `message_type` column to `interview_messages` table

```sql
-- Add message_type column to support different message types
ALTER TABLE interview_messages 
ADD COLUMN message_type TEXT DEFAULT 'text' 
CHECK (message_type IN ('text', 'audio', 'video'));

-- Add comment for documentation  
COMMENT ON COLUMN interview_messages.message_type IS 'Type of message: text, audio, or video';
```

### 3. Add `interview_type` column to `interview_reports` table

```sql
-- Add interview_type column to reports for filtering
ALTER TABLE interview_reports 
ADD COLUMN interview_type TEXT DEFAULT 'text' 
CHECK (interview_type IN ('text', 'video'));

-- Add comment for documentation
COMMENT ON COLUMN interview_reports.interview_type IS 'Type of interview that generated this report';
```

### 4. Create indexes for new columns (optional, for performance)

```sql
-- Create indexes for better query performance on new columns
CREATE INDEX idx_interview_sessions_interview_type ON interview_sessions(interview_type);
CREATE INDEX idx_interview_messages_message_type ON interview_messages(message_type);  
CREATE INDEX idx_interview_reports_interview_type ON interview_reports(interview_type);
```

## How to Apply the Migration

### Option 1: Supabase Dashboard (Recommended)
1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the SQL commands above
4. Run each command one by one

### Option 2: Using SQL Script
1. Save the SQL commands to a file called `migration_video_interviews.sql`
2. Run through Supabase SQL editor or your preferred database client

## Complete Migration Script

```sql
-- Migration: Add Video Interview Support
-- Date: 2025-09-16
-- Description: Add columns to support video interview functionality

-- 1. Add interview_type to interview_sessions
ALTER TABLE interview_sessions 
ADD COLUMN interview_type TEXT DEFAULT 'text' 
CHECK (interview_type IN ('text', 'video'));

COMMENT ON COLUMN interview_sessions.interview_type IS 'Type of interview: text or video';

-- 2. Add message_type to interview_messages  
ALTER TABLE interview_messages 
ADD COLUMN message_type TEXT DEFAULT 'text' 
CHECK (message_type IN ('text', 'audio', 'video'));

COMMENT ON COLUMN interview_messages.message_type IS 'Type of message: text, audio, or video';

-- 3. Add interview_type to interview_reports
ALTER TABLE interview_reports 
ADD COLUMN interview_type TEXT DEFAULT 'text' 
CHECK (interview_type IN ('text', 'video'));

COMMENT ON COLUMN interview_reports.interview_type IS 'Type of interview that generated this report';

-- 4. Create performance indexes
CREATE INDEX idx_interview_sessions_interview_type ON interview_sessions(interview_type);
CREATE INDEX idx_interview_messages_message_type ON interview_messages(message_type);
CREATE INDEX idx_interview_reports_interview_type ON interview_reports(interview_type);

-- 5. Verify the migration
SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'interview_sessions' 
AND column_name = 'interview_type';

SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'interview_messages' 
AND column_name = 'message_type';

SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'interview_reports' 
AND column_name = 'interview_type';
```

## Expected Results After Migration

After running the migration, you should see:

1. **interview_sessions** table with `interview_type` column
2. **interview_messages** table with `message_type` column  
3. **interview_reports** table with `interview_type` column
4. Performance indexes on the new columns
5. No more "Could not find column" errors

## Verification

After running the migration, test that it works:

1. **Check Column Exists**:
   ```sql
   \d interview_sessions
   ```

2. **Test Insert**:
   ```sql
   INSERT INTO interview_sessions (applicant_id, start_time, interview_type) 
   VALUES ('test_user', NOW(), 'video');
   ```

3. **Test Video Interview**: Try starting a video interview through the app

## Rollback (if needed)

If you need to rollback the changes:

```sql
-- Remove the added columns (CAUTION: This will delete data)
ALTER TABLE interview_sessions DROP COLUMN interview_type;
ALTER TABLE interview_messages DROP COLUMN message_type;
ALTER TABLE interview_reports DROP COLUMN interview_type;

-- Remove indexes
DROP INDEX idx_interview_sessions_interview_type;
DROP INDEX idx_interview_messages_message_type;  
DROP INDEX idx_interview_reports_interview_type;
```

## Post-Migration Notes

- **Default Values**: All existing records will have `interview_type = 'text'` and `message_type = 'text'`
- **New Video Interviews**: Will be saved with `interview_type = 'video'`
- **Backward Compatibility**: Existing text-based interviews continue to work
- **Performance**: Indexes improve query performance for filtering by interview type

## Files That Use These Columns

- **[video_interview_service.py](file://c:\Users\Anjal\SRA\backend\app\services\video_interview_service.py)** - Sets interview_type = 'video' when saving sessions
- **[interview_service.py](file://c:\Users\Anjal\SRA\backend\app\services\interview_service.py)** - Uses interview_type = 'text' for regular interviews
- **[recruiter_service.py](file://c:\Users\Anjal\SRA\backend\app\services\recruiter_service.py)** - Filters reports by interview_type

After applying this migration, the video interview functionality should work without database errors! 🎉