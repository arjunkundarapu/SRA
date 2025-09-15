from fastapi import FastAPI
from .routers import applicant_router,recruiter_router,auth_router,api_router

app = FastAPI()
app.include_router(applicant_router.router)
app.include_router(recruiter_router.router)
# app.include_router(auth_router.router)
app.include_router(api_router.router)
@app.get('/')
async def home():
    return "Smart Recruiting Assistant"