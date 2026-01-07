from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class AIRun(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    user_id: str
    project_id: Optional[str] = None
    job_id: Optional[str] = None
    provider: str  # openai, gemini, claude, custom
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    status: str = "success"  # success, failed
    error_message: Optional[str] = None
    cost_estimate: float = 0.0
    is_byo_key: bool = False
    created_at: str

class AIProviderConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    provider: str
    is_enabled: bool = True
    is_default: bool = False
    health_status: str = "healthy"  # healthy, slow, down
    is_blocked: bool = False
    block_reason: Optional[str] = None
    updated_at: str

class UserAIKey(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    user_id: str
    provider: str  # openai, gemini, claude
    encrypted_key: str  # Never store raw key
    key_hint: str  # Last 4 chars for display
    is_active: bool = True
    created_at: str
    last_used_at: Optional[str] = None

class UserAIKeyCreate(BaseModel):
    provider: str
    api_key: str
