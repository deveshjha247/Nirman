from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import uuid

from app.core.security import require_admin, require_auth
from app.db.mongo import db
from app.models.user import AdminUserUpdate
from app.models.coupon import CouponCreate, CouponUpdate
from app.models.plan import PlanCreate, PlanUpdate
from app.core.config import PLANS
from app.services.utils import get_user_generations_limit

router = APIRouter(prefix="/admin", tags=["admin"])

# ==================== AUDIT LOGGING ====================
async def create_audit_log(admin: dict, action: str, target_type: str, target_id: str, 
                           old_value: dict = None, new_value: dict = None, reason: str = None,
                           ip_address: str = None):
    """Create audit log entry"""
    audit = {
        "id": str(uuid.uuid4()),
        "admin_id": admin["id"],
        "admin_email": admin["email"],
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "old_value": old_value,
        "new_value": new_value,
        "reason": reason,
        "ip_address": ip_address,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(audit)

# ==================== DASHBOARD STATS ====================
@router.get("/stats")
async def get_admin_stats(admin: dict = Depends(require_admin)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    day_ago = now - timedelta(hours=24)
    
    # User stats
    total_users = await db.users.count_documents({})
    pro_users = await db.users.count_documents({"plan": {"$in": ["pro", "enterprise"]}})
    today_signups = await db.users.count_documents({"created_at": {"$gte": today_start.isoformat()}})
    week_signups = await db.users.count_documents({"created_at": {"$gte": week_ago.isoformat()}})
    month_signups = await db.users.count_documents({"created_at": {"$gte": month_ago.isoformat()}})
    
    # Revenue stats
    purchases = await db.purchases.find({"status": "completed"}, {"_id": 0}).to_list(10000)
    total_revenue = sum(p.get('amount', 0) for p in purchases)
    
    # MRR calculation (active pro/enterprise users)
    active_subscriptions = await db.users.find({
        "plan": {"$in": ["pro", "enterprise"]},
        "plan_expiry": {"$gte": now.isoformat()}
    }).to_list(10000)
    mrr = sum(
        PLANS.get(u.get('plan', 'free'), {}).get('price_monthly', 0) 
        for u in active_subscriptions
    )
    
    # Churn (cancelled in last 30 days)
    churned = await db.purchases.count_documents({
        "status": "cancelled",
        "created_at": {"$gte": month_ago.isoformat()}
    })
    
    # Project stats
    total_projects = await db.projects.count_documents({})
    total_deployments = await db.deployments.count_documents({})
    
    # AI Jobs stats
    ai_jobs_running = await db.jobs.count_documents({"status": "running"})
    ai_jobs_failed = await db.jobs.count_documents({"status": "failed"})
    ai_jobs_queued = await db.jobs.count_documents({"status": "queued"})
    
    # AI Usage stats (last 24h)
    ai_runs_24h = await db.ai_runs.find({"created_at": {"$gte": day_ago.isoformat()}}).to_list(10000)
    total_ai_runs = len(ai_runs_24h)
    failed_ai_runs = len([r for r in ai_runs_24h if r.get("status") == "failed"])
    ai_error_rate = (failed_ai_runs / total_ai_runs * 100) if total_ai_runs > 0 else 0
    total_ai_cost = sum(r.get('cost_estimate', 0) for r in ai_runs_24h)
    
    # Error stats (last 24h)
    errors_24h = await db.error_logs.find({"created_at": {"$gte": day_ago.isoformat()}}).to_list(1000)
    error_count = len(errors_24h)
    
    # Top errors
    error_types = {}
    for e in errors_24h:
        err_type = e.get('error_type', 'Unknown')
        error_types[err_type] = error_types.get(err_type, 0) + 1
    top_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Plan distribution
    plan_distribution = {
        "free": await db.users.count_documents({"plan": "free"}),
        "pro": await db.users.count_documents({"plan": "pro"}),
        "enterprise": await db.users.count_documents({"plan": "enterprise"})
    }
    
    # Support tickets
    open_tickets = await db.support_tickets.count_documents({"status": {"$in": ["open", "in_progress"]}})
    
    return {
        "users": {
            "total": total_users,
            "pro": pro_users,
            "today_signups": today_signups,
            "week_signups": week_signups,
            "month_signups": month_signups,
            "plan_distribution": plan_distribution
        },
        "revenue": {
            "total": total_revenue,
            "mrr": mrr,
            "churned_30d": churned
        },
        "projects": {
            "total": total_projects,
            "deployments": total_deployments
        },
        "ai_jobs": {
            "running": ai_jobs_running,
            "failed": ai_jobs_failed,
            "queued": ai_jobs_queued
        },
        "ai_usage_24h": {
            "total_runs": total_ai_runs,
            "failed_runs": failed_ai_runs,
            "error_rate": round(ai_error_rate, 2),
            "total_cost": round(total_ai_cost, 4)
        },
        "errors_24h": {
            "count": error_count,
            "top_errors": [{"type": t, "count": c} for t, c in top_errors]
        },
        "support": {
            "open_tickets": open_tickets
        }
    }

# ==================== USERS MANAGEMENT ====================
@router.get("/users")
async def get_admin_users(
    admin: dict = Depends(require_admin),
    search: str = None,
    plan: str = None,
    skip: int = 0,
    limit: int = 50
):
    query = {}
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
            {"id": search}
        ]
    if plan:
        query["plan"] = plan
    
    users = await db.users.find(
        query,
        {"_id": 0, "password_hash": 0}
    ).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with additional data
    for user in users:
        user["projects_count"] = await db.projects.count_documents({"user_id": user["id"]})
        user["deployments_count"] = await db.deployments.count_documents({"user_id": user["id"]})
        # Calculate total revenue from user
        purchases = await db.purchases.find({"user_id": user["id"], "status": "completed"}).to_list(100)
        user["total_revenue"] = sum(p.get("amount", 0) for p in purchases)
    
    return {"users": users, "total": await db.users.count_documents(query)}

@router.get("/users/{user_id}")
async def get_admin_user_detail(user_id: str, admin: dict = Depends(require_admin)):
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get related data
    user["projects"] = await db.projects.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    user["deployments"] = await db.deployments.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    user["purchases"] = await db.purchases.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    user["wallet_transactions"] = await db.wallet_transactions.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    user["ai_runs"] = await db.ai_runs.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    user["support_tickets"] = await db.support_tickets.find({"user_id": user_id}, {"_id": 0}).to_list(50)
    
    # Total revenue
    user["total_revenue"] = sum(p.get("amount", 0) for p in user["purchases"] if p.get("status") == "completed")
    
    return user

@router.put("/users/{user_id}")
async def update_admin_user(
    user_id: str,
    update_data: AdminUserUpdate,
    reason: str = None,
    request: Request = None,
    admin: dict = Depends(require_admin)
):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if 'plan' in update_dict:
        update_dict['generations_limit'] = get_user_generations_limit(update_dict['plan'])
        update_dict['generations_used'] = 0
    
    # Create audit log
    await create_audit_log(
        admin=admin,
        action="user_update",
        target_type="user",
        target_id=user_id,
        old_value={k: user.get(k) for k in update_dict.keys()},
        new_value=update_dict,
        reason=reason,
        ip_address=request.client.host if request else None
    )
    
    await db.users.update_one({"id": user_id}, {"$set": update_dict})
    return {"message": "User updated successfully"}

@router.post("/users/{user_id}/ban")
async def ban_user(user_id: str, reason: str = None, request: Request = None, admin: dict = Depends(require_admin)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one({"id": user_id}, {"$set": {"is_banned": True, "banned_reason": reason}})
    
    await create_audit_log(admin, "user_ban", "user", user_id, {"is_banned": False}, {"is_banned": True}, reason, request.client.host if request else None)
    
    return {"message": "User banned successfully"}

@router.post("/users/{user_id}/unban")
async def unban_user(user_id: str, request: Request = None, admin: dict = Depends(require_admin)):
    await db.users.update_one({"id": user_id}, {"$set": {"is_banned": False, "banned_reason": None}})
    await create_audit_log(admin, "user_unban", "user", user_id, ip_address=request.client.host if request else None)
    return {"message": "User unbanned successfully"}

@router.post("/users/{user_id}/force-logout")
async def force_logout_user(user_id: str, admin: dict = Depends(require_admin)):
    # Invalidate sessions by updating a session_version field
    await db.users.update_one({"id": user_id}, {"$inc": {"session_version": 1}})
    await create_audit_log(admin, "force_logout", "user", user_id)
    return {"message": "User sessions invalidated"}

@router.post("/users/{user_id}/reset-password")
async def trigger_password_reset(user_id: str, admin: dict = Depends(require_admin)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate reset token
    reset_token = str(uuid.uuid4())
    await db.password_resets.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "token": reset_token,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    })
    
    await create_audit_log(admin, "password_reset_triggered", "user", user_id)
    
    # In production, send email
    return {"message": "Password reset link generated", "reset_token": reset_token}

@router.post("/users/{user_id}/set-limits")
async def set_user_limits(
    user_id: str,
    max_projects: int = None,
    generations_limit: int = None,
    admin: dict = Depends(require_admin)
):
    update = {}
    if max_projects is not None:
        update["max_projects"] = max_projects
    if generations_limit is not None:
        update["generations_limit"] = generations_limit
    
    if update:
        await db.users.update_one({"id": user_id}, {"$set": update})
        await create_audit_log(admin, "set_limits", "user", user_id, new_value=update)
    
    return {"message": "User limits updated"}

@router.post("/users/{user_id}/extend-plan")
async def extend_user_plan(user_id: str, days: int = 7, admin: dict = Depends(require_admin)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_expiry = user.get("plan_expiry")
    if current_expiry:
        try:
            expiry_dt = datetime.fromisoformat(current_expiry.replace('Z', '+00:00'))
        except Exception:
            expiry_dt = datetime.now(timezone.utc)
    else:
        expiry_dt = datetime.now(timezone.utc)
    
    new_expiry = (expiry_dt + timedelta(days=days)).isoformat()
    await db.users.update_one({"id": user_id}, {"$set": {"plan_expiry": new_expiry}})
    
    await create_audit_log(admin, "extend_plan", "user", user_id, 
                          {"plan_expiry": current_expiry}, {"plan_expiry": new_expiry})
    
    return {"message": f"Plan extended by {days} days", "new_expiry": new_expiry}

# ==================== PURCHASES & BILLING ====================
@router.get("/purchases")
async def get_admin_purchases(
    admin: dict = Depends(require_admin),
    status: str = None,
    skip: int = 0,
    limit: int = 50
):
    query = {}
    if status:
        query["status"] = status
    
    purchases = await db.purchases.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"purchases": purchases, "total": await db.purchases.count_documents(query)}

@router.post("/purchases/{purchase_id}/refund")
async def refund_purchase(purchase_id: str, reason: str = None, admin: dict = Depends(require_admin)):
    purchase = await db.purchases.find_one({"id": purchase_id})
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Credit wallet
    await db.users.update_one(
        {"id": purchase["user_id"]},
        {"$inc": {"wallet_balance": purchase["amount"]}}
    )
    
    # Update purchase status
    await db.purchases.update_one({"id": purchase_id}, {"$set": {"status": "refunded", "refund_reason": reason}})
    
    # Record transaction
    await db.wallet_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": purchase["user_id"],
        "amount": purchase["amount"],
        "type": "credit",
        "description": f"Refund: {reason or 'Admin refund'}",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    await create_audit_log(admin, "refund", "purchase", purchase_id, reason=reason)
    
    return {"message": "Refund processed"}

@router.get("/invoices/export")
async def export_invoices(
    start_date: str = None,
    end_date: str = None,
    admin: dict = Depends(require_admin)
):
    query = {"status": "completed"}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    
    purchases = await db.purchases.find(query, {"_id": 0}).to_list(10000)
    
    # Format as CSV
    csv_lines = ["id,user_email,plan,billing_cycle,amount,coupon_code,coupon_discount,created_at"]
    for p in purchases:
        csv_lines.append(f"{p.get('id')},{p.get('user_email')},{p.get('plan')},{p.get('billing_cycle')},{p.get('amount')},{p.get('coupon_code','')},{p.get('coupon_discount',0)},{p.get('created_at')}")
    
    return {"csv_data": "\n".join(csv_lines), "total_records": len(purchases)}

# ==================== COUPONS ====================
@router.get("/coupons")
async def get_admin_coupons(admin: dict = Depends(require_admin)):
    coupons = await db.coupons.find({}, {"_id": 0}).to_list(100)
    return {"coupons": coupons}

@router.post("/coupons")
async def create_admin_coupon(coupon_data: CouponCreate, admin: dict = Depends(require_admin)):
    existing = await db.coupons.find_one({"code": coupon_data.code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Coupon code already exists")
    
    now = datetime.now(timezone.utc)
    coupon_doc = {
        "id": str(uuid.uuid4()),
        "code": coupon_data.code.upper(),
        "discount_type": coupon_data.discount_type,
        "discount_value": coupon_data.discount_value,
        "min_purchase": coupon_data.min_purchase,
        "max_discount": coupon_data.max_discount,
        "valid_from": now.isoformat(),
        "valid_until": coupon_data.valid_until,
        "usage_limit": coupon_data.usage_limit,
        "used_count": 0,
        "applicable_plans": coupon_data.applicable_plans,
        "is_active": coupon_data.is_active,
        "created_at": now.isoformat()
    }
    
    await db.coupons.insert_one(coupon_doc)
    await create_audit_log(admin, "coupon_create", "coupon", coupon_doc["id"])
    return {"message": "Coupon created", "coupon": coupon_doc}

@router.put("/coupons/{coupon_id}")
async def update_admin_coupon(coupon_id: str, update_data: CouponUpdate, admin: dict = Depends(require_admin)):
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if 'code' in update_dict:
        update_dict['code'] = update_dict['code'].upper()
    
    result = await db.coupons.update_one({"id": coupon_id}, {"$set": update_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    await create_audit_log(admin, "coupon_update", "coupon", coupon_id, new_value=update_dict)
    return {"message": "Coupon updated"}

@router.delete("/coupons/{coupon_id}")
async def delete_admin_coupon(coupon_id: str, admin: dict = Depends(require_admin)):
    result = await db.coupons.delete_one({"id": coupon_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Coupon not found")
    await create_audit_log(admin, "coupon_delete", "coupon", coupon_id)
    return {"message": "Coupon deleted"}

# ==================== PLANS ====================
@router.get("/plans")
async def get_admin_plans(admin: dict = Depends(require_admin)):
    db_plans = await db.plans.find({}, {"_id": 0}).to_list(100)
    
    all_plans = []
    default_ids = set()
    
    for plan in db_plans:
        all_plans.append(plan)
        default_ids.add(plan['id'])
    
    for plan_id, plan_data in PLANS.items():
        if plan_id not in default_ids:
            plan_copy = {**plan_data, "from_default": True}
            all_plans.append(plan_copy)
    
    return {"plans": sorted(all_plans, key=lambda x: x.get('sort_order', 0))}

@router.post("/plans")
async def create_admin_plan(plan_data: PlanCreate, admin: dict = Depends(require_admin)):
    existing = await db.plans.find_one({"id": plan_data.id})
    if existing:
        raise HTTPException(status_code=400, detail="Plan ID already exists")
    
    plan_doc = {
        "id": plan_data.id,
        "name": plan_data.name,
        "price_monthly": plan_data.price_monthly,
        "price_yearly": plan_data.price_yearly,
        "features": plan_data.features,
        "limits": plan_data.limits,
        "is_active": plan_data.is_active,
        "sort_order": plan_data.sort_order,
        "from_default": False
    }
    
    await db.plans.insert_one(plan_doc)
    await create_audit_log(admin, "plan_create", "plan", plan_doc["id"])
    return {"message": "Plan created", "plan": plan_doc}

@router.put("/plans/{plan_id}")
async def update_admin_plan(plan_id: str, update_data: PlanUpdate, admin: dict = Depends(require_admin)):
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    existing = await db.plans.find_one({"id": plan_id})
    
    if existing:
        await db.plans.update_one({"id": plan_id}, {"$set": update_dict})
    elif plan_id in PLANS:
        plan_doc = {**PLANS[plan_id], **update_dict, "from_default": True}
        await db.plans.insert_one(plan_doc)
    else:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    await create_audit_log(admin, "plan_update", "plan", plan_id, new_value=update_dict)
    return {"message": "Plan updated"}

# ==================== AI USAGE & COSTS ====================
@router.get("/ai-usage")
async def get_ai_usage(
    admin: dict = Depends(require_admin),
    provider: str = None,
    start_date: str = None,
    skip: int = 0,
    limit: int = 100
):
    query = {}
    if provider:
        query["provider"] = provider
    if start_date:
        query["created_at"] = {"$gte": start_date}
    
    runs = await db.ai_runs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Aggregate stats
    all_runs = await db.ai_runs.find(query, {"_id": 0}).to_list(100000)
    
    by_provider = {}
    by_model = {}
    total_cost = 0
    total_tokens = 0
    success_count = 0
    fail_count = 0
    byo_count = 0
    
    for r in all_runs:
        prov = r.get("provider", "unknown")
        model = r.get("model", "unknown")
        
        by_provider[prov] = by_provider.get(prov, 0) + 1
        by_model[model] = by_model.get(model, 0) + 1
        
        total_cost += r.get("cost_estimate", 0)
        total_tokens += r.get("tokens_in", 0) + r.get("tokens_out", 0)
        
        if r.get("status") == "success":
            success_count += 1
        else:
            fail_count += 1
        
        if r.get("is_byo_key"):
            byo_count += 1
    
    return {
        "runs": runs,
        "total": len(all_runs),
        "stats": {
            "by_provider": by_provider,
            "by_model": by_model,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "success_count": success_count,
            "fail_count": fail_count,
            "byo_key_count": byo_count
        }
    }

@router.get("/ai-providers")
async def get_ai_providers(admin: dict = Depends(require_admin)):
    providers = await db.ai_provider_configs.find({}, {"_id": 0}).to_list(100)
    
    # Default providers if not in DB
    default_providers = ["openai", "gemini", "claude"]
    existing_providers = {p["provider"] for p in providers}
    
    for prov in default_providers:
        if prov not in existing_providers:
            providers.append({
                "provider": prov,
                "is_enabled": True,
                "is_default": prov == "openai",
                "health_status": "healthy",
                "is_blocked": False
            })
    
    return {"providers": providers}

@router.put("/ai-providers/{provider}")
async def update_ai_provider(
    provider: str,
    is_enabled: bool = None,
    is_default: bool = None,
    is_blocked: bool = None,
    block_reason: str = None,
    admin: dict = Depends(require_admin)
):
    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if is_enabled is not None:
        update["is_enabled"] = is_enabled
    if is_default is not None:
        update["is_default"] = is_default
    if is_blocked is not None:
        update["is_blocked"] = is_blocked
        update["block_reason"] = block_reason
    
    await db.ai_provider_configs.update_one(
        {"provider": provider},
        {"$set": update},
        upsert=True
    )
    
    await create_audit_log(admin, "ai_provider_update", "ai_provider", provider, new_value=update)
    return {"message": "Provider updated"}

# ==================== ERRORS ====================
@router.get("/errors")
async def get_admin_errors(
    admin: dict = Depends(require_admin),
    error_type: str = None,
    skip: int = 0,
    limit: int = 50
):
    query = {}
    if error_type:
        query["error_type"] = error_type
    
    errors = await db.error_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"errors": errors, "total": await db.error_logs.count_documents(query)}

# ==================== AUDIT LOGS ====================
@router.get("/audit-logs")
async def get_audit_logs(
    admin: dict = Depends(require_admin),
    action: str = None,
    admin_id: str = None,
    skip: int = 0,
    limit: int = 100
):
    query = {}
    if action:
        query["action"] = action
    if admin_id:
        query["admin_id"] = admin_id
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"logs": logs, "total": await db.audit_logs.count_documents(query)}


# ==================== PROJECTS MANAGEMENT ====================
@router.get("/projects")
async def get_admin_projects(
    admin: dict = Depends(require_admin),
    plan: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 50
):
    query = {}
    
    # Filter by user plan
    if plan:
        plan_users = await db.users.find({"plan": plan}, {"id": 1}).to_list(10000)
        user_ids = [u["id"] for u in plan_users]
        query["user_id"] = {"$in": user_ids}
    
    # Filter by project status
    if status == "frozen":
        query["is_frozen"] = True
    elif status == "active":
        query["is_frozen"] = {"$ne": True}
    
    projects = await db.projects.find(query, {"_id": 0}).sort("updated_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with user data
    for project in projects:
        user = await db.users.find_one({"id": project["user_id"]}, {"_id": 0, "name": 1, "email": 1, "plan": 1})
        project["owner"] = user
        # Get deployment info
        deployment = await db.deployments.find_one({"project_id": project["id"]}, {"_id": 0})
        project["deployment"] = deployment
    
    return {"projects": projects, "total": await db.projects.count_documents(query)}

@router.get("/projects/{project_id}")
async def get_admin_project_detail(project_id: str, admin: dict = Depends(require_admin)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get owner
    owner = await db.users.find_one({"id": project["user_id"]}, {"_id": 0, "password_hash": 0})
    project["owner"] = owner
    
    # Get deployments
    deployments = await db.deployments.find({"project_id": project_id}, {"_id": 0}).sort("created_at", -1).to_list(10)
    project["deployments"] = deployments
    
    # Get chat messages count
    messages_count = await db.chat_messages.count_documents({"project_id": project_id})
    project["messages_count"] = messages_count
    
    return project

@router.post("/projects/{project_id}/freeze")
async def freeze_project(project_id: str, reason: str = None, admin: dict = Depends(require_admin)):
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"is_frozen": True, "freeze_reason": reason, "frozen_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await create_audit_log(admin, "project_freeze", "project", project_id, reason=reason)
    return {"message": "Project frozen"}

@router.post("/projects/{project_id}/unfreeze")
async def unfreeze_project(project_id: str, admin: dict = Depends(require_admin)):
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"is_frozen": False, "freeze_reason": None, "frozen_at": None}}
    )
    await create_audit_log(admin, "project_unfreeze", "project", project_id)
    return {"message": "Project unfrozen"}

@router.delete("/projects/{project_id}")
async def delete_admin_project(project_id: str, admin: dict = Depends(require_admin)):
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Soft delete - move to deleted collection
    project["deleted_at"] = datetime.now(timezone.utc).isoformat()
    project["deleted_by"] = admin["id"]
    await db.deleted_projects.insert_one(project)
    
    # Delete from main collection
    await db.projects.delete_one({"id": project_id})
    await db.chat_messages.delete_many({"project_id": project_id})
    
    await create_audit_log(admin, "project_delete", "project", project_id)
    return {"message": "Project deleted"}

@router.post("/projects/{project_id}/restore")
async def restore_admin_project(project_id: str, admin: dict = Depends(require_admin)):
    deleted_project = await db.deleted_projects.find_one({"id": project_id})
    if not deleted_project:
        raise HTTPException(status_code=404, detail="Deleted project not found")
    
    # Remove deletion metadata
    del deleted_project["deleted_at"]
    del deleted_project["deleted_by"]
    if "_id" in deleted_project:
        del deleted_project["_id"]
    
    # Restore to main collection
    await db.projects.insert_one(deleted_project)
    await db.deleted_projects.delete_one({"id": project_id})
    
    await create_audit_log(admin, "project_restore", "project", project_id)
    return {"message": "Project restored"}

@router.post("/projects/{project_id}/regenerate")
async def force_regenerate_project(project_id: str, admin: dict = Depends(require_admin)):
    """Force regenerate project code (support tool)"""
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create a job for regeneration
    job = {
        "id": str(uuid.uuid4()),
        "user_id": project["user_id"],
        "project_id": project_id,
        "job_type": "force_regenerate",
        "status": "queued",
        "priority": 100,  # High priority for admin-triggered
        "created_at": datetime.now(timezone.utc).isoformat(),
        "triggered_by_admin": admin["id"]
    }
    await db.jobs.insert_one(job)
    
    await create_audit_log(admin, "project_force_regenerate", "project", project_id)
    return {"message": "Regeneration job queued", "job_id": job["id"]}

# ==================== SETTINGS (Platform Controls) ====================
@router.get("/settings")
async def get_platform_settings(admin: dict = Depends(require_admin)):
    settings = await db.platform_settings.find_one({"id": "global"}, {"_id": 0})
    
    if not settings:
        # Default settings
        settings = {
            "id": "global",
            "feature_flags": {
                "byo_ai_enabled": True,
                "subdomain_enabled": True,
                "export_zip_enabled": True,
                "custom_domain_enabled": False,
                "team_collaboration_enabled": False
            },
            "maintenance_mode": False,
            "maintenance_message": "",
            "default_ai_provider": "openai",
            "rate_limits": {
                "requests_per_minute": 60,
                "generations_per_hour": 20
            },
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.platform_settings.insert_one(settings)
    
    return settings

@router.put("/settings")
async def update_platform_settings(
    settings_update: dict,
    admin: dict = Depends(require_admin)
):
    current = await db.platform_settings.find_one({"id": "global"})
    
    settings_update["updated_at"] = datetime.now(timezone.utc).isoformat()
    settings_update["updated_by"] = admin["id"]
    
    await db.platform_settings.update_one(
        {"id": "global"},
        {"$set": settings_update},
        upsert=True
    )
    
    await create_audit_log(
        admin, "settings_update", "settings", "global",
        old_value=current,
        new_value=settings_update
    )
    
    return {"message": "Settings updated"}

@router.post("/settings/maintenance")
async def toggle_maintenance_mode(
    enabled: bool,
    message: str = "",
    admin: dict = Depends(require_admin)
):
    await db.platform_settings.update_one(
        {"id": "global"},
        {"$set": {
            "maintenance_mode": enabled,
            "maintenance_message": message,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    await create_audit_log(admin, "maintenance_toggle", "settings", "global", new_value={"enabled": enabled})
    return {"message": f"Maintenance mode {'enabled' if enabled else 'disabled'}"}

@router.put("/settings/feature-flags")
async def update_feature_flags(
    flags: dict,
    admin: dict = Depends(require_admin)
):
    await db.platform_settings.update_one(
        {"id": "global"},
        {"$set": {"feature_flags": flags, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    await create_audit_log(admin, "feature_flags_update", "settings", "global", new_value=flags)
    return {"message": "Feature flags updated"}

# ==================== JOBS & BUILD LOGS ====================
@router.get("/jobs")
async def get_admin_jobs(
    admin: dict = Depends(require_admin),
    status: str = None,
    skip: int = 0,
    limit: int = 50
):
    query = {}
    if status:
        query["status"] = status
    
    jobs = await db.jobs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with user and project data
    for job in jobs:
        user = await db.users.find_one({"id": job["user_id"]}, {"_id": 0, "name": 1, "email": 1})
        job["user"] = user
        project = await db.projects.find_one({"id": job["project_id"]}, {"_id": 0, "name": 1})
        job["project"] = project
    
    return {
        "jobs": jobs,
        "total": await db.jobs.count_documents(query),
        "counts": {
            "queued": await db.jobs.count_documents({"status": "queued"}),
            "running": await db.jobs.count_documents({"status": "running"}),
            "completed": await db.jobs.count_documents({"status": "completed"}),
            "failed": await db.jobs.count_documents({"status": "failed"})
        }
    }

@router.get("/jobs/{job_id}")
async def get_admin_job_detail(job_id: str, admin: dict = Depends(require_admin)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get user and project
    job["user"] = await db.users.find_one({"id": job["user_id"]}, {"_id": 0, "password_hash": 0})
    job["project"] = await db.projects.find_one({"id": job["project_id"]}, {"_id": 0})
    
    return job

@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str, admin: dict = Depends(require_admin)):
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] not in ["failed", "completed"]:
        raise HTTPException(status_code=400, detail="Can only retry failed or completed jobs")
    
    # Create new job
    new_job = {
        "id": str(uuid.uuid4()),
        "user_id": job["user_id"],
        "project_id": job["project_id"],
        "job_type": job["job_type"],
        "status": "queued",
        "priority": job.get("priority", 0) + 10,  # Higher priority for retries
        "retry_of": job_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.jobs.insert_one(new_job)
    
    await create_audit_log(admin, "job_retry", "job", job_id)
    return {"message": "Job queued for retry", "new_job_id": new_job["id"]}

@router.post("/jobs/{job_id}/resolve")
async def mark_job_resolved(job_id: str, notes: str = None, admin: dict = Depends(require_admin)):
    await db.jobs.update_one(
        {"id": job_id},
        {"$set": {
            "resolved": True,
            "resolution_notes": notes,
            "resolved_by": admin["id"],
            "resolved_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await create_audit_log(admin, "job_resolve", "job", job_id, reason=notes)
    return {"message": "Job marked as resolved"}

