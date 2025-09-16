from pydantic import BaseModel,EmailStr
from pydantic import BaseModel,EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# Authentication Schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    user_type: str  # "recruiter" or "applicant"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Resume and Applicant Schemas
class ResumeData(BaseModel):
    raw_text: Optional[str] = None
    contact_info: Dict[str, Any]
    skills: List[str]
    experience: List[Dict[str, Any]]
    education: Optional[List[str]] = None
    summary: str

class ResumeUploadResponse(BaseModel):
    parsed_resume: ResumeData
    file_name: str
    file_size: int
    upload_timestamp: str

# Interview Schemas
class InterviewStartRequest(BaseModel):
    applicant_id: str
    resume_data: Optional[ResumeData] = None

class InterviewMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str

class InterviewSession(BaseModel):
    session_id: str
    applicant_id: str
    start_time: str
    end_time: Optional[str] = None
    status: str  # "active", "completed", "cancelled"
    conversation_history: List[InterviewMessage]
    resume_data: Optional[ResumeData] = None

class InterviewResponse(BaseModel):
    session_id: str
    message: str
    status: str

class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str

# Report Schemas
class InterviewReport(BaseModel):
    report_id: str
    session_id: str
    applicant_id: str
    interview_date: str
    duration: str
    total_questions: int
    report_content: str
    generated_at: str
    status: str

class ReportSummary(BaseModel):
    report_id: str
    applicant_id: str
    interview_date: str
    duration: str
    status: str
    brief_summary: str

# Recruiter Schemas
class InterviewStatistics(BaseModel):
    total_interviews: int
    completed_interviews: int
    active_interviews: int
    completion_rate: float
    last_updated: str

class ReportSearchRequest(BaseModel):
    query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = 50
    offset: Optional[int] = 0

# WebSocket Schemas
class WebSocketMessage(BaseModel):
    type: str  # "message", "join", "leave", "error"
    session_id: Optional[str] = None
    content: Optional[str] = None
    timestamp: str
    user_id: Optional[str] = None

class ChatMessage(BaseModel):
    session_id: str
    message: str
    user_type: str  # "applicant" or "interviewer"

# API Response Schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool