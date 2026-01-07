from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.core.config import DEFAULT_AI_PROVIDER

class Project(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    framework: str = "react"
    html_code: Optional[str] = None
    css_code: Optional[str] = None
    js_code: Optional[str] = None
    created_at: str
    updated_at: str

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    framework: str = "react"

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    html_code: Optional[str] = None
    css_code: Optional[str] = None
    js_code: Optional[str] = None

class ChatMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    project_id: str
    role: str  # 'user' or 'assistant'
    content: str
    code_generated: Optional[str] = None
    ai_provider: Optional[str] = None
    created_at: str

class ChatRequest(BaseModel):
    project_id: str
    message: str
    ai_provider: str = DEFAULT_AI_PROVIDER
