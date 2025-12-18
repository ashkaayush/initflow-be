from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict
from app.models import SpecFile, SpecFileUpdate, SpecVersion, SpecRollback, User
from app.auth import get_current_user
from app.database import get_supabase
import uuid
from datetime import datetime

router = APIRouter()

# --- GET latest spec file ---
@router.get("/{file_type}", response_model=SpecFile)
async def get_spec_file(
    project_id: str,
    file_type: str,
    current_user: User = Depends(get_current_user)
):
    supabase = get_supabase()
    response = supabase.table("spec_files")\
        .select("*")\
        .eq("project_id", project_id)\
        .eq("file_type", file_type)\
        .order("version", desc=True)\
        .limit(1)\
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Spec file not found")
    
    return SpecFile(**response.data[0])


# --- UPDATE spec file (create new version) ---
@router.put("/{file_type}", response_model=SpecFile)
async def update_spec_file(
    project_id: str,
    file_type: str,
    spec_data: SpecFileUpdate,
    current_user: User = Depends(get_current_user)
):
    supabase = get_supabase()

    # Get latest spec file
    latest = supabase.table("spec_files")\
        .select("*")\
        .eq("project_id", project_id)\
        .eq("file_type", file_type)\
        .order("version", desc=True)\
        .limit(1)\
        .execute()
    
    if not latest.data:
        raise HTTPException(status_code=404, detail="Spec file not found")

    current_spec = latest.data[0]

    # --- Save current version to spec_versions ---
    version_id = str(uuid.uuid4())
    version_data = {
        "id": version_id,
        "spec_file_id": current_spec["id"],
        "version": current_spec["version"],
        "content": current_spec["content"],
        "changes_summary": "Updated via editor",
        "created_by": current_user.id,
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("spec_versions").insert(version_data).execute()

    # --- Update spec file with new content ---
    new_version = current_spec["version"] + 1
    update_data = {
        "content": spec_data.content,
        "version": new_version,
        "updated_at": datetime.utcnow().isoformat()
    }
    updated = supabase.table("spec_files")\
        .update(update_data)\
        .eq("id", current_spec["id"])\
        .execute()

    # --- Update sandbox file structure ---
    await update_sandbox_files(project_id, file_type, spec_data.content)

    return SpecFile(**updated.data[0])


# --- GET version history ---
@router.get("/{file_type}/versions", response_model=List[SpecVersion])
async def get_spec_versions(
    project_id: str,
    file_type: str,
    current_user: User = Depends(get_current_user)
):
    supabase = get_supabase()
    spec = supabase.table("spec_files")\
        .select("id")\
        .eq("project_id", project_id)\
        .eq("file_type", file_type)\
        .limit(1)\
        .execute()
    
    if not spec.data:
        return []
    
    spec_file_id = spec.data[0]["id"]
    versions = supabase.table("spec_versions")\
        .select("*")\
        .eq("spec_file_id", spec_file_id)\
        .order("version", desc=True)\
        .execute()
    
    return [SpecVersion(**v) for v in versions.data]


# --- ROLLBACK spec file ---
@router.post("/{file_type}/rollback", response_model=SpecFile)
async def rollback_spec(
    project_id: str,
    file_type: str,
    rollback_data: SpecRollback,
    current_user: User = Depends(get_current_user)
):
    supabase = get_supabase()
    
    # Get version to rollback to
    version_resp = supabase.table("spec_versions")\
        .select("*")\
        .eq("id", rollback_data.version_id)\
        .execute()
    
    if not version_resp.data:
        raise HTTPException(status_code=404, detail="Version not found")
    
    target_version = version_resp.data[0]
    
    # Get current spec file
    spec_resp = supabase.table("spec_files")\
        .select("*")\
        .eq("id", target_version["spec_file_id"])\
        .execute()
    
    if not spec_resp.data:
        raise HTTPException(status_code=404, detail="Spec file not found")
    
    current_spec = spec_resp.data[0]

    # Save current spec as new version before rollback
    history_id = str(uuid.uuid4())
    history_data = {
        "id": history_id,
        "spec_file_id": current_spec["id"],
        "version": current_spec["version"],
        "content": current_spec["content"],
        "changes_summary": f"Before rollback to version {target_version['version']}",
        "created_by": current_user.id,
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("spec_versions").insert(history_data).execute()
    
    # Apply rollback
    new_version = current_spec["version"] + 1
    update_data = {
        "content": target_version["content"],
        "version": new_version,
        "updated_at": datetime.utcnow().isoformat()
    }
    updated = supabase.table("spec_files")\
        .update(update_data)\
        .eq("id", current_spec["id"])\
        .execute()

    # Update sandbox file structure after rollback
    await update_sandbox_files(project_id, file_type, target_version["content"])

    return SpecFile(**updated.data[0])


# --- Helper function: update sandbox files ---
async def update_sandbox_files(project_id: str, file_type: str, content: str):
    """
    Update the E2B sandbox file structure based on spec content.
    For simplicity, we map spec content directly to App.js or other files.
    """
    from app.services.sandbox_service import sandbox_service

    sandbox = await sandbox_service.get_sandbox(project_id)
    if not sandbox:
        sandbox = await sandbox_service.create_sandbox(project_id)
    
    # Simple mapping example: content of spec -> App.js
    if file_type == "app":
        sandbox["App.js"]["content"] = content
    elif file_type == "login":
        sandbox["screens"]["LoginScreen.js"]["content"] = content
    elif file_type == "button":
        sandbox["components"]["Button.js"]["content"] = content
    
    await sandbox_service.update_sandbox(project_id, sandbox)
