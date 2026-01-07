from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime

class Job(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    user_id: str
    project_id: str
    job_type: str  # generate, regenerate, deploy
    status: str = "queued"  # queued, running, completed, failed
    priority: int = 0  # Higher = more priority
    steps: List[Dict] = []  # [{name, status, started_at, completed_at, logs}]
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    resolved: bool = False
    resolution_notes: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class JobStep(BaseModel):
    name: str  # planner, codegen, test, build, deploy
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    logs: Optional[str] = None

class Deployment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    user_id: str
    project_id: str
    job_id: Optional[str] = None
    status: str = "pending"  # pending, building, deployed, failed
    subdomain: Optional[str] = None
    custom_domain: Optional[str] = None
    build_time_ms: int = 0
    deploy_time_ms: int = 0
    storage_size_mb: float = 0
    version: int = 1
    logs_url: Optional[str] = None
    can_rollback: bool = False
    previous_version_id: Optional[str] = None
    created_at: str
    deployed_at: Optional[str] = None


# =============================================================================
# Build System Models (SSE streaming)
# =============================================================================

from enum import Enum

class BuildJobStatus(str, Enum):
    """Possible states for a build job"""
    QUEUED = "queued"
    RUNNING = "running"
    FAILED = "failed"
    SUCCESS = "success"
    CANCELLED = "cancelled"


class BuildEventType(str, Enum):
    """Types of build events for SSE streaming"""
    # Job lifecycle
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    
    # Agent events
    AGENT_SELECTED = "agent_selected"
    AGENT_THINKING = "agent_thinking"
    AGENT_RESPONSE = "agent_response"
    
    # Planning events
    PLANNING_STARTED = "planning_started"
    PLANNING_STEP = "planning_step"
    PLANNING_DONE = "planning_done"
    
    # Code events
    CODEGEN_STARTED = "codegen_started"
    CODEGEN_PROGRESS = "codegen_progress"
    CODEGEN_DONE = "codegen_done"
    CODE_EXECUTION = "code_execution"
    CODE_ERROR = "code_error"
    CODE_SUCCESS = "code_success"
    
    # File events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    
    # Browser events
    BROWSER_NAVIGATING = "browser_navigating"
    BROWSER_SCREENSHOT = "browser_screenshot"
    BROWSER_FORM_FILL = "browser_form_fill"
    
    # Build events
    BUILD_STARTED = "build_started"
    BUILD_PROGRESS = "build_progress"
    BUILD_COMPLETED = "build_completed"
    BUILD_ERROR = "build_error"
    
    # Install events
    INSTALL_STARTED = "install_started"
    INSTALL_PROGRESS = "install_progress"
    INSTALL_COMPLETED = "install_completed"
    
    # Preview events
    PREVIEW_READY = "preview_ready"
    PREVIEW_ERROR = "preview_error"
    
    # MCP events
    MCP_TOOL_CALL = "mcp_tool_call"
    MCP_TOOL_RESULT = "mcp_tool_result"
    
    # General
    PACKAGING = "packaging"
    ARTIFACT_READY = "artifact_ready"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"
    DEBUG = "debug"


class AgentType(str, Enum):
    """Types of agents in the system"""
    CODER = "coder"
    BROWSER = "browser"
    FILE = "file"
    PLANNER = "planner"
    CASUAL = "casual"
    MCP = "mcp"


class BuildJob(BaseModel):
    """
    Represents a build job with SSE streaming support.
    Stored in 'build_jobs' collection.
    """
    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)
    
    id: str
    user_id: str
    project_id: Optional[str] = None
    prompt: str  # User's build prompt
    status: BuildJobStatus = BuildJobStatus.QUEUED
    progress: int = 0  # 0-100
    ai_provider: str = "auto"  # openai, gemini, claude, or auto
    
    # Agent info
    current_agent: Optional[str] = None
    agents_used: List[str] = []
    
    # Results
    response: Optional[str] = None
    reasoning: Optional[str] = None
    code_blocks: List[Dict] = []
    files_created: List[str] = []
    files_modified: List[str] = []
    
    # Preview
    has_preview: bool = False
    preview_url: Optional[str] = None
    preview_type: Optional[str] = None  # web, image, document
    
    artifact_url: Optional[str] = None  # Download URL when ready
    error_message: Optional[str] = None
    
    # Timestamps
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Metadata
    model_used: Optional[str] = None
    tokens_used: int = 0
    cost: float = 0.0


class BuildEvent(BaseModel):
    """
    Represents a single event in a build job's timeline.
    Stored in 'build_events' collection.
    """
    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)
    
    id: str
    job_id: str
    seq: int  # Sequence number for ordering
    type: BuildEventType
    message: str  # Human-readable message
    payload: Optional[Dict] = None  # Additional data (provider, model, url, code, etc.)
    created_at: str


# Request/Response schemas for Build API

class CreateBuildRequest(BaseModel):
    """Request body for POST /api/projects/{project_id}/build"""
    prompt: str  # What to build
    ai_provider: str = "auto"  # AI provider preference


class BuildJobResponse(BaseModel):
    """Response for GET /api/jobs/{job_id}"""
    model_config = ConfigDict(use_enum_values=True)
    
    id: str
    status: BuildJobStatus
    progress: int
    artifact_url: Optional[str] = None
    error_message: Optional[str] = None
    message: Optional[str] = None  # Status message
    events: List[Dict] = []  # Recent events
    created_at: str
    updated_at: str

