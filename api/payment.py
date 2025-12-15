from fastapi import APIRouter, HTTPException, status, Depends
from app.models.payment import PaymentRequest, PaymentResponse, PaymentVerifyRequest
from app.models import User
from app.auth import get_current_user
import uuid
from datetime import datetime

router = APIRouter()

# Mock database for payments
PAYMENTS_DB = {}

# --- Initialize Payment ---
@router.post("/polar/initiate", response_model=PaymentResponse)
async def initiate_payment(payment: PaymentRequest, current_user: User = Depends(get_current_user)):
    """
    Initialize a payment via Polar for a specific project
    """
    payment_id = str(uuid.uuid4())
    PAYMENTS_DB[payment_id] = {
        "project_id": payment.project_id,
        "status": "pending",
        "amount": payment.amount,
        "currency": payment.currency,
        "description": payment.description,
        "created_at": datetime.utcnow()
    }
    
    return PaymentResponse(
        payment_id=payment_id,
        project_id=payment.project_id,
        status="pending",
        amount=payment.amount,
        currency=payment.currency,
        message="Payment initialized. Awaiting completion."
    )

# --- Verify Payment ---
@router.post("/polar/verify", response_model=PaymentResponse)
async def verify_payment(verify_request: PaymentVerifyRequest, current_user: User = Depends(get_current_user)):
    """
    Verify the status of a Polar payment
    """
    payment = PAYMENTS_DB.get(verify_request.payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    # Mock logic: randomly mark as completed if pending
    if payment["status"] == "pending":
        payment["status"] = "completed"
    
    return PaymentResponse(
        payment_id=verify_request.payment_id,
        project_id=payment["project_id"],
        status=payment["status"],
        amount=payment["amount"],
        currency=payment["currency"],
        message=f"Payment {payment['status']}"
    )
