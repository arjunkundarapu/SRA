from typing import List, Dict, Optional
from datetime import datetime
from ..database import supabase

async def get_all_reports() -> List[Dict]:
    """
    Get all interview reports for recruiters to review
    """
    try:
        # Fetch all completed interview reports
        response = supabase.table("interview_reports").select(
            "*, interview_sessions(applicant_id, start_time, end_time)"
        ).eq("status", "completed").order("generated_at", desc=True).execute()
        
        reports = response.data if response.data else []
        
        # Format reports for better presentation
        formatted_reports = []
        for report in reports:
            formatted_report = {
                "report_id": report["id"],
                "session_id": report["session_id"],
                "applicant_id": report["applicant_id"],
                "interview_date": report.get("interview_sessions", {}).get("start_time", "Unknown"),
                "duration": report["interview_duration"],
                "total_questions": report["total_questions"],
                "report_content": report["report_content"],
                "generated_at": report["generated_at"],
                "status": report["status"]
            }
            formatted_reports.append(formatted_report)
        
        return formatted_reports
        
    except Exception as e:
        print(f"Error fetching reports: {e}")
        return []

async def get_report_by_id(report_id: str) -> Optional[Dict]:
    """
    Get a specific interview report by ID
    """
    try:
        response = supabase.table("interview_reports").select(
            "*, interview_sessions(applicant_id, start_time, end_time)"
        ).eq("id", report_id).single().execute()
        
        if response.data:
            report = response.data
            return {
                "report_id": report["id"],
                "session_id": report["session_id"],
                "applicant_id": report["applicant_id"],
                "interview_date": report.get("interview_sessions", {}).get("start_time", "Unknown"),
                "duration": report["interview_duration"],
                "total_questions": report["total_questions"],
                "report_content": report["report_content"],
                "generated_at": report["generated_at"],
                "status": report["status"]
            }
        return None
        
    except Exception as e:
        print(f"Error fetching report {report_id}: {e}")
        return None

async def get_reports_by_applicant(applicant_id: str) -> List[Dict]:
    """
    Get all interview reports for a specific applicant
    """
    try:
        response = supabase.table("interview_reports").select(
            "*, interview_sessions(start_time, end_time)"
        ).eq("applicant_id", applicant_id).order("generated_at", desc=True).execute()
        
        reports = response.data if response.data else []
        
        formatted_reports = []
        for report in reports:
            formatted_report = {
                "report_id": report["id"],
                "session_id": report["session_id"],
                "interview_date": report.get("interview_sessions", {}).get("start_time", "Unknown"),
                "duration": report["interview_duration"],
                "total_questions": report["total_questions"],
                "report_content": report["report_content"],
                "generated_at": report["generated_at"],
                "status": report["status"]
            }
            formatted_reports.append(formatted_report)
        
        return formatted_reports
        
    except Exception as e:
        print(f"Error fetching reports for applicant {applicant_id}: {e}")
        return []

async def get_interview_statistics() -> Dict:
    """
    Get overall interview statistics for recruiters
    """
    try:
        # Get total interviews
        total_sessions = supabase.table("interview_sessions").select("*").execute()
        total_count = len(total_sessions.data) if total_sessions.data else 0
        
        # Get completed interviews
        completed_sessions = supabase.table("interview_sessions").select(
            "*"
        ).eq("status", "completed").execute()
        completed_count = len(completed_sessions.data) if completed_sessions.data else 0
        
        # Get active interviews
        active_sessions = supabase.table("interview_sessions").select(
            "*"
        ).eq("status", "active").execute()
        active_count = len(active_sessions.data) if active_sessions.data else 0
        
        # Calculate completion rate
        completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0
        
        return {
            "total_interviews": total_count,
            "completed_interviews": completed_count,
            "active_interviews": active_count,
            "completion_rate": round(completion_rate, 2),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error fetching statistics: {e}")
        return {
            "total_interviews": 0,
            "completed_interviews": 0,
            "active_interviews": 0,
            "completion_rate": 0,
            "last_updated": datetime.now().isoformat()
        }

async def search_reports(query: str, filters: Optional[Dict] = None) -> List[Dict]:
    """
    Search interview reports based on query and filters
    """
    try:
        # Start with base query
        db_query = supabase.table("interview_reports").select(
            "*, interview_sessions(applicant_id, start_time, end_time)"
        )
        
        # Apply filters if provided
        if filters:
            if filters.get("status"):
                db_query = db_query.eq("status", filters["status"])
            if filters.get("applicant_id"):
                db_query = db_query.eq("applicant_id", filters["applicant_id"])
            if filters.get("date_from"):
                db_query = db_query.gte("generated_at", filters["date_from"])
            if filters.get("date_to"):
                db_query = db_query.lte("generated_at", filters["date_to"])
        
        # Execute query
        response = db_query.order("generated_at", desc=True).execute()
        reports = response.data if response.data else []
        
        # Filter by text search if query provided
        if query:
            filtered_reports = []
            query_lower = query.lower()
            for report in reports:
                if (query_lower in report["report_content"].lower() or 
                    query_lower in report["applicant_id"].lower()):
                    filtered_reports.append(report)
            reports = filtered_reports
        
        # Format results
        formatted_reports = []
        for report in reports:
            formatted_report = {
                "report_id": report["id"],
                "session_id": report["session_id"],
                "applicant_id": report["applicant_id"],
                "interview_date": report.get("interview_sessions", {}).get("start_time", "Unknown"),
                "duration": report["interview_duration"],
                "total_questions": report["total_questions"],
                "report_content": report["report_content"],
                "generated_at": report["generated_at"],
                "status": report["status"]
            }
            formatted_reports.append(formatted_report)
        
        return formatted_reports
        
    except Exception as e:
        print(f"Error searching reports: {e}")
        return []