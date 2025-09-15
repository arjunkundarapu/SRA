from fastapi import HTTPException
from ..schemas import RegisterRequest,LoginRequest
from ..database import supabase, supabase_admin

async def register(email,password,user_type):
    try:
        # Validate user_type
        if user_type not in ["recruiter", "applicant"]:
            raise HTTPException(status_code=400, detail="user_type must be 'recruiter' or 'applicant'")
        
        # Register user with Supabase Auth
        result = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
        
        if hasattr(result, 'user') and result.user:
            user_id = result.user.id
            
            # Use service_role client for inserting into profiles table
            # This bypasses RLS policies during registration
            try:
                profile_result = supabase_admin.table("profiles").insert({
                    "id": user_id,
                    "email": email,
                    "user_type": user_type
                }).execute()
                
                return {"message": "User registered successfully", "user_id": user_id}
            except Exception as profile_error:
                # If profile creation fails, we should clean up the auth user
                # Note: This requires admin privileges which might not be available
                raise HTTPException(
                    status_code=400, 
                    detail=f"Profile creation failed: {str(profile_error)}. Please check database schema."
                )
        else:
            raise HTTPException(status_code=400, detail="Registration failed - no user created")
            
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except Exception as e:
        # More detailed error handling
        error_msg = str(e)
        if "row-level security" in error_msg.lower():
            raise HTTPException(
                status_code=500, 
                detail="Database security policy error. Please contact administrator to configure RLS policies."
            )
        elif "Email address" in error_msg and "invalid" in error_msg:
            raise HTTPException(status_code=400, detail=f"Email validation failed: {error_msg}")
        elif "email" in error_msg.lower():
            raise HTTPException(status_code=400, detail=f"Email error: {error_msg}")
        else:
            raise HTTPException(status_code=400, detail=f"Registration error: {error_msg}")

async def login(email,password):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        if hasattr(result, 'session') and result.session:
            return {
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
                "user": result.user
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Login failed")