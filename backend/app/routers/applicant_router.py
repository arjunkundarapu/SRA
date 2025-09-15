from fastapi import APIRouter,UploadFile,File,HTTPException,Form
from typing import Optional, Dict, Any
from ..services import applicant_service,interview_service
from ..schemas import InterviewResponse, InterviewStartRequest
from datetime import datetime

router = APIRouter(prefix='/applicant',tags=["applicant"])

@router.get('/')
async def appdash():
    """Applicant dashboard"""
    return {"message": "Welcome to your applicant dashboard", "status": "active"}

@router.post('/upload_resume')
async def upload_resume(applicant_id: str = Form(...), file: UploadFile = File(...)):
    """Upload and parse resume file, then save to database"""
    # Check file extension as backup if content_type detection fails
    file_extension = file.filename.lower().split('.')[-1] if file.filename else ""
    
    # More flexible content type checking
    valid_content_types = [
        "application/pdf", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream"  # Sometimes PDFs are detected as this
    ]
    
    valid_extensions = ["pdf", "docx"]
    
    # Check both content type and file extension
    if (file.content_type not in valid_content_types and file_extension not in valid_extensions):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. File type detected: '{file.content_type}', Extension: '{file_extension}'. Only PDF and DOCX files are supported."
        )
    
    # Additional validation for PDF files
    if file_extension == "pdf" or "pdf" in (file.content_type or "").lower():
        # Reset file pointer and read first few bytes to verify it's actually a PDF
        await file.seek(0)
        header = await file.read(4)
        await file.seek(0)  # Reset for processing
        
        if header != b'%PDF':
            raise HTTPException(status_code=400, detail="File appears to be corrupted or not a valid PDF.")
    
    try:
        # Parse the resume file
        parsed_data = await applicant_service.parse_resume(file)
        
        # Save to database
        result = await applicant_service.save_resume_to_database(applicant_id, file, parsed_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@router.get('/resumes/{applicant_id}')
async def get_applicant_resumes(applicant_id: str):
    """Get all resumes uploaded by an applicant"""
    try:
        resumes = await applicant_service.get_applicant_resumes(applicant_id)
        return {"resumes": resumes, "count": len(resumes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving resumes: {str(e)}")

@router.get('/resume/{upload_id}')
async def get_resume_by_id(upload_id: str):
    """Get a specific resume by its upload ID"""
    try:
        resume = await applicant_service.get_resume_by_id(upload_id)
        return resume
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Resume not found: {str(e)}")

@router.delete('/resume/{upload_id}')
async def delete_resume(upload_id: str):
    """Delete a resume by its upload ID"""
    try:
        # This would delete the resume from the database
        result = await applicant_service.delete_resume(upload_id)
        return {"message": "Resume deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error deleting resume: {str(e)}")

@router.post('/start_interview', response_model=InterviewResponse)
async def start_interview(request: InterviewStartRequest):
    """Start a new AI interview session"""
    try:
        # Convert ResumeData model to dict if provided
        resume_data = request.resume_data.dict() if request.resume_data else None
        session = await interview_service.initiate_interview(request.applicant_id, resume_data)
        return InterviewResponse(
            session_id=session["session_id"],
            message=session["message"],
            status=session["status"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting interview: {str(e)}")

@router.get('/interview_status/{session_id}')
async def get_interview_status(session_id: str):
    """Get the current status of an interview session"""
    try:
        # This would check the session status in the database
        return {"session_id": session_id, "status": "active", "message": "Interview in progress"}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Interview session not found")