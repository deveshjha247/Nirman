from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class WalletTransaction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    user_id: str
    amount: float
    type: str  # 'credit' or 'debit'
    description: str
    payment_id: Optional[str] = None
    created_at: str

class AddMoneyRequest(BaseModel):
    amount: float

class Purchase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    user_id: str
    plan: str
    billing_cycle: str
    amount: float
    coupon_code: Optional[str] = None
    coupon_discount: float = 0
    status: str = "pending"
    created_at: str

class Referral(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    referrer_id: str
    referee_id: str
    referee_name: Optional[str] = None
    referee_email: Optional[str] = None
    bonus_amount: float = 50
    bonus_given: bool = False
    created_at: str
