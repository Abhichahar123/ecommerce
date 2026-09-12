from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional


class PaymentCreate(BaseModel):
    order_id: int
    amount: float
    idempotency_key: str

    # Amount validate karo — 0 ya negative nahi hona chahiye
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

    # Idempotency key validate karo — empty nahi honi chahiye
    @validator('idempotency_key')
    def key_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Idempotency key cannot be empty')
        return v.strip()


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    amount: float
    status: str
    idempotency_key: str
    failure_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True