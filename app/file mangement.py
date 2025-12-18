from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.auth import get_current_user
from app.models import User
from app.database import get_supabase
import uuid

router = APIRouter()


# --- Models ---
class FileUpdate(BaseModel):
    file_path: str
    content: str


class FileCreate(BaseModel):
    path: str
    type: str  # "file" or "directory"
    content: Optional[str] = None


class FileDelete(BaseModel):
    path: str


# --- Get entire project file structure ---
@router.get("", response_model=Dict[str, Any])
async def get_files(project_id: str, current_user: User = Depends(get_current_user)):
    """
    Retrieve the full sandbox file structure.
    """
    from app.services.sandbox_service import sandbox_service

    sandbox = await sandbox_service.get_sandbox(project_id)
    if not sandbox:
        sandbox = await sandbox_service.create_sandbox(project_id)

    return sandbox


# --- Read single file ---
@router.get("/read", response_model=Dict[str, str])
async def read_file(project_id: str, file_path: str, current_user: User = Depends(get_current_user)):
    from app.services.sandbox_service import sandbox_service

    sandbox = await sandbox_service.get_sandbox(project_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")

    # Traverse nested structure
    parts = file_path.split("/")
    node = sandbox
    for part in parts:
        if part not in node:
            raise HTTPException(status_code=404, detail=f"File {file_path} not found")
        node = node[part]
        if node.get("type") == "directory":
            node = node.get("children", {})

    return {"file_path": file_path, "content": node.get("content", "")}


# --- Update file ---
@router.put("", response_model=Dict[str, str])
async def update_file(project_id: str, file_data: FileUpdate, current_user: User = Depends(get_current_user)):
    from app.services.sandbox_service import sandbox_service

    sandbox = await sandbox_service.get_sandbox(project_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")

    # Traverse nested structure to update
    parts = file_data.file_path.split("/")
    node = sandbox
    for part in parts[:-1]:
        if part not in node or node[part]["type"] != "directory":
            raise HTTPException(status_code=404, detail=f"Directory {part} not found")
        node = node[part]["children"]

    file_name = parts[-1]
    if file_name not in node or node[file_name]["type"] != "file":
        raise HTTPException(status_code=404, detail=f"File {file_data.file_path} not found")

    node[file_name]["content"] = file_data.content

    await sandbox_service.update_sandbox(project_id, sandbox)
    return {"message": f"File {file_data.file_path} updated successfully", "file_path": file_data.file_path}


# --- Create new file or directory ---
@router.post("", response_model=Dict[str, str])
async def create_file(project_id: str, file_create: FileCreate, current_user: User = Depends(get_current_user)):
    from app.services.sandbox_service import sandbox_service

    sandbox = await sandbox_service.get_sandbox(project_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")

    parts = file_create.path.split("/")
    node = sandbox
    for part in parts[:-1]:
        if part not in node or node[part]["type"] != "directory":
            # Auto-create directories if missing
            node[part] = {"type": "directory", "children": {}}
        node = node[part]["children"]

    name = parts[-1]
    if name in node:
        raise HTTPException(status_code=400, detail=f"{file_create.type.capitalize()} already exists at {file_create.path}")

    if file_create.type == "file":
        node[name] = {"type": "file", "content": file_create.content or ""}
    else:
        node[name] = {"type": "directory", "children": {}}

    await sandbox_service.update_sandbox(project_id, sandbox)
    return {"message": f"{file_create.type.capitalize()} created successfully", "path": file_create.path}


# --- Delete file or directory ---
@router.delete("", response_model=Dict[str, str])
async def delete_file(project_id: str, file_delete: FileDelete, current_user: User = Depends(get_current_user)):
    from app.services.sandbox_service import sandbox_service

    sandbox = await sandbox_service.get_sandbox(project_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")

    parts = file_delete.path.split("/")
    node = sandbox
    for part in parts[:-1]:
        if part not in node or node[part]["type"] != "directory":
            raise HTTPException(status_code=404, detail=f"Directory {part} not found")
        node = node[part]["children"]

    name = parts[-1]
    if name not in node:
        raise HTTPException(status_code=404, detail=f"Path {file_delete.path} not found")

    del node[name]
    await sandbox_service.update_sandbox(project_id, sandbox)
    return {"message": f"Deleted {file_delete.path} successfully", "path": file_delete.path}

