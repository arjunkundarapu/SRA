# from fastapi import APIRouter,HTTPException,status,Body
# from ..schemas import RegisterRequest,LoginRequest
# from ..database import supabase
# from ..services import auth_service

# router = APIRouter(prefix="/auth",tags=["auth"])

# @router.post("/register")
# async def register(data: RegisterRequest):
#     return auth_service.register(data.email,data.password,data.user_type)

# @router.post("/login")
# async def login(data: LoginRequest):
#     return auth_service.login(data.email,data.password)