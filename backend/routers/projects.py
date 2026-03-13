from fastapi import APIRouter,HTTPException,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from database import get_supabase
from typing import Optional
from jose import jwt as jose_jwt

router = APIRouter()
security = HTTPBearer()

class ProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None

@router.get('/') #we already have a prefix saved in the main.py file when we register the router in the main.py file
def get_projects(
    limit: int = 10, #how many records to return 
    offset:int = 0, #how many records to skip for pagination
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    client = get_supabase(token) #this will create sup client and runs queries as authenticated user based on the token provided in the request header

    projects = client.table("projects")\
    .select("*")\
    .order("created_at", desc=True)\
    .limit(limit)\
    .offset(offset)\
    .execute()
    
    return{
        "projects": projects.data,
        "limit": limit,
        "offset": offset
    }

@router.get("/{project_id}/stats")
def get_project_stats(
    project_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    client = get_supabase(token)

    tasks = client.table("tasks")\
        .select("status")\
        .eq("project_id", project_id)\
        .execute()

    task_list = tasks.data

    stats = {
        "todo": 0,
        "in_progress": 0,
        "done": 0
    }

    for task in task_list:
        status = task["status"]
        if status in stats:
            stats[status] += 1

    return {
        "project_id": project_id,
        "total_tasks": len(task_list),
        "todo": stats["todo"],
        "in_progress": stats["in_progress"],
        "done": stats["done"]
    }

@router.post('/')
def create_project(
    data:ProjectRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials
    client = get_supabase(token)

    payload = jose_jwt.get_unverified_claims(token)
    user_id = payload.get("sub")
    profile = client.table("profiles").select("*").eq("id", user_id).single().execute()

    
    # profile = client.table("profiles").select("*").single().execute()
    
    if not profile.data:
            raise HTTPException(status_code=404, detail ="Profile not found")
    # always enusre the profile is verified and u get that.. and we will access the org id and other data throigh this profile data


    project = client.table("projects").insert({
            "name": data.name,
            "description":data.description,
            "org_id": profile.data["org_id"],
            "created_by": profile.data["id"]
    }).execute()

    return{
        "message": "project created successfully",
        "project_id": project.data[0]["id"] #it ll give the first row of the list of projects created
    }
        
@router.get("/{project_id}")
def get_project(
     project_id:str,
     credentials: HTTPAuthorizationCredentials = Depends(security)):
    
     token = credentials.credentials
     client = get_supabase(token)

     project = client.table("projects").select("*").eq("id",project_id).single().execute()

     if not project.data:
        raise HTTPException(status_code=404, detail="Project not found")
     
     return project.data

@router.delete("/{project_id}")
def delete_project(
    project_id:str,
    credentials: HTTPAuthorizationCredentials = Depends(security)):
     
    token = credentials.credentials
    client = get_supabase(token)
    
    existing = client.table("projects")\
        .select("id")\
        .eq("id", project_id)\
        .execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Project not found")

    client.table("projects")\
        .delete()\
        .eq("id", project_id)\
        .execute()

    return {"message": "Project deleted successfully"}


