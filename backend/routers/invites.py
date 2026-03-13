from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from database import get_supabase, get_admin_supabase
from typing import Optional
from jose import jwt as jose_jwt

router = APIRouter()
security = HTTPBearer()

class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "member"

class AcceptInviteRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str




@router.post("/")
def send_invite(
    data: InviteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    client = get_supabase(token)

    payload = jose_jwt.get_unverified_claims(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get current user profile (RLS ensures they're admin)
    profile = client.table("profiles").select("*").eq("id",user_id).single().execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.data["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can send invites")

    # Check if invite already exists
    existing = client.table("invites")\
        .select("*")\
        .eq("email", data.email)\
        .execute()

    if existing.data:
        raise HTTPException(status_code=400, detail="Invite already sent to this email")

    # Create invite
    invite = client.table("invites").insert({
        "org_id": profile.data["org_id"],
        "email": data.email,
        "role": data.role,
        "invited_by": profile.data["id"]
    }).execute()

    return {
        "message": f"Invite sent to {data.email}",
        "invite": invite.data[0]
    }

@router.get("/")
def get_invites(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    client = get_supabase(token)

    invites = client.table("invites")\
        .select("*")\
        .execute()

    return {"invites": invites.data}


@router.delete("/{invite_id}")
def delete_invite(
    invite_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials
    client = get_supabase(token)

    existing = client.table("invites").select("id").eq("id", invite_id).execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Invite not found")

    client.table("invites").delete().eq("id", invite_id).execute()
    return {"message": "Invite deleted"}


 
  