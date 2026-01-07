from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class Coupon(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    code: str
    discount_type: str = "percentage"  # 'percentage' or 'fixed'
    discount_value: float
    min_purchase: float = 0
    max_discount: Optional[float] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    usage_limit: int = -1
    used_count: int = 0
    applicable_plans: List[str] = []
    is_active: bool = True
    created_at: str

class CouponCreate(BaseModel):
    code: str
    discount_type: str = "percentage"
    discount_value: float
    min_purchase: float = 0
    max_discount: Optional[float] = None
    valid_until: Optional[str] = None
    usage_limit: int = -1
    applicable_plans: List[str] = []
    is_active: bool = True

class CouponUpdate(BaseModel):
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_purchase: Optional[float] = None
    max_discount: Optional[float] = None
    valid_until: Optional[str] = None
    usage_limit: Optional[int] = None
    applicable_plans: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ErrorLog(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    error_type: str
    error_message: str
    endpoint: str
    user_id: Optional[str] = None
    stack_trace: Optional[str] = None
    created_at: str
