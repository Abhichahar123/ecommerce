from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# Signup ke liye user se kya data chahiye
class UserCreate(BaseModel):
    email: EmailStr        # automatically validate karta hai email format
    username: str
    password: str          # plain password — hum isse hash karenge


# Login ke liye
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Response mein user ki info (password kabhi return mat karo)
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True   # SQLAlchemy model se directly convert hone deta hai


# JWT token response
class TokenResponse(BaseModel):
    access_token: str     # actual jwt token 
    token_type: str = "bearer"


# Token ke andar jo data store hoga
class TokenData(BaseModel):
    email: Optional[str] = None