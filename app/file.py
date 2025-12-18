from fastapi import APIRouter, Depends
from typing import Dict
from app.models import FileUpdate, User
from app.auth import get_current_user
from app.services.sandbox_service import sandbox_service

router = APIRouter()

@router.get("", response_model=Dict[str, dict])
async def get_project_files(project_id: str, current_user: User = Depends(get_current_user)):
    """Retrieve full sandbox structure"""
    return await sandbox_service.get_sandbox(project_id)

@router.put("", response_model=dict)
async def update_file(project_id: str, file_data: FileUpdate, current_user: User = Depends(get_current_user)):
    """Update a file in the sandbox"""
    await sandbox_service.update_file(project_id, file_data.file_path, file_data.content)
    return {"message": "File updated successfully", "file_path": file_data.file_path}

@router.get("/file", response_model=dict)
async def get_file(project_id: str, file_path: str, current_user: User = Depends(get_current_user)):
    """Get content of a single file"""
    content = await sandbox_service.get_file(project_id, file_path)
    return {"file_path": file_path, "content": content}
