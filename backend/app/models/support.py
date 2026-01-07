from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class SupportTicket(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    user_id: str
    user_email: str
    user_name: str
    user_plan: str  # free, pro, enterprise
    user_revenue: float = 0  # Total revenue from user (for priority)
    subject: str
    description: str
    category: str = "general"  # general, billing, technical, abuse
    status: str = "open"  # open, in_progress, waiting, resolved, closed
    priority: int = 0  # Calculated from plan + revenue
    assigned_to: Optional[str] = None
    messages: List[dict] = []  # [{sender, message, created_at}]
    resolution: Optional[str] = None
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None

class SupportTicketCreate(BaseModel):
    subject: str
    description: str
    category: str = "general"

class SupportMessage(BaseModel):
    message: str

class AuditLog(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    admin_id: str
    admin_email: str
    action: str  # user_ban, plan_change, refund, etc.
    target_type: str  # user, plan, coupon, project, etc.
    target_id: str
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: str
