from fastapi import APIRouter,Form
from ..schemas import InterviewAnswerRequest
router = APIRouter(prefix="/api",tags=["api"])

from ..services import interview_service

@router.get('/questions')
async def get_questions(prompt):
    return interview_service.get_questions(prompt)

@router.post('/next_question')
async def next_question(request: InterviewAnswerRequest):
    followup = await interview_service.process_answer_and_get_next(request.session_id, request.answer)
    return followup

@router.post('/finish_interview')
async def finish_interview(session_id: str):
    report = await interview_service.generate_report(session_id)
    # Optionally, notify recruiter here
    return report