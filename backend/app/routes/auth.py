from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime, timezone, timedelta
import uuid
import random
import string

from app.core.security import hash_password, verify_password, create_access_token, require_auth
from app.db.mongo import db
from app.models.user import UserCreate, UserLogin, TokenResponse, UserResponse
from app.services.utils import format_user_response, get_user_generations_limit

router = APIRouter(prefix="/auth", tags=["auth"])

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if email exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Handle referral
    referred_by = None
    if user_data.referral_code:
        referrer = await db.users.find_one({"referral_code": user_data.referral_code.upper()})
        if referrer:
            referred_by = referrer['id']
    
    # Create user
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "is_admin": False,
        "plan": "free",
        "plan_expiry": (now + timedelta(days=30)).isoformat(),
        "wallet_balance": 0,
        "referral_code": generate_referral_code(),
        "referred_by": referred_by,
        "generations_used": 0,
        "generations_limit": get_user_generations_limit("free"),
        "created_at": now.isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create referral record
    if referred_by:
        referral_doc = {
            "id": str(uuid.uuid4()),
            "referrer_id": referred_by,
            "referee_id": user_id,
            "referee_name": user_data.name,
            "referee_email": user_data.email,
            "bonus_amount": 50,
            "bonus_given": False,
            "created_at": now.isoformat()
        }
        await db.referrals.insert_one(referral_doc)
    
    token = create_access_token(user_id)
    return TokenResponse(
        access_token=token,
        user=format_user_response(user_doc)
    )

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(user['id'])
    return TokenResponse(
        access_token=token,
        user=format_user_response(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(require_auth)):
    return format_user_response(user)
