from pydantic import BaseModel,EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    user_type: str  # "recruiter" or "applicant"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str