from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# Naya product banane ke liye — client se yeh data chahiye
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0
    category: Optional[str] = None


# Product update ke liye — saare fields optional hain
# Isliye Optional — partial update allow karta hai
# Jaise sirf price update karna ho toh baaki fields bhejne ki zaroorat nahi
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    is_available: Optional[bool] = None


# Response mein client ko kya milega
class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    stock: int
    category: Optional[str]
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True