# from fastapi import HTTPException
# from ..schemas import RegisterRequest,LoginRequest
# from ..database import supabase

# def register(email,password,user_type):
#     # Register user with Supabase Auth
#     result = supabase.auth.sign_up({
#         "email": email,
#         "password": password,
#     })
#     if result.get("error"):
#         raise HTTPException(status_code=400, detail=result["error"]["message"])
#     # Store user type in a 'profiles' table
#     user_id = result["user"]["id"]
#     supabase.table("profiles").insert({
#         "id": user_id,
#         "email": email,
#         "user_type": user_type
#     }).execute()
#     return {"message": "User registered successfully", "user_id": user_id}

# def login(email,password):
#     result = supabase.auth.sign_in_with_password({
#         "email": email,
#         "password": password,
#     })
#     if result.get("error"):
#         raise HTTPException(status_code=400, detail=result["error"]["message"])
#     return {
#         "access_token": result["session"]["access_token"],
#         "refresh_token": result["session"]["refresh_token"],
#         "user": result["user"]
#     }