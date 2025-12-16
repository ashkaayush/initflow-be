from pydantic import BaseModel
from typing import Optional

class PaymentRequest(BaseModel):
    project_id: str
    amount: float
    currency: str = "USD"
    description: Optional[str] = None

class PaymentResponse(BaseModel):
    payment_id: str
    project_id: str
    status: str
    amount: float
    currency: str
    message: str

class PaymentVerifyRequest(BaseModel):
    payment_id: str
