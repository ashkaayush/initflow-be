from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class BuildCreate(BaseModel):
    project_id: str
    platform: str  # "ios", "android", "web", or "all"

class BuildStatus(BaseModel):
    build_id: str
    project_id: str
    platform: str
    status: str  # "pending", "building", "success", "failed"
    logs: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class DeploymentResponse(BaseModel):
    message: str
    build: BuildStatus
