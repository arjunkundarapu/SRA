from fastapi import APIRouter
from ..services import recruiter_service

router = APIRouter(prefix='/recruiter',tags=["recruiter"])

@router.get('/')
async def recdash():
    "recruiter dashboard"

@router.get('/applicant_reports')
async def get_applicant_reports():
    reports = await recruiter_service.get_all_reports()
    return reports