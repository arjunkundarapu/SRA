import PyPDF2
import docx
import re
from typing import Dict, List
from fastapi import UploadFile
import io
from datetime import datetime
from ..database import supabase_admin
import uuid

async def parse_resume(file: UploadFile) -> Dict:
    """
    Parse resume file (PDF or DOCX) and extract key information
    """
    content = ""
    
    # Read file content based on type
    if file.content_type == "application/pdf":
        content = await extract_pdf_text(file)
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        content = await extract_docx_text(file)
    else:
        raise ValueError("Unsupported file type")
    
    # Extract structured information
    parsed_data = {
        "raw_text": content,
        "contact_info": extract_contact_info(content),
        "skills": extract_skills(content),
        "experience": extract_experience(content),
        "education": extract_education(content),
        "summary": generate_summary(content)
    }
    
    return parsed_data

async def save_resume_to_database(applicant_id: str, file: UploadFile, parsed_data: Dict) -> Dict:
    """
    Save parsed resume data to the database
    """
    try:
        # Generate unique ID for the resume upload
        upload_id = str(uuid.uuid4())
        
        # Prepare data for database insertion
        resume_record = {
            "id": upload_id,
            "applicant_id": applicant_id,
            "file_name": file.filename or "unknown",
            "file_size": file.size or 0,
            "file_type": file.content_type,
            "parsed_data": parsed_data,
            "upload_timestamp": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        # Insert into resume_uploads table using admin client
        result = supabase_admin.table("resume_uploads").insert(resume_record).execute()
        
        if result.data:
            return {
                "upload_id": upload_id,
                "message": "Resume uploaded and parsed successfully",
                "parsed_resume": parsed_data,
                "file_name": file.filename or "unknown",
                "file_size": file.size or 0,
                "upload_timestamp": resume_record["upload_timestamp"]
            }
        else:
            raise Exception("Failed to save resume to database")
            
    except Exception as e:
        raise Exception(f"Database error while saving resume: {str(e)}")

async def get_applicant_resumes(applicant_id: str) -> List[Dict]:
    """
    Get all resumes uploaded by an applicant
    """
    try:
        result = supabase_admin.table("resume_uploads").select("*").eq("applicant_id", applicant_id).execute()
        
        if result.data:
            return result.data
        else:
            return []
            
    except Exception as e:
        raise Exception(f"Error retrieving resumes: {str(e)}")

async def get_resume_by_id(upload_id: str) -> Dict:
    """
    Get a specific resume by its upload ID
    """
    try:
        result = supabase_admin.table("resume_uploads").select("*").eq("id", upload_id).single().execute()
        
        if result.data:
            return result.data
        else:
            raise Exception("Resume not found")
            
    except Exception as e:
        raise Exception(f"Error retrieving resume: {str(e)}")

async def delete_resume(upload_id: str) -> bool:
    """
    Delete a resume by its upload ID
    """
    try:
        result = supabase_admin.table("resume_uploads").delete().eq("id", upload_id).execute()
        
        if result.data:
            return True
        else:
            raise Exception("Resume not found or could not be deleted")
            
    except Exception as e:
        raise Exception(f"Error deleting resume: {str(e)}")

async def extract_pdf_text(file: UploadFile) -> str:
    """Extract text from PDF file"""
    try:
        content = await file.read()
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        await file.seek(0)  # Reset file pointer
        return text
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")

async def extract_docx_text(file: UploadFile) -> str:
    """Extract text from DOCX file"""
    try:
        content = await file.read()
        doc = docx.Document(io.BytesIO(content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        await file.seek(0)  # Reset file pointer
        return text
    except Exception as e:
        raise ValueError(f"Error reading DOCX: {str(e)}")

def extract_contact_info(text: str) -> Dict:
    """Extract contact information from resume text"""
    contact_info = {}
    
    # Extract name (usually the first line or prominent text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Try to find name - look for patterns that indicate a name
    name_candidates = []
    for i, line in enumerate(lines[:5]):  # Check first 5 lines
        # Skip lines that look like headers, emails, or phone numbers
        if not any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum', '@', 'phone', 'email', 'address']):
            # Look for lines with 2-4 words that could be a name
            words = line.split()
            if 2 <= len(words) <= 4 and all(word.replace('.', '').replace(',', '').isalpha() for word in words):
                name_candidates.append(line)
    
    if name_candidates:
        contact_info["name"] = name_candidates[0]
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        contact_info["email"] = emails[0]
    
    # Extract phone number
    phone_pattern = r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'
    phones = re.findall(phone_pattern, text)
    if phones:
        contact_info["phone"] = f"({phones[0][0]}) {phones[0][1]}-{phones[0][2]}"
    
    return contact_info

def extract_skills(text: str) -> List[str]:
    """Extract skills from resume text"""
    # Common technical skills keywords
    skill_keywords = [
        "Python", "Java", "JavaScript", "React", "Node.js", "SQL", "MongoDB",
        "AWS", "Docker", "Kubernetes", "Git", "HTML", "CSS", "TypeScript",
        "C++", "C#", "Ruby", "PHP", "Go", "Rust", "Swift", "Kotlin",
        "Machine Learning", "AI", "Data Science", "Analytics", "Tableau",
        "Excel", "PowerBI", "Agile", "Scrum", "DevOps", "Linux", "Windows"
    ]
    
    found_skills = []
    text_upper = text.upper()
    
    for skill in skill_keywords:
        if skill.upper() in text_upper:
            found_skills.append(skill)
    
    return found_skills

def extract_experience(text: str) -> List[Dict]:
    """Extract work experience from resume text"""
    # This is a simplified extraction - in production, you'd use more sophisticated NLP
    experience_sections = []
    
    # Look for common experience indicators
    experience_patterns = [
        r'(\d{4})\s*[-–]\s*(\d{4}|present|current)',
        r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|present|current)'
    ]
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        for pattern in experience_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Try to extract job title and company from surrounding context
                context = ' '.join(lines[max(0, i-2):i+3])
                experience_sections.append({
                    "period": line.strip(),
                    "context": context.strip()
                })
                break
    
    return experience_sections

def extract_education(text: str) -> List[str]:
    """Extract education information from resume text"""
    education_keywords = [
        "Bachelor", "Master", "PhD", "Doctorate", "Associate", "Degree",
        "University", "College", "Institute", "School", "Education"
    ]
    
    education_info = []
    lines = text.split('\n')
    
    for line in lines:
        for keyword in education_keywords:
            if keyword.lower() in line.lower():
                education_info.append(line.strip())
                break
    
    return list(set(education_info))  # Remove duplicates

def generate_summary(text: str) -> str:
    """Generate a brief summary of the resume"""
    # This is a simple summary - in production, you'd use AI/NLP for better summarization
    word_count = len(text.split())
    char_count = len(text)
    
    return f"Resume contains {word_count} words and {char_count} characters. " \
           f"Analysis complete - ready for AI interview preparation."