"""
Build Models - Data models for Build Jobs and Chat
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class BuildStatus(str, Enum):
    """Status of a build job"""
    QUEUED = "queued"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    """Types of agents"""
    CODER = "coder"
    BROWSER = "browser"
    FILE = "file"
    PLANNER = "planner"
    CASUAL = "casual"
    MCP = "mcp"


class EventType(str, Enum):
    """Types of build events"""
    # Job lifecycle
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"
    
    # Agent events
    AGENT_SELECTED = "agent_selected"
    AGENT_THINKING = "agent_thinking"
    AGENT_RESPONSE = "agent_response"
    
    # Planning events
    PLAN_CREATED = "plan_created"
    PLAN_STEP_START = "plan_step_start"
    PLAN_STEP_COMPLETE = "plan_step_complete"
    
    # Code events
    CODE_GENERATING = "code_generating"
    CODE_GENERATED = "code_generated"
    CODE_EXECUTING = "code_executing"
    CODE_SUCCESS = "code_success"
    CODE_ERROR = "code_error"
    
    # File events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    
    # Browser events
    BROWSER_NAVIGATING = "browser_navigating"
    BROWSER_SEARCHING = "browser_searching"
    BROWSER_SCREENSHOT = "browser_screenshot"
    
    # MCP events
    MCP_TOOL_CALL = "mcp_tool_call"
    MCP_TOOL_RESULT = "mcp_tool_result"
    
    # Build events
    BUILD_STARTED = "build_started"
    BUILD_PROGRESS = "build_progress"
    BUILD_COMPLETED = "build_completed"
    
    # Preview events
    PREVIEW_READY = "preview_ready"
    PREVIEW_ERROR = "preview_error"
    
    # General
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class PlanStep(BaseModel):
    """Step in an execution plan"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    agent: AgentType
    task: str
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[str] = None
    error: Optional[str] = None


class BuildJob(BaseModel):
    """Build job model"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    user_id: str
    project_id: Optional[str] = None
    prompt: str
    status: BuildStatus = BuildStatus.QUEUED
    progress: int = 0
    current_agent: Optional[str] = None
    current_step: Optional[str] = None
    
    # Results
    response: Optional[str] = None
    code_blocks: List[Dict[str, Any]] = []
    files: List[str] = []
    
    # Preview
    has_preview: bool = False
    preview_url: Optional[str] = None
    
    # Metadata
    model_used: Optional[str] = None
    tokens_used: int = 0
    error: Optional[str] = None
    
    # Timestamps
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class BuildEvent(BaseModel):
    """Single event in a build job"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    job_id: str
    seq: int
    type: str
    message: str
    data: Optional[Dict[str, Any]] = None
    progress: Optional[int] = None
    created_at: str


class ChatMessage(BaseModel):
    """Chat message in conversation"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    conversation_id: str
    user_id: str
    role: str  # user, assistant, system
    content: str
    
    # Optional metadata
    agent: Optional[str] = None
    job_id: Optional[str] = None
    code_blocks: List[Dict[str, Any]] = []
    
    timestamp: str


class Conversation(BaseModel):
    """Conversation model"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    user_id: str
    project_id: Optional[str] = None
    title: Optional[str] = None
    messages: List[ChatMessage] = []
    created_at: str
    updated_at: str


# Request models
class StartBuildRequest(BaseModel):
    """Request to start a build job"""
    prompt: str
    project_id: Optional[str] = None
    ai_provider: str = "auto"


class ChatRequest(BaseModel):
    """Request for chat message"""
    message: str
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None


class StopBuildRequest(BaseModel):
    """Request to stop a build job"""
    job_id: str


# Response models
class BuildJobResponse(BaseModel):
    """Response for build job status"""
    id: str
    status: BuildStatus
    progress: int
    response: Optional[str] = None
    error: Optional[str] = None
    has_preview: bool = False
    events: List[Dict[str, Any]] = []


class ChatResponse(BaseModel):
    """Response for chat"""
    job_id: str
    conversation_id: str
    status: str
    message: str
