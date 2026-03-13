from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Regular client - respects RLS (used for normal user requests)
def get_supabase(token: str = None) -> Client:
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    if token:
        client.postgrest.auth(token)
    return client

def get_admin_supabase() -> Client:
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    client.postgrest.auth(SUPABASE_SERVICE_KEY)  # explicitly set service key
    return client
