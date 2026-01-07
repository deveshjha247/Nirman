"""
App Integrations Models
Nirman AI - Connect GitHub, Vercel, Netlify, etc.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class IntegrationType(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    VERCEL = "vercel"
    NETLIFY = "netlify"
    SUPABASE = "supabase"
    FIREBASE = "firebase"
    CLOUDFLARE = "cloudflare"
    RAILWAY = "railway"
    RENDER = "render"


class IntegrationStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"
    ERROR = "error"


class UserIntegration(BaseModel):
    """User's connected integration"""
    id: str
    user_id: str
    integration_type: IntegrationType
    status: IntegrationStatus = IntegrationStatus.DISCONNECTED
    
    # OAuth tokens (encrypted)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[str] = None
    
    # Provider-specific data
    provider_user_id: Optional[str] = None
    provider_username: Optional[str] = None
    provider_email: Optional[str] = None
    provider_avatar: Optional[str] = None
    
    # Metadata
    scopes: List[str] = []
    connected_at: Optional[str] = None
    last_used_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: Optional[str] = None


class GitHubRepo(BaseModel):
    """GitHub Repository info"""
    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    private: bool = False
    html_url: str
    clone_url: str
    default_branch: str = "main"
    owner: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    pushed_at: Optional[str] = None
    size: int = 0
    language: Optional[str] = None
    topics: List[str] = []


class GitHubFile(BaseModel):
    """GitHub File info"""
    name: str
    path: str
    sha: str
    size: int
    type: str  # "file" or "dir"
    content: Optional[str] = None  # Base64 encoded for files
    download_url: Optional[str] = None


class GitHubCommit(BaseModel):
    """GitHub Commit info"""
    sha: str
    message: str
    author: str
    date: str
    url: str


class DeploymentTarget(BaseModel):
    """Deployment target info"""
    id: str
    user_id: str
    project_id: str
    integration_type: IntegrationType
    
    # Deployment config
    repo_name: Optional[str] = None
    repo_url: Optional[str] = None
    deploy_url: Optional[str] = None
    custom_domain: Optional[str] = None
    
    # Status
    last_deployed_at: Optional[str] = None
    deployment_status: str = "pending"
    
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CreateRepoRequest(BaseModel):
    """Request to create a new repo"""
    name: str
    description: Optional[str] = None
    private: bool = False
    auto_init: bool = True


class PushCodeRequest(BaseModel):
    """Request to push code to repo"""
    repo_name: str
    file_path: str = "index.html"
    content: str
    commit_message: str = "Update from Nirman AI"
    branch: str = "main"


class DeployRequest(BaseModel):
    """Request to deploy project"""
    project_id: str
    target: IntegrationType
    repo_name: Optional[str] = None
    custom_domain: Optional[str] = None
