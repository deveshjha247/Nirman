from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    email: EmailStr
    name: str
    password_hash: str
    is_admin: bool = False
    plan: str = "free"
    plan_expiry: Optional[str] = None
    wallet_balance: float = 0
    referral_code: str
    referred_by: Optional[str] = None
    generations_used: int = 0
    generations_limit: int = 100
    created_at: str

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    referral_code: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    is_admin: bool
    plan: str
    plan_expiry: Optional[str] = None
    wallet_balance: float
    referral_code: str
    generations_used: int
    generations_limit: int
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    plan: Optional[str] = None
    wallet_balance: Optional[float] = None
    is_admin: Optional[bool] = None
