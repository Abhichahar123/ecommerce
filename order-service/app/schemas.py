from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional


class OrderCreate(BaseModel):
    product_id: int
    quantity: int

    # Validation — quantity 1 se kam nahi ho sakti
    @validator('quantity')    # before reaching database it give error if value<0
    def quantity_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        return v


class OrderResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    total_price: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True