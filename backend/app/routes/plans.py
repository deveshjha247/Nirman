from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import uuid

from app.core.security import require_auth
from app.db.mongo import db
from app.models.plan import PurchasePlanRequest
from app.models.wallet import AddMoneyRequest
from app.services.utils import get_plans_from_db, get_plan_by_id, validate_coupon, get_user_generations_limit
from app.services.payments import create_cashfree_order, verify_cashfree_payment
from app.core.config import CASHFREE_APP_ID, CASHFREE_SECRET_KEY

router = APIRouter(tags=["plans"])

# ========== PLANS ==========
@router.get("/plans")
async def get_plans():
    plans = await get_plans_from_db()
    return plans

@router.post("/plans/purchase")
async def purchase_plan(request: PurchasePlanRequest, user: dict = Depends(require_auth)):
    plan = await get_plan_by_id(request.plan)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    if request.plan == "free":
        raise HTTPException(status_code=400, detail="Cannot purchase free plan")
    
    # Calculate price
    price = plan['price_yearly'] if request.billing_cycle == 'yearly' else plan['price_monthly']
    discount = 0
    coupon_data = None
    
    # Validate and apply coupon
    if request.coupon_code:
        coupon_result = await validate_coupon(request.coupon_code, request.plan, price)
        if not coupon_result['valid']:
            raise HTTPException(status_code=400, detail=coupon_result['error'])
        discount = coupon_result['discount']
        coupon_data = coupon_result['coupon']
    
    # Check for referral discount (first purchase only)
    if user.get('referred_by') and user.get('plan') == 'free':
        purchases = await db.purchases.count_documents({"user_id": user['id'], "status": "completed"})
        if purchases == 0:
            referral_discount = price * 0.1
            discount += referral_discount
    
    final_price = max(0, price - discount)
    wallet_balance = user.get('wallet_balance', 0)
    
    # Check wallet balance
    if request.use_wallet:
        if wallet_balance < final_price:
            return {
                "status": "payment_required",
                "amount": final_price - wallet_balance,
                "message": f"Insufficient wallet balance. Add ₹{final_price - wallet_balance} to proceed."
            }
        
        # Deduct from wallet and update plan
        now = datetime.now(timezone.utc)
        expiry = (now + timedelta(days=365 if request.billing_cycle == 'yearly' else 30)).isoformat()
        
        # Update user
        await db.users.update_one(
            {"id": user['id']},
            {"$set": {
                "plan": request.plan,
                "plan_expiry": expiry,
                "wallet_balance": wallet_balance - final_price,
                "generations_limit": get_user_generations_limit(request.plan),
                "generations_used": 0
            }}
        )
        
        # Record transaction
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": user['id'],
            "amount": final_price,
            "type": "debit",
            "description": f"Plan purchase: {plan['name']} ({request.billing_cycle})",
            "created_at": now.isoformat()
        }
        await db.wallet_transactions.insert_one(transaction)
        
        # Record purchase
        purchase = {
            "id": str(uuid.uuid4()),
            "user_id": user['id'],
            "user_name": user['name'],
            "user_email": user['email'],
            "plan": request.plan,
            "billing_cycle": request.billing_cycle,
            "amount": final_price,
            "original_amount": price,
            "coupon_code": request.coupon_code,
            "coupon_discount": discount,
            "status": "completed",
            "created_at": now.isoformat()
        }
        await db.purchases.insert_one(purchase)
        
        # Update coupon usage
        if coupon_data:
            await db.coupons.update_one(
                {"code": request.coupon_code.upper()},
                {"$inc": {"used_count": 1}}
            )
        
        # Give referral bonus
        if user.get('referred_by'):
            referral = await db.referrals.find_one({
                "referrer_id": user['referred_by'],
                "referee_id": user['id'],
                "bonus_given": False
            })
            if referral:
                await db.users.update_one(
                    {"id": user['referred_by']},
                    {"$inc": {"wallet_balance": referral['bonus_amount']}}
                )
                await db.referrals.update_one(
                    {"id": referral['id']},
                    {"$set": {"bonus_given": True}}
                )
                # Record referral bonus transaction
                bonus_tx = {
                    "id": str(uuid.uuid4()),
                    "user_id": user['referred_by'],
                    "amount": referral['bonus_amount'],
                    "type": "credit",
                    "description": f"Referral bonus: {user['name']} purchased a plan",
                    "created_at": now.isoformat()
                }
                await db.wallet_transactions.insert_one(bonus_tx)
        
        return {
            "status": "success",
            "message": f"Successfully upgraded to {plan['name']}",
            "discount": discount
        }
    
    return {"status": "payment_method_required"}

@router.post("/coupons/validate")
async def validate_coupon_endpoint(code: str, plan: str, amount: float, user: dict = Depends(require_auth)):
    result = await validate_coupon(code, plan, amount)
    if not result['valid']:
        raise HTTPException(status_code=400, detail=result['error'])
    return {"valid": True, "discount": result['discount']}
