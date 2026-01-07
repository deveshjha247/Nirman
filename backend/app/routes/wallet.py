"""
Wallet Routes - Full Wallet System
Nirman AI - Credits, Payments, Transactions, Withdrawals
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
from typing import Optional
import uuid
import os

from app.core.security import require_auth
from app.db.mongo import db
from app.models.wallet import AddMoneyRequest
from app.services.payments import create_cashfree_order, verify_cashfree_payment
from app.core.config import CASHFREE_APP_ID, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

router = APIRouter(tags=["wallet"])


# =============================================================================
# WALLET BALANCE & TRANSACTIONS
# =============================================================================

@router.get("/wallet")
async def get_wallet(user: dict = Depends(require_auth)):
    """Get wallet balance and recent transactions"""
    transactions = await db.wallet_transactions.find(
        {"user_id": user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Calculate stats
    total_credits = sum(t['amount'] for t in transactions if t.get('type') == 'credit')
    total_debits = sum(t['amount'] for t in transactions if t.get('type') == 'debit')
    pending_withdrawals = await db.withdrawals.count_documents({
        "user_id": user['id'],
        "status": "pending"
    })
    
    return {
        "balance": user.get('wallet_balance', 0),
        "transactions": transactions[:50],
        "stats": {
            "total_credited": total_credits,
            "total_spent": total_debits,
            "transaction_count": len(transactions),
            "pending_withdrawals": pending_withdrawals
        }
    }


@router.get("/wallet/transactions")
async def get_transactions(
    type: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    user: dict = Depends(require_auth)
):
    """Get paginated transactions with filters"""
    query = {"user_id": user['id']}
    if type:
        query["type"] = type
    
    transactions = await db.wallet_transactions.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    
    total = await db.wallet_transactions.count_documents(query)
    
    return {
        "transactions": transactions,
        "total": total,
        "offset": offset,
        "limit": limit
    }


# =============================================================================
# ADD MONEY
# =============================================================================

@router.post("/wallet/add")
async def add_money_to_wallet(
    request: AddMoneyRequest, 
    payment_method: str = Query("auto", description="razorpay, cashfree, or auto"),
    user: dict = Depends(require_auth)
):
    """Add money to wallet via Razorpay or Cashfree"""
    if request.amount < 10:
        raise HTTPException(status_code=400, detail="Minimum amount is ₹10")
    if request.amount > 100000:
        raise HTTPException(status_code=400, detail="Maximum amount is ₹1,00,000")
    
    order_id = f"wallet_{user['id']}_{int(datetime.now(timezone.utc).timestamp())}_{int(request.amount)}"
    now = datetime.now(timezone.utc)
    
    # Check available payment gateways
    razorpay_available = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
    cashfree_available = bool(CASHFREE_APP_ID)
    
    # Auto-select payment method
    if payment_method == "auto":
        if razorpay_available:
            payment_method = "razorpay"
        elif cashfree_available:
            payment_method = "cashfree"
        else:
            payment_method = "demo"
    
    # Demo mode - directly credit wallet
    if payment_method == "demo" or (not razorpay_available and not cashfree_available):
        new_balance = user.get('wallet_balance', 0) + request.amount
        
        await db.users.update_one(
            {"id": user['id']},
            {"$set": {"wallet_balance": new_balance}}
        )
        
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": user['id'],
            "amount": request.amount,
            "type": "credit",
            "category": "recharge",
            "description": "Wallet recharge (Demo Mode)",
            "payment_method": "demo",
            "payment_id": order_id,
            "status": "completed",
            "created_at": now.isoformat()
        }
        await db.wallet_transactions.insert_one(transaction)
        
        return {
            "status": "success",
            "demo_mode": True,
            "message": "Demo mode: Money added directly to wallet",
            "new_balance": new_balance,
            "transaction_id": transaction["id"]
        }
    
    # Razorpay order creation
    if payment_method == "razorpay":
        import httpx
        import base64
        
        auth_string = f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}"
        auth_header = base64.b64encode(auth_string.encode()).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.razorpay.com/v1/orders",
                json={
                    "amount": int(request.amount * 100),
                    "currency": "INR",
                    "receipt": order_id,
                    "notes": {
                        "user_id": user['id'],
                        "purpose": "wallet_recharge"
                    }
                },
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to create Razorpay order")
            
            order_data = response.json()
        
        # Store pending order
        await db.pending_orders.insert_one({
            "order_id": order_data['id'],
            "internal_order_id": order_id,
            "user_id": user['id'],
            "amount": request.amount,
            "payment_method": "razorpay",
            "status": "pending",
            "created_at": now.isoformat()
        })
        
        return {
            "status": "order_created",
            "payment_method": "razorpay",
            "order_id": order_data['id'],
            "amount": request.amount,
            "key_id": RAZORPAY_KEY_ID,
            "currency": "INR",
            "name": "Nirman AI",
            "description": f"Add ₹{request.amount} to wallet",
            "prefill": {
                "email": user.get('email', ''),
                "name": user.get('name', '')
            }
        }
    
    # Cashfree order creation
    if payment_method == "cashfree":
        order_response = await create_cashfree_order(
            order_id=order_id,
            amount=request.amount,
            customer_id=user['id'],
            customer_email=user['email']
        )
        
        if order_response.get('demo_mode'):
            return order_response
        
        await db.pending_orders.insert_one({
            "order_id": order_id,
            "user_id": user['id'],
            "amount": request.amount,
            "payment_method": "cashfree",
            "status": "pending",
            "created_at": now.isoformat()
        })
        
        return {
            "status": "order_created",
            "payment_method": "cashfree",
            "order_id": order_id,
            "payment_session_id": order_response.get('payment_session_id'),
            "order_details": order_response
        }
    
    raise HTTPException(status_code=400, detail="Invalid payment method")


# =============================================================================
# VERIFY PAYMENT
# =============================================================================

@router.post("/wallet/verify-razorpay")
async def verify_razorpay_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    user: dict = Depends(require_auth)
):
    """Verify Razorpay payment and credit wallet"""
    import hmac
    import hashlib
    
    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if expected_signature != razorpay_signature:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    
    pending_order = await db.pending_orders.find_one({
        "order_id": razorpay_order_id,
        "user_id": user['id'],
        "status": "pending"
    })
    
    if not pending_order:
        raise HTTPException(status_code=404, detail="Order not found or already processed")
    
    amount = pending_order['amount']
    now = datetime.now(timezone.utc)
    
    new_balance = user.get('wallet_balance', 0) + amount
    
    await db.users.update_one(
        {"id": user['id']},
        {"$set": {"wallet_balance": new_balance}}
    )
    
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user['id'],
        "amount": amount,
        "type": "credit",
        "category": "recharge",
        "description": f"Wallet recharge via Razorpay",
        "payment_method": "razorpay",
        "payment_id": razorpay_payment_id,
        "order_id": razorpay_order_id,
        "status": "completed",
        "created_at": now.isoformat()
    }
    await db.wallet_transactions.insert_one(transaction)
    
    await db.pending_orders.update_one(
        {"order_id": razorpay_order_id},
        {"$set": {"status": "completed", "payment_id": razorpay_payment_id}}
    )
    
    return {
        "status": "success",
        "message": "Payment verified and wallet credited",
        "new_balance": new_balance,
        "amount_added": amount,
        "transaction_id": transaction["id"]
    }


@router.post("/wallet/verify-cashfree")
async def verify_cashfree_wallet_payment(
    order_id: str,
    user: dict = Depends(require_auth)
):
    """Verify Cashfree payment and credit wallet"""
    payment_status = await verify_cashfree_payment(order_id)
    
    if payment_status.get('order_status') == 'PAID' or payment_status.get('demo_mode'):
        pending_order = await db.pending_orders.find_one({
            "order_id": order_id,
            "user_id": user['id']
        })
        
        if pending_order and pending_order.get('status') == 'completed':
            return {"status": "already_processed", "message": "Payment already credited"}
        
        try:
            amount = float(order_id.split('_')[-1])
        except:
            amount = pending_order.get('amount', 0) if pending_order else 0
        
        now = datetime.now(timezone.utc)
        new_balance = user.get('wallet_balance', 0) + amount
        
        await db.users.update_one(
            {"id": user['id']},
            {"$set": {"wallet_balance": new_balance}}
        )
        
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": user['id'],
            "amount": amount,
            "type": "credit",
            "category": "recharge",
            "description": "Wallet recharge via Cashfree",
            "payment_method": "cashfree",
            "payment_id": order_id,
            "status": "completed",
            "created_at": now.isoformat()
        }
        await db.wallet_transactions.insert_one(transaction)
        
        if pending_order:
            await db.pending_orders.update_one(
                {"order_id": order_id},
                {"$set": {"status": "completed"}}
            )
        
        return {
            "status": "success",
            "new_balance": new_balance,
            "amount_added": amount
        }
    
    return {"status": "pending", "payment_status": payment_status}


@router.post("/wallet/verify-payment")
async def verify_wallet_payment(order_id: str, user: dict = Depends(require_auth)):
    """Legacy verify endpoint"""
    return await verify_cashfree_wallet_payment(order_id, user)


# =============================================================================
# INTERNAL WALLET FUNCTIONS
# =============================================================================

async def deduct_from_wallet(
    user_id: str, 
    amount: float, 
    description: str,
    category: str = "usage"
) -> dict:
    """Deduct amount from user wallet"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_balance = user.get('wallet_balance', 0)
    if current_balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")
    
    new_balance = current_balance - amount
    now = datetime.now(timezone.utc)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"wallet_balance": new_balance}}
    )
    
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "amount": amount,
        "type": "debit",
        "category": category,
        "description": description,
        "status": "completed",
        "created_at": now.isoformat()
    }
    await db.wallet_transactions.insert_one(transaction)
    
    return {"new_balance": new_balance, "transaction_id": transaction["id"]}


async def credit_to_wallet(
    user_id: str,
    amount: float,
    description: str,
    category: str = "bonus"
) -> dict:
    """Credit amount to user wallet"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_balance = user.get('wallet_balance', 0) + amount
    now = datetime.now(timezone.utc)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"wallet_balance": new_balance}}
    )
    
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "amount": amount,
        "type": "credit",
        "category": category,
        "description": description,
        "status": "completed",
        "created_at": now.isoformat()
    }
    await db.wallet_transactions.insert_one(transaction)
    
    return {"new_balance": new_balance, "transaction_id": transaction["id"]}


# =============================================================================
# WITHDRAWAL REQUESTS
# =============================================================================

@router.post("/wallet/withdraw")
async def request_withdrawal(
    amount: float,
    bank_account: str,
    ifsc_code: str,
    account_holder: str,
    upi_id: str = None,
    user: dict = Depends(require_auth)
):
    """Request wallet withdrawal to bank account or UPI"""
    if amount < 100:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is ₹100")
    
    current_balance = user.get('wallet_balance', 0)
    if current_balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    pending = await db.withdrawals.count_documents({
        "user_id": user['id'],
        "status": "pending"
    })
    if pending > 0:
        raise HTTPException(status_code=400, detail="You have a pending withdrawal request")
    
    now = datetime.now(timezone.utc)
    
    new_balance = current_balance - amount
    await db.users.update_one(
        {"id": user['id']},
        {"$set": {"wallet_balance": new_balance}}
    )
    
    withdrawal = {
        "id": str(uuid.uuid4()),
        "user_id": user['id'],
        "amount": amount,
        "bank_account": bank_account[-4:].rjust(len(bank_account), '*'),
        "bank_account_full": bank_account,
        "ifsc_code": ifsc_code,
        "account_holder": account_holder,
        "upi_id": upi_id,
        "status": "pending",
        "created_at": now.isoformat()
    }
    await db.withdrawals.insert_one(withdrawal)
    
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user['id'],
        "amount": amount,
        "type": "debit",
        "category": "withdrawal",
        "description": f"Withdrawal request to {bank_account[-4:]}",
        "withdrawal_id": withdrawal["id"],
        "status": "pending",
        "created_at": now.isoformat()
    }
    await db.wallet_transactions.insert_one(transaction)
    
    return {
        "status": "success",
        "message": "Withdrawal request submitted. Processing within 3-5 business days.",
        "withdrawal_id": withdrawal["id"],
        "new_balance": new_balance
    }


@router.get("/wallet/withdrawals")
async def get_withdrawals(user: dict = Depends(require_auth)):
    """Get user's withdrawal history"""
    withdrawals = await db.withdrawals.find(
        {"user_id": user['id']},
        {"_id": 0, "bank_account_full": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {"withdrawals": withdrawals}


# =============================================================================
# REFERRALS
# =============================================================================

@router.get("/referrals")
async def get_referrals(user: dict = Depends(require_auth)):
    """Get user's referral info and earnings"""
    referrals = await db.referrals.find(
        {"referrer_id": user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    total_earnings = sum(r['bonus_amount'] for r in referrals if r.get('bonus_given'))
    pending_earnings = sum(r['bonus_amount'] for r in referrals if not r.get('bonus_given'))
    
    base_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    return {
        "referral_code": user.get('referral_code'),
        "referral_link": f"{base_url}/register?ref={user.get('referral_code')}",
        "total_referrals": len(referrals),
        "successful_referrals": len([r for r in referrals if r.get('bonus_given')]),
        "total_earnings": total_earnings,
        "pending_earnings": pending_earnings,
        "referrals": referrals
    }


# =============================================================================
# PAYMENT METHODS
# =============================================================================

@router.get("/wallet/payment-methods")
async def get_available_payment_methods(user: dict = Depends(require_auth)):
    """Get available payment methods"""
    razorpay_available = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
    cashfree_available = bool(CASHFREE_APP_ID)
    
    methods = []
    
    if razorpay_available:
        methods.append({
            "id": "razorpay",
            "name": "Razorpay",
            "icon": "💳",
            "description": "UPI, Cards, NetBanking, Wallets",
            "recommended": True
        })
    
    if cashfree_available:
        methods.append({
            "id": "cashfree",
            "name": "Cashfree",
            "icon": "💰",
            "description": "UPI, Cards, NetBanking",
            "recommended": not razorpay_available
        })
    
    if not methods:
        methods.append({
            "id": "demo",
            "name": "Demo Mode",
            "icon": "🎮",
            "description": "Instant credits (no real payment)",
            "recommended": True
        })
    
    return {
        "methods": methods,
        "default": methods[0]["id"] if methods else "demo"
    }


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.post("/admin/withdrawals/{withdrawal_id}/process")
async def process_withdrawal(
    withdrawal_id: str,
    action: str,
    notes: str = None,
    user: dict = Depends(require_auth)
):
    """Admin: Process withdrawal request"""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    withdrawal = await db.withdrawals.find_one({"id": withdrawal_id})
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal.get('status') != 'pending':
        raise HTTPException(status_code=400, detail="Withdrawal already processed")
    
    now = datetime.now(timezone.utc)
    
    if action == "approve":
        await db.withdrawals.update_one(
            {"id": withdrawal_id},
            {"$set": {
                "status": "completed",
                "processed_at": now.isoformat(),
                "processed_by": user['id'],
                "notes": notes
            }}
        )
        
        await db.wallet_transactions.update_one(
            {"withdrawal_id": withdrawal_id},
            {"$set": {"status": "completed"}}
        )
        
        return {"status": "success", "message": "Withdrawal approved"}
    
    elif action == "reject":
        target_user = await db.users.find_one({"id": withdrawal['user_id']})
        new_balance = target_user.get('wallet_balance', 0) + withdrawal['amount']
        
        await db.users.update_one(
            {"id": withdrawal['user_id']},
            {"$set": {"wallet_balance": new_balance}}
        )
        
        await db.withdrawals.update_one(
            {"id": withdrawal_id},
            {"$set": {
                "status": "rejected",
                "processed_at": now.isoformat(),
                "processed_by": user['id'],
                "notes": notes
            }}
        )
        
        await db.wallet_transactions.update_one(
            {"withdrawal_id": withdrawal_id},
            {"$set": {"status": "refunded"}}
        )
        
        refund_tx = {
            "id": str(uuid.uuid4()),
            "user_id": withdrawal['user_id'],
            "amount": withdrawal['amount'],
            "type": "credit",
            "category": "refund",
            "description": f"Withdrawal rejected: {notes or 'No reason provided'}",
            "status": "completed",
            "created_at": now.isoformat()
        }
        await db.wallet_transactions.insert_one(refund_tx)
        
        return {"status": "success", "message": "Withdrawal rejected and refunded"}
    
    raise HTTPException(status_code=400, detail="Invalid action")


@router.get("/admin/withdrawals")
async def get_all_withdrawals(
    status: str = None,
    user: dict = Depends(require_auth)
):
    """Admin: Get all withdrawal requests"""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if status:
        query["status"] = status
    
    withdrawals = await db.withdrawals.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    for w in withdrawals:
        user_info = await db.users.find_one(
            {"id": w['user_id']},
            {"_id": 0, "id": 1, "name": 1, "email": 1}
        )
        w['user'] = user_info
    
    return {"withdrawals": withdrawals}


@router.post("/admin/wallet/credit")
async def admin_credit_wallet(
    user_id: str,
    amount: float,
    reason: str,
    user: dict = Depends(require_auth)
):
    """Admin: Credit user wallet manually"""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await credit_to_wallet(user_id, amount, f"Admin credit: {reason}", "admin_credit")
    
    # Log admin action
    await db.admin_logs.insert_one({
        "id": str(uuid.uuid4()),
        "admin_id": user['id'],
        "action": "wallet_credit",
        "target_user_id": user_id,
        "amount": amount,
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"status": "success", "new_balance": result["new_balance"]}


@router.post("/admin/wallet/debit")
async def admin_debit_wallet(
    user_id: str,
    amount: float,
    reason: str,
    user: dict = Depends(require_auth)
):
    """Admin: Debit user wallet manually"""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await deduct_from_wallet(user_id, amount, f"Admin debit: {reason}", "admin_debit")
    
    await db.admin_logs.insert_one({
        "id": str(uuid.uuid4()),
        "admin_id": user['id'],
        "action": "wallet_debit",
        "target_user_id": user_id,
        "amount": amount,
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"status": "success", "new_balance": result["new_balance"]}
