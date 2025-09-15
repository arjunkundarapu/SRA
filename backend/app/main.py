from fastapi import FastAPI
from .routers import applicant_router, recruiter_router, auth_router, api_router, websocket_router

app = FastAPI(title="Smart Recruiting Assistant", description="AI-powered interview system")
app.include_router(applicant_router.router)
app.include_router(recruiter_router.router)
app.include_router(auth_router.router)
app.include_router(api_router.router)
app.include_router(websocket_router.router)
@app.get('/')
async def home():
    return "Smart Recruiting Assistant"