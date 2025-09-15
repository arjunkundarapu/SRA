import requests
import os
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from ..database import supabase

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# In-memory storage for interview sessions (in production, use database)
interview_sessions = {}

def get_questions(prompt: str):
    """
    Calls Gemini API with the given prompt and returns the generated questions.
    """
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "key": GEMINI_API_KEY
    }
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=data)
    if response.status_code != 200:
        raise Exception(f"Gemini API error: {response.status_code} {response.text}")
    result = response.json()
    # Extract the generated text from the response
    try:
        generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
        return generated_text
    except (KeyError, IndexError):
        raise Exception("Unexpected Gemini API response format")

async def initiate_interview(applicant_id: str, resume_data: Optional[Dict] = None) -> Dict:
    """
    Start a new interview session for an applicant
    """
    session_id = str(uuid.uuid4())
    
    # Create initial interview context based on resume
    candidate_name = ""
    if resume_data and resume_data.get('contact_info', {}).get('name'):
        candidate_name = resume_data['contact_info']['name']
    
    context = f"""
    You are an AI interviewer conducting a professional job interview. 
    You should act like a human recruiter - be friendly, professional, and engaging.
    
    Interview Guidelines:
    1. Start with a warm greeting and introduction
    2. Use the candidate's actual name if provided: {candidate_name if candidate_name else '[Candidate Name]'}
    3. Ask relevant questions based on the candidate's resume
    4. Follow up on answers with deeper questions
    5. Assess technical skills, experience, and cultural fit
    6. Keep the conversation natural and flowing
    7. Be encouraging and positive
    
    Candidate Information:
    Name: {candidate_name if candidate_name else 'Not provided'}
    Resume Summary: {resume_data.get('summary', 'No resume provided') if resume_data else 'No resume provided'}
    Skills: {', '.join(resume_data.get('skills', [])) if resume_data else 'Not specified'}
    Experience: {len(resume_data.get('experience', [])) if resume_data else 0} experience entries found
    
    Start the interview with a professional greeting using the candidate's name (if available) and your first question.
    """
    
    # Get initial question from AI
    initial_response = get_questions(context)
    
    # Store session data
    session_data = {
        "session_id": session_id,
        "applicant_id": applicant_id,
        "start_time": datetime.now().isoformat(),
        "resume_data": resume_data,
        "conversation_history": [
            {"role": "assistant", "content": initial_response, "timestamp": datetime.now().isoformat()}
        ],
        "status": "active"
    }
    
    interview_sessions[session_id] = session_data
    
    # Store in database
    try:
        supabase.table("interview_sessions").insert({
            "id": session_id,
            "applicant_id": applicant_id,
            "start_time": session_data["start_time"],
            "resume_data": json.dumps(resume_data) if resume_data else None,
            "status": "active"
        }).execute()
    except Exception as e:
        print(f"Database error: {e}")  # In production, use proper logging
    
    return {
        "session_id": session_id,
        "message": initial_response,
        "status": "active"
    }

async def process_answer_and_get_next(session_id: str, answer: str) -> Dict:
    """
    Process applicant's answer and generate next question
    """
    if session_id not in interview_sessions:
        raise Exception("Interview session not found")
    
    session = interview_sessions[session_id]
    
    # Add applicant's answer to conversation history
    session["conversation_history"].append({
        "role": "user",
        "content": answer,
        "timestamp": datetime.now().isoformat()
    })
    
    # Build context for next question
    conversation_context = "\n".join([
        f"{msg['role']}: {msg['content']}" for msg in session["conversation_history"][-5:]  # Last 5 messages
    ])
    
    prompt = f"""
    Continue this job interview conversation. You are the interviewer.
    
    Previous conversation:
    {conversation_context}
    
    The candidate just answered: "{answer}"
    
    Provide a thoughtful follow-up question or response. Consider:
    1. Acknowledge their answer appropriately
    2. Ask a relevant follow-up question
    3. Dive deeper into their experience or skills
    4. Keep the conversation natural and engaging
    5. If this seems like a good stopping point, you can wrap up the interview
    
    Respond as the interviewer would in a real interview.
    """
    
    # Get AI response
    ai_response = get_questions(prompt)
    
    # Add AI response to conversation history
    session["conversation_history"].append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.now().isoformat()
    })
    
    # Update database
    try:
        supabase.table("interview_messages").insert({
            "session_id": session_id,
            "role": "user",
            "content": answer,
            "timestamp": datetime.now().isoformat()
        }).execute()
        
        supabase.table("interview_messages").insert({
            "session_id": session_id,
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        print(f"Database error: {e}")
    
    return {
        "session_id": session_id,
        "message": ai_response,
        "status": session["status"]
    }

async def generate_report(session_id: str) -> Dict:
    """
    Generate interview report and analysis
    """
    if session_id not in interview_sessions:
        raise Exception("Interview session not found")
    
    session = interview_sessions[session_id]
    session["status"] = "completed"
    session["end_time"] = datetime.now().isoformat()
    
    # Build conversation for analysis
    conversation_text = "\n".join([
        f"{msg['role']}: {msg['content']}" for msg in session["conversation_history"]
    ])
    
    # Generate comprehensive report using AI
    report_prompt = f"""
    Analyze this job interview conversation and provide a comprehensive report.
    
    Interview Conversation:
    {conversation_text}
    
    Please provide a detailed assessment including:
    
    1. **Overall Performance**: Rate the candidate's overall interview performance (1-10)
    2. **Communication Skills**: Assess clarity, articulation, and professionalism
    3. **Technical Competency**: Evaluate technical knowledge and skills demonstrated
    4. **Experience Relevance**: How well their experience matches the role
    5. **Cultural Fit**: Assessment of personality and cultural alignment
    6. **Strengths**: Key strengths demonstrated during the interview
    7. **Areas for Improvement**: Constructive feedback and development areas
    8. **Recommendation**: Hire/Don't Hire with reasoning
    9. **Summary**: Brief overall summary and key takeaways
    
    Format the response as a professional interview assessment report.
    """
    
    report_content = get_questions(report_prompt)
    
    # Create report data
    report_data = {
        "session_id": session_id,
        "applicant_id": session["applicant_id"],
        "interview_duration": calculate_duration(session["start_time"], session["end_time"]),
        "total_questions": len([msg for msg in session["conversation_history"] if msg["role"] == "assistant"]),
        "report_content": report_content,
        "generated_at": datetime.now().isoformat(),
        "status": "completed"
    }
    
    # Store report in database
    try:
        supabase.table("interview_reports").insert({
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "applicant_id": session["applicant_id"],
            "report_content": report_content,
            "interview_duration": report_data["interview_duration"],
            "total_questions": report_data["total_questions"],
            "generated_at": report_data["generated_at"],
            "status": "completed"
        }).execute()
        
        # Update session status
        supabase.table("interview_sessions").update({
            "status": "completed",
            "end_time": session["end_time"]
        }).eq("id", session_id).execute()
        
    except Exception as e:
        print(f"Database error: {e}")
    
    return report_data

def calculate_duration(start_time: str, end_time: str) -> str:
    """
    Calculate interview duration in minutes
    """
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        duration = end - start
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} minutes"
    except:
        return "Unknown"