from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class PlanModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    name: str
    price_monthly: float
    price_yearly: float
    features: List[str] = []
    limits: dict = {}
    is_active: bool = True
    sort_order: int = 0
    from_default: bool = False

class PlanCreate(BaseModel):
    id: str
    name: str
    price_monthly: float
    price_yearly: float
    features: List[str] = []
    limits: dict = {}
    is_active: bool = True
    sort_order: int = 0

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    features: Optional[List[str]] = None
    limits: Optional[dict] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class PurchasePlanRequest(BaseModel):
    plan: str
    billing_cycle: str = "monthly"
    use_wallet: bool = True
    coupon_code: Optional[str] = None
