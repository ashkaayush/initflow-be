from fastapi import APIRouter, Depends
from typing import Dict
from app.models import FileUpdate, User
from app.auth import get_current_user
from app.services.sandbox_service import sandbox_service

router = APIRouter()

@router.get("", response_model=Dict[str, dict])
async def get_project_files(project_id: str, current_user: User = Depends(get_current_user)):
    return await sandbox_service.get_sandbox(project_id)

@router.put("", response_model=dict)
async def update_file(project_id: str, file_data: FileUpdate, current_user: User = Depends(get_current_user)):
    await sandbox_service.update_file(project_id, file_data.file_path, file_data.content)
    return {"message": "File updated", "file_path": file_data.file_path}
