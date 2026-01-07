from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import List
import uuid

from app.core.security import require_auth, require_admin
from app.db.mongo import db
from app.models.support import SupportTicketCreate, SupportMessage

router = APIRouter(tags=["support"])

def calculate_ticket_priority(user: dict) -> int:
    """Calculate ticket priority based on plan and revenue"""
    plan_priority = {"free": 0, "pro": 50, "enterprise": 100}
    priority = plan_priority.get(user.get("plan", "free"), 0)
    
    # Add revenue-based priority (1 point per ₹100 spent)
    # This will be calculated when creating ticket
    return priority

# ==================== USER ENDPOINTS ====================
@router.post("/support/tickets")
async def create_support_ticket(ticket_data: SupportTicketCreate, user: dict = Depends(require_auth)):
    # Get user's total revenue
    purchases = await db.purchases.find({"user_id": user["id"], "status": "completed"}).to_list(1000)
    total_revenue = sum(p.get("amount", 0) for p in purchases)
    
    # Calculate priority
    plan_priority = {"free": 0, "pro": 50, "enterprise": 100}
    priority = plan_priority.get(user.get("plan", "free"), 0)
    priority += int(total_revenue / 100)  # 1 point per ₹100
    
    now = datetime.now(timezone.utc)
    ticket = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "user_email": user["email"],
        "user_name": user["name"],
        "user_plan": user.get("plan", "free"),
        "user_revenue": total_revenue,
        "subject": ticket_data.subject,
        "description": ticket_data.description,
        "category": ticket_data.category,
        "status": "open",
        "priority": priority,
        "assigned_to": None,
        "messages": [{
            "sender": "user",
            "sender_id": user["id"],
            "message": ticket_data.description,
            "created_at": now.isoformat()
        }],
        "resolution": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "resolved_at": None
    }
    
    await db.support_tickets.insert_one(ticket)
    return {"message": "Ticket created", "ticket_id": ticket["id"]}

@router.get("/support/tickets")
async def get_user_tickets(user: dict = Depends(require_auth)):
    tickets = await db.support_tickets.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"tickets": tickets}

@router.get("/support/tickets/{ticket_id}")
async def get_ticket_detail(ticket_id: str, user: dict = Depends(require_auth)):
    ticket = await db.support_tickets.find_one(
        {"id": ticket_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.post("/support/tickets/{ticket_id}/message")
async def add_ticket_message(ticket_id: str, message_data: SupportMessage, user: dict = Depends(require_auth)):
    ticket = await db.support_tickets.find_one({"id": ticket_id, "user_id": user["id"]})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket["status"] in ["resolved", "closed"]:
        raise HTTPException(status_code=400, detail="Cannot add message to closed ticket")
    
    now = datetime.now(timezone.utc)
    new_message = {
        "sender": "user",
        "sender_id": user["id"],
        "message": message_data.message,
        "created_at": now.isoformat()
    }
    
    await db.support_tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"messages": new_message},
            "$set": {"updated_at": now.isoformat(), "status": "open"}
        }
    )
    
    return {"message": "Message added"}

# ==================== ADMIN ENDPOINTS ====================
@router.get("/admin/support/tickets")
async def get_admin_tickets(
    admin: dict = Depends(require_admin),
    status: str = None,
    category: str = None,
    skip: int = 0,
    limit: int = 50
):
    query = {}
    if status:
        query["status"] = status
    if category:
        query["category"] = category
    
    # Sort by priority (high first), then by created_at
    tickets = await db.support_tickets.find(
        query, {"_id": 0}
    ).sort([("priority", -1), ("created_at", 1)]).skip(skip).limit(limit).to_list(limit)
    
    return {
        "tickets": tickets,
        "total": await db.support_tickets.count_documents(query)
    }

@router.get("/admin/support/tickets/{ticket_id}")
async def get_admin_ticket_detail(ticket_id: str, admin: dict = Depends(require_admin)):
    ticket = await db.support_tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get user details
    user = await db.users.find_one({"id": ticket["user_id"]}, {"_id": 0, "password_hash": 0})
    ticket["user_details"] = user
    
    return ticket

@router.post("/admin/support/tickets/{ticket_id}/reply")
async def admin_reply_ticket(ticket_id: str, message_data: SupportMessage, admin: dict = Depends(require_admin)):
    ticket = await db.support_tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    now = datetime.now(timezone.utc)
    new_message = {
        "sender": "admin",
        "sender_id": admin["id"],
        "sender_name": admin["name"],
        "message": message_data.message,
        "created_at": now.isoformat()
    }
    
    await db.support_tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"messages": new_message},
            "$set": {
                "updated_at": now.isoformat(),
                "status": "in_progress",
                "assigned_to": admin["id"]
            }
        }
    )
    
    return {"message": "Reply sent"}

@router.put("/admin/support/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    status: str,
    resolution: str = None,
    admin: dict = Depends(require_admin)
):
    valid_statuses = ["open", "in_progress", "waiting", "resolved", "closed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    now = datetime.now(timezone.utc)
    update = {"status": status, "updated_at": now.isoformat()}
    
    if status in ["resolved", "closed"]:
        update["resolved_at"] = now.isoformat()
        if resolution:
            update["resolution"] = resolution
    
    await db.support_tickets.update_one({"id": ticket_id}, {"$set": update})
    return {"message": "Ticket status updated"}

@router.put("/admin/support/tickets/{ticket_id}/assign")
async def assign_ticket(ticket_id: str, admin_id: str = None, admin: dict = Depends(require_admin)):
    assigned_to = admin_id or admin["id"]
    
    await db.support_tickets.update_one(
        {"id": ticket_id},
        {"$set": {
            "assigned_to": assigned_to,
            "status": "in_progress",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Ticket assigned"}

@router.get("/admin/support/stats")
async def get_support_stats(admin: dict = Depends(require_admin)):
    open_count = await db.support_tickets.count_documents({"status": "open"})
    in_progress = await db.support_tickets.count_documents({"status": "in_progress"})
    waiting = await db.support_tickets.count_documents({"status": "waiting"})
    resolved = await db.support_tickets.count_documents({"status": "resolved"})
    
    # Average resolution time
    resolved_tickets = await db.support_tickets.find(
        {"status": {"$in": ["resolved", "closed"]}, "resolved_at": {"$ne": None}}
    ).to_list(1000)
    
    avg_resolution_hours = 0
    if resolved_tickets:
        total_hours = 0
        for t in resolved_tickets:
            try:
                created = datetime.fromisoformat(t["created_at"].replace('Z', '+00:00'))
                resolved = datetime.fromisoformat(t["resolved_at"].replace('Z', '+00:00'))
                total_hours += (resolved - created).total_seconds() / 3600
            except Exception:
                pass
        avg_resolution_hours = total_hours / len(resolved_tickets) if resolved_tickets else 0
    
    # By category
    by_category = {}
    all_tickets = await db.support_tickets.find({}, {"category": 1}).to_list(10000)
    for t in all_tickets:
        cat = t.get("category", "general")
        by_category[cat] = by_category.get(cat, 0) + 1
    
    return {
        "open": open_count,
        "in_progress": in_progress,
        "waiting": waiting,
        "resolved": resolved,
        "avg_resolution_hours": round(avg_resolution_hours, 2),
        "by_category": by_category
    }
