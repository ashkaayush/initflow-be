from fastapi import APIRouter, HTTPException, status, Depends
from app.models.deployment import BuildCreate, BuildStatus, DeploymentResponse
from app.auth import get_current_user
from app.models import User
from app.services.deployment_service import deployment_service

router = APIRouter()

@router.post("/build", response_model=DeploymentResponse)
async def create_build(
    build_request: BuildCreate,
    current_user: User = Depends(get_current_user)
):
    if build_request.platform.lower() not in ["ios", "android", "web", "all"]:
        raise HTTPException(status_code=400, detail="Invalid platform")
    
    build_status = await deployment_service.create_build_job(build_request.project_id, build_request.platform)
    return DeploymentResponse(message="Build job created", build=build_status)

@router.get("/builds/{build_id}", response_model=BuildStatus)
async def get_build_status(build_id: str, current_user: User = Depends(get_current_user)):
    build_status = await deployment_service.get_build_status(build_id)
    if not build_status:
        raise HTTPException(status_code=404, detail="Build not found")
    return build_status

@router.get("/deployment-guide/{platform}")
async def get_deployment_guide(platform: str, current_user: User = Depends(get_current_user)):
    guide = await deployment_service.get_deployment_guide(platform)
    return guide
