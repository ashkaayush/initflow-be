from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models import CodeChange, ChangeModification, User
from app.auth import get_current_user
from app.services.review_service import ReviewService

router = APIRouter()
review_service = ReviewService()

@router.get("/changes/pending", response_model=List[CodeChange])
async def get_pending_changes(project_id: str, current_user: User = Depends(get_current_user)):
    """List pending code changes"""
    changes = review_service.list_pending_changes(project_id)
    return [CodeChange(**c) for c in changes]

@router.post("/changes/{change_id}/approve")
async def approve_change(change_id: str, current_user: User = Depends(get_current_user)):
    """Approve a code change"""
    try:
        change = await review_service.approve_change(change_id, current_user)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Change approved", "change_id": change["id"]}

@router.post("/changes/{change_id}/reject")
async def reject_change(change_id: str, current_user: User = Depends(get_current_user)):
    """Reject a code change"""
    try:
        change = review_service.reject_change(change_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Change rejected", "change_id": change["id"]}

@router.post("/changes/{change_id}/modify")
async def request_modification(change_id: str, modification: ChangeModification, current_user: User = Depends(get_current_user)):
    """Request modification on a code change"""
    try:
        result = review_service.request_modification(change_id, modification.feedback, current_user)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Modification task created", **result}
