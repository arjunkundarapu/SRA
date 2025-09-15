from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY environment variable is required")
if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_KEY environment variable is required")

print(SUPABASE_URL)

# Regular client for normal operations (with RLS)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Service role client for administrative operations (bypasses RLS)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# async def get_client() -> Client:
#     create_client(SUPABASE_URL, SUPABASE_KEY)