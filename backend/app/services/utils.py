from datetime import datetime, timezone
import uuid
from app.db.mongo import db
from app.core.config import PLANS

async def log_error(error_type: str, error_message: str, endpoint: str, user_id: str = None, stack_trace: str = None):
    """Log error to database"""
    error_doc = {
        "id": str(uuid.uuid4()),
        "error_type": error_type,
        "error_message": error_message,
        "endpoint": endpoint,
        "user_id": user_id,
        "stack_trace": stack_trace,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.error_logs.insert_one(error_doc)

def get_user_generations_limit(plan: str) -> int:
    """Get generation limit based on plan"""
    return PLANS.get(plan, PLANS["free"])["limits"]["generations_per_month"]

async def get_plans_from_db():
    """Get plans from database or defaults"""
    db_plans = await db.plans.find({"is_active": {"$ne": False}}, {"_id": 0}).to_list(100)
    if db_plans:
        return sorted(db_plans, key=lambda x: x.get('sort_order', 0))
    return [PLANS["free"], PLANS["pro"], PLANS["enterprise"]]

async def get_plan_by_id(plan_id: str):
    """Get specific plan by ID"""
    db_plan = await db.plans.find_one({"id": plan_id, "is_active": {"$ne": False}}, {"_id": 0})
    if db_plan:
        return db_plan
    return PLANS.get(plan_id)

async def validate_coupon(code: str, plan_id: str, amount: float):
    """Validate coupon code"""
    coupon = await db.coupons.find_one({"code": code.upper(), "is_active": True}, {"_id": 0})
    
    if not coupon:
        return {"valid": False, "error": "Invalid coupon code"}
    
    # Check expiry
    if coupon.get('valid_until'):
        expiry = datetime.fromisoformat(coupon['valid_until'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expiry:
            return {"valid": False, "error": "Coupon has expired"}
    
    # Check usage limit
    if coupon.get('usage_limit', -1) != -1 and coupon.get('used_count', 0) >= coupon['usage_limit']:
        return {"valid": False, "error": "Coupon usage limit reached"}
    
    # Check minimum purchase
    if amount < coupon.get('min_purchase', 0):
        return {"valid": False, "error": f"Minimum purchase amount is ₹{coupon['min_purchase']}"}
    
    # Check applicable plans
    if coupon.get('applicable_plans') and plan_id not in coupon['applicable_plans']:
        return {"valid": False, "error": "Coupon not applicable for this plan"}
    
    # Calculate discount
    if coupon['discount_type'] == 'percentage':
        discount = amount * (coupon['discount_value'] / 100)
        if coupon.get('max_discount'):
            discount = min(discount, coupon['max_discount'])
    else:
        discount = coupon['discount_value']
    
    return {
        "valid": True,
        "discount": discount,
        "coupon": coupon
    }

def format_user_response(user: dict):
    """Format user dict for API response"""
    from app.models.user import UserResponse
    
    created_at = user.get('created_at', datetime.now(timezone.utc).isoformat())
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    
    return UserResponse(
        id=user['id'],
        email=user['email'],
        name=user['name'],
        is_admin=user.get('is_admin', False),
        plan=user.get('plan', 'free'),
        plan_expiry=user.get('plan_expiry'),
        wallet_balance=user.get('wallet_balance', 0),
        referral_code=user.get('referral_code', ''),
        generations_used=user.get('generations_used', 0),
        generations_limit=user.get('generations_limit', 100),
        created_at=created_at
    )
