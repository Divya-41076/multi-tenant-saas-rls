from fastapi import APIRouter, HTTPException, Header,Depends
from pydantic import BaseModel, EmailStr, constr
from database import get_supabase, get_admin_supabase
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()

class SignupRequest(BaseModel):
    email:EmailStr
    password:constr(min_length=5) # type: ignore
    full_name:str
    org_name:str

    class Config:
        extra ="forbid"

class LoginRequest(BaseModel):
    email:EmailStr
    password:str

class AcceptInviteRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    # invite_id: str

@router.post("/signup")
def signup(data: SignupRequest):
    # creates admin client
    authadmin = get_admin_supabase()
    # admin = get_admin_supabase()

    

    # create a user in supabase auth
    auth_response = authadmin.auth.sign_up(
        {
            "email": data.email,
            "password": data.password

        }
    )
    user = auth_response.user
    if not user:
        raise HTTPException(status_code=400, detail="Signup failed")
    
    # create organization  
    admin = get_admin_supabase() # create a new admin client for database operations  
    org = admin.table("organizations").insert(
        {
         "name": data.org_name,
         "slug": data.org_name.lower().replace(" ", "-")   
        }
    ).execute()
    org_id = org.data[0]["id"]


    # create profile..admin is first user so they get admin role
    admin.table("profiles").insert(
        {
            "id": user.id,
            "org_id": org_id,
            "full_name": data.full_name,
            "role": "admin"
        }
    ).execute()

    return {"message": "Signup successful", "user_id": user.id, "org_id": org_id}



# login

@router.post("/login")
def login(data: LoginRequest):
    # till above it recieves the request
    # then it uses the get_supabase function to create a client instance with the provided email and password.
    # create a supabase client
    client = get_supabase()

    auth_response = client.auth.sign_in_with_password({
        "email": data.email,
        "password": data.password
    })

    if not auth_response.user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return{
        "access_token": auth_response.session.access_token,
        "user_id": auth_response.user.id
    }
    # now if login successfull and credentials are valid then it return access tolen and user id to the frontend.
    # the client stores this token usually in loacl storage memory cookie


@router.get("/me")
def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    client = get_supabase(token)

    profile = client.table("profiles").select("*").single().execute()

    if not profile.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile.data


# invite
@router.post("/accept-invite")
def accept_invite(data: AcceptInviteRequest):
    admin_db = get_admin_supabase()

    # verify invite exists and is not accepted
    invite = admin_db.table("invites").select("*")\
    .eq("email", data.email)\
    .eq("accepted", False)\
    .execute()
    # .eq("id", data.invite_id)\                                             
        
 
    if not invite.data:
        raise HTTPException(status_code=404, detail="invalid or already accepted invite")
    
    invite_data = invite.data[0]

    # 2. Create user in Supabase Auth...
    authadmin = get_admin_supabase()

    auth_response = authadmin.auth.sign_up({
        "email":data.email,
        "password":data.password
    })

    user = auth_response.user
    if not user:
        raise HTTPException(status_code=400, detail="Signup failed")
    
    # 3. Create profile with the org_id from the invite and role from the invite
    admin_db.table("profiles").insert({
        "id": user.id,
        "org_id": invite_data["org_id"],
        "full_name": data.full_name,
        "role": invite_data["role"]
    }).execute()

    # 4. Mark the invite as accepted (you can also delete it)
    admin_db.table("invites")\
        .update({"accepted": True})\
        .eq("email", data.email)\
        .execute()

    return{
        "message": "successfully joined organization",
        "org_id": invite_data["org_id"],
        "role": invite_data["role"]
    }

    





