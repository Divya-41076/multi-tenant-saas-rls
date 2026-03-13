from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from database import get_supabase
from typing import Optional
from jose import jwt as jose_jwt

router = APIRouter()
security = HTTPBearer()

class TaskRequest(BaseModel):
    title:str
    description: Optional[str] = None
    project_id:str
    assigned_to: Optional[str] = None

class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None 
    assigned_to: Optional[str] = None
    status: Optional[str] = None


@router.get("/")#we did smtg called as filtering and asking specific task
def get_tasks(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials
    client = get_supabase(token)

    query = client.table("tasks").select("*").order("created_at", desc = True).limit(limit).offset(offset)

    if project_id:
        query = query.eq("project_id", project_id)

    if status:
        query = query.eq("status", status)

    if assigned_to:
        query = query.eq("assigned_to", assigned_to)

    tasks = query.execute()

    return {
        "tasks": tasks.data,
        "limit": limit,

        "offset": offset
    }

@router.get("/{task_id}/history")
def get_task_history(
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    client = get_supabase(token)

    logs = client.table("audit_logs")\
        .select("user_id, action, old_data, new_data, created_at")\
        .eq("table_name", "tasks")\
        .eq("record_id", task_id)\
        .order("created_at", desc=True)\
        .execute()

    return {
        "task_id": task_id,
        "history": logs.data
    }

@router.post("/")
def create_task(
    data: TaskRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials
    client = get_supabase(token)

    # get the current user profile

    payload = jose_jwt.get_unverified_claims(token)
    user_id = payload.get("sub")
    profile = client.table("profiles").select("*").eq("id", user_id).single().execute()
    # profile = client.table("profiles").select("*").single().execute()

    if not profile.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    

    # now verify the project id belongs to the user's organization rls will handle this
    
    project = client.table("projects").select("id").eq("id", data.project_id).single().execute()

    if not project.data:
        raise HTTPException(status_code=404, detail="Project not found or access denied")

    task = client.table("tasks").insert({
        "title": data.title,
        "description": data.description,
        "project_id": data.project_id,
        "org_id": profile.data["org_id"],

        "assigned_to": data.assigned_to,
        "created_by": profile.data["id"],
        "status": "todo"#initially it is to-do
    }).execute()

    return task.data[0]

@router.patch("/{task_id}")
def update_task(
    task_id:str,
    data: TaskUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials
    client = get_supabase(token)

    # always esure task exists and belongs to the user's org which rls will handle

    existing = client.table("tasks").select("id").eq("id", task_id).execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail = "Task not found")

    # update the task wit provided data or the fields tht must be updated
    update_data = {k:v for k, v in data.dict().items() if v is not None}
    #  so we will consider only those fields whch are not none otheriwise none fields will overwrite the exisiting data in database

    # now we need to validate the status 
    if "status" in update_data:
        if update_data["status"] not in ["todo", "in_progress", "done"]:
            raise HTTPException(status_code=400, detail="Invalid status value. must be todo, in_progress or done")
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")

    # Now lets update it in the database
    task = client.table("tasks").update(update_data)\
        .eq("id", task_id).execute()

    return task.data[0]



@router.delete("/{task_id}")
def delete_task(
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    client = get_supabase(token)

    existing = client.table("tasks")\
        .select("id")\
        .eq("id", task_id)\
        .execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Task not found")

    client.table("tasks")\
        .delete()\
        .eq("id", task_id)\
        .execute()

    return {"message": "Task deleted successfully"}


