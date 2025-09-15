from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from ..services import recruiter_service
from ..schemas import InterviewReport, InterviewStatistics, APIResponse

router = APIRouter(prefix='/recruiter', tags=["recruiter"])

@router.get('/')
async def recruiter_dashboard():
    """Recruiter dashboard with summary information"""
    try:
        # Get basic statistics for dashboard
        stats = await recruiter_service.get_interview_statistics()
        return {
            "message": "Welcome to your recruiter dashboard",
            "status": "active",
            "dashboard_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dashboard: {str(e)}")

@router.get('/applicant_reports')
async def get_applicant_reports():
    """Get all interview reports"""
    try:
        reports = await recruiter_service.get_all_reports()
        return {"reports": reports, "total": len(reports)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching reports: {str(e)}")

@router.get('/report/{report_id}')
async def get_report_details(report_id: str):
    """Get detailed view of a specific interview report"""
    try:
        report = await recruiter_service.get_report_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching report: {str(e)}")

@router.get('/applicant/{applicant_id}/reports')
async def get_applicant_interview_history(applicant_id: str):
    """Get all interview reports for a specific applicant"""
    try:
        reports = await recruiter_service.get_reports_by_applicant(applicant_id)
        return {"applicant_id": applicant_id, "reports": reports, "total": len(reports)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching applicant reports: {str(e)}")

@router.get('/statistics', response_model=InterviewStatistics)
async def get_interview_statistics():
    """Get overall interview statistics"""
    try:
        stats = await recruiter_service.get_interview_statistics()
        return InterviewStatistics(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

@router.get('/search_reports')
async def search_interview_reports(
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="Filter by status (completed, draft)"),
    applicant_id: Optional[str] = Query(None, description="Filter by applicant ID"),
    date_from: Optional[str] = Query(None, description="Filter by date from (ISO format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by date to (ISO format: YYYY-MM-DD)"),
    limit: Optional[int] = Query(50, description="Maximum number of results"),
    offset: Optional[int] = Query(0, description="Number of results to skip")
):
    """Search and filter interview reports with pagination"""
    try:
        filters = {}
        if status:
            if status not in ["completed", "draft"]:
                raise HTTPException(status_code=400, detail="Invalid status. Must be 'completed' or 'draft'")
            filters["status"] = status
        if applicant_id:
            filters["applicant_id"] = applicant_id
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        
        # Get all matching reports
        all_reports = await recruiter_service.search_reports(q or "", filters)
        
        # Apply pagination with safe defaults
        total_results = len(all_reports)
        safe_limit = limit or 50
        safe_offset = offset or 0
        paginated_reports = all_reports[safe_offset:safe_offset + safe_limit]
        
        return {
            "query": q,
            "filters": filters,
            "reports": paginated_reports,
            "pagination": {
                "total": total_results,
                "limit": safe_limit,
                "offset": safe_offset,
                "has_next": safe_offset + safe_limit < total_results,
                "has_prev": safe_offset > 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching reports: {str(e)}")