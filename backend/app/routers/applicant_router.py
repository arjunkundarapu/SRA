from fastapi import APIRouter,UploadFile,File,HTTPException
from ..services import applicant_service,interview_service

router = APIRouter(prefix='/applicant',tags=["applicant"])

@router.get('/')
async def appdash():
    "applicant dashboard"

@router.post('/upload_resume')
async def upload_resume(file: UploadFile = File(...)):
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    parsed_data = await applicant_service.parse_resume(file)
    return {"parsed_resume": parsed_data}

@router.post('/start_interview')
async def start_interview(applicant_id: str):
    session = await interview_service.initiate_interview(applicant_id)
    return session