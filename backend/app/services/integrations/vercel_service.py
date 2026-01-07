"""
Vercel Integration Service
Nirman AI - Deploy to Vercel Platform

Features:
- OAuth authentication
- Project deployment
- Preview URLs
- Custom domains
- Environment variables
- Deployment logs
"""

import httpx
import os
import base64
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from app.db.mongo import db

# Vercel API Configuration
VERCEL_CLIENT_ID = os.environ.get("VERCEL_CLIENT_ID", "")
VERCEL_CLIENT_SECRET = os.environ.get("VERCEL_CLIENT_SECRET", "")
VERCEL_REDIRECT_URI = os.environ.get("VERCEL_REDIRECT_URI", "http://localhost:3000/integrations")
VERCEL_API_URL = "https://api.vercel.com"


def get_vercel_oauth_url(state: str) -> str:
    """Generate Vercel OAuth URL"""
    params = {
        "client_id": VERCEL_CLIENT_ID,
        "redirect_uri": VERCEL_REDIRECT_URI,
        "state": state,
        "scope": "user:read project:read project:write deployment:read deployment:write"
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://vercel.com/integrations/{VERCEL_CLIENT_ID}/new?{query}"


async def exchange_vercel_code_for_token(code: str) -> Dict[str, Any]:
    """Exchange OAuth code for access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.vercel.com/v2/oauth/access_token",
            data={
                "client_id": VERCEL_CLIENT_ID,
                "client_secret": VERCEL_CLIENT_SECRET,
                "code": code,
                "redirect_uri": VERCEL_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json()


async def save_vercel_integration(user_id: str, access_token: str, team_id: Optional[str], user_info: Dict) -> Dict:
    """Save Vercel integration to database"""
    now = datetime.now(timezone.utc).isoformat()
    
    integration = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "integration_type": "vercel",
        "status": "connected",
        "access_token": access_token,
        "team_id": team_id,
        "provider_user_id": user_info.get("id"),
        "provider_username": user_info.get("username"),
        "provider_email": user_info.get("email"),
        "provider_avatar": user_info.get("avatar"),
        "scopes": ["user:read", "project:read", "project:write", "deployment:read", "deployment:write"],
        "connected_at": now,
        "created_at": now,
        "updated_at": now,
    }
    
    # Upsert integration
    await db.user_integrations.update_one(
        {"user_id": user_id, "integration_type": "vercel"},
        {"$set": integration},
        upsert=True
    )
    
    return integration


async def get_vercel_integration(user_id: str) -> Optional[Dict]:
    """Get user's Vercel integration"""
    return await db.user_integrations.find_one(
        {"user_id": user_id, "integration_type": "vercel"},
        {"_id": 0}
    )


async def disconnect_vercel(user_id: str) -> bool:
    """Disconnect Vercel integration"""
    result = await db.user_integrations.delete_one(
        {"user_id": user_id, "integration_type": "vercel"}
    )
    return result.deleted_count > 0


class VercelService:
    """
    Vercel API Service
    
    Handles all Vercel platform operations including:
    - User authentication
    - Project management
    - Deployments
    - Domain configuration
    """
    
    def __init__(self, access_token: str, team_id: Optional[str] = None):
        self.access_token = access_token
        self.team_id = team_id
        self.base_url = VERCEL_API_URL
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Vercel API"""
        url = f"{self.base_url}{endpoint}"
        
        # Add team_id if available
        if self.team_id:
            if "params" not in kwargs:
                kwargs["params"] = {}
            kwargs["params"]["teamId"] = self.team_id
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=self.headers, **kwargs
            )
            response.raise_for_status()
            return response.json()
    
    # =========================================================================
    # USER OPERATIONS
    # =========================================================================
    
    async def get_user(self) -> Dict[str, Any]:
        """Get authenticated user info"""
        return await self._request("GET", "/v2/user")
    
    async def get_teams(self) -> List[Dict[str, Any]]:
        """Get user's teams"""
        result = await self._request("GET", "/v2/teams")
        return result.get("teams", [])
    
    # =========================================================================
    # PROJECT OPERATIONS
    # =========================================================================
    
    async def list_projects(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List all projects"""
        result = await self._request("GET", "/v9/projects", params={"limit": limit})
        return result.get("projects", [])
    
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details"""
        return await self._request("GET", f"/v9/projects/{project_id}")
    
    async def create_project(
        self,
        name: str,
        framework: str = "nextjs",
        git_repo: Optional[str] = None,
        environment_variables: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Create a new Vercel project"""
        data = {
            "name": name,
            "framework": framework,
        }
        
        if git_repo:
            data["gitRepository"] = {
                "type": "github",
                "repo": git_repo
            }
        
        if environment_variables:
            data["environmentVariables"] = environment_variables
        
        return await self._request("POST", "/v10/projects", json=data)
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        await self._request("DELETE", f"/v9/projects/{project_id}")
        return True
    
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update project settings"""
        return await self._request("PATCH", f"/v9/projects/{project_id}", json=updates)
    
    # =========================================================================
    # DEPLOYMENT OPERATIONS
    # =========================================================================
    
    async def list_deployments(self, project_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """List deployments"""
        params = {"limit": limit}
        if project_id:
            params["projectId"] = project_id
        
        result = await self._request("GET", "/v6/deployments", params=params)
        return result.get("deployments", [])
    
    async def get_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment details"""
        return await self._request("GET", f"/v13/deployments/{deployment_id}")
    
    async def create_deployment(
        self,
        name: str,
        files: List[Dict[str, Any]],
        project_id: Optional[str] = None,
        target: str = "production",
        env_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new deployment
        
        Args:
            name: Deployment name
            files: List of files [{"file": "path", "data": "content"}]
            project_id: Optional project to deploy to
            target: "production" or "preview"
            env_vars: Environment variables
        """
        # Prepare files for deployment
        prepared_files = []
        for f in files:
            file_content = f.get("data", "")
            if isinstance(file_content, str):
                file_content = file_content.encode()
            
            prepared_files.append({
                "file": f["file"],
                "data": base64.b64encode(file_content).decode(),
                "encoding": "base64"
            })
        
        data = {
            "name": name,
            "files": prepared_files,
            "target": target,
        }
        
        if project_id:
            data["project"] = project_id
        
        if env_vars:
            data["env"] = env_vars
        
        return await self._request("POST", "/v13/deployments", json=data)
    
    async def cancel_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """Cancel a running deployment"""
        return await self._request("PATCH", f"/v12/deployments/{deployment_id}/cancel")
    
    async def get_deployment_events(self, deployment_id: str) -> List[Dict[str, Any]]:
        """Get deployment build logs/events"""
        result = await self._request("GET", f"/v2/deployments/{deployment_id}/events")
        return result
    
    # =========================================================================
    # DOMAIN OPERATIONS
    # =========================================================================
    
    async def list_domains(self, project_id: str) -> List[Dict[str, Any]]:
        """List project domains"""
        result = await self._request("GET", f"/v9/projects/{project_id}/domains")
        return result.get("domains", [])
    
    async def add_domain(self, project_id: str, domain: str) -> Dict[str, Any]:
        """Add a domain to project"""
        return await self._request(
            "POST", 
            f"/v9/projects/{project_id}/domains",
            json={"name": domain}
        )
    
    async def remove_domain(self, project_id: str, domain: str) -> bool:
        """Remove domain from project"""
        await self._request("DELETE", f"/v9/projects/{project_id}/domains/{domain}")
        return True
    
    async def verify_domain(self, domain: str) -> Dict[str, Any]:
        """Verify domain ownership"""
        return await self._request("POST", f"/v6/domains/{domain}/verify")
    
    # =========================================================================
    # ENVIRONMENT VARIABLES
    # =========================================================================
    
    async def list_env_vars(self, project_id: str) -> List[Dict[str, Any]]:
        """List project environment variables"""
        result = await self._request("GET", f"/v9/projects/{project_id}/env")
        return result.get("envs", [])
    
    async def add_env_var(
        self,
        project_id: str,
        key: str,
        value: str,
        target: List[str] = ["production", "preview", "development"],
        env_type: str = "encrypted"
    ) -> Dict[str, Any]:
        """Add environment variable"""
        return await self._request(
            "POST",
            f"/v10/projects/{project_id}/env",
            json={
                "key": key,
                "value": value,
                "target": target,
                "type": env_type
            }
        )
    
    async def delete_env_var(self, project_id: str, env_id: str) -> bool:
        """Delete environment variable"""
        await self._request("DELETE", f"/v9/projects/{project_id}/env/{env_id}")
        return True
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    async def deploy_static_site(
        self,
        name: str,
        html_content: str,
        css_content: Optional[str] = None,
        js_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Quick deploy a static site
        
        Creates deployment with HTML, CSS, and JS files
        """
        files = [{"file": "index.html", "data": html_content}]
        
        if css_content:
            files.append({"file": "styles.css", "data": css_content})
        
        if js_content:
            files.append({"file": "script.js", "data": js_content})
        
        return await self.create_deployment(name=name, files=files)
    
    async def deploy_from_project(self, project_id: str, code: Dict[str, str]) -> Dict[str, Any]:
        """
        Deploy code from a Nirman project
        
        Args:
            project_id: Nirman project ID
            code: Dict with file paths as keys and content as values
        """
        from app.db.mongo import db
        
        project = await db.projects.find_one({"id": project_id})
        if not project:
            raise ValueError("Project not found")
        
        files = [{"file": path, "data": content} for path, content in code.items()]
        
        return await self.create_deployment(
            name=project.get("name", "nirman-project"),
            files=files,
            target="production"
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_vercel_service(user_id: str) -> Optional[VercelService]:
    """Get VercelService for user if connected"""
    integration = await get_vercel_integration(user_id)
    if not integration or integration.get("status") != "connected":
        return None
    return VercelService(
        integration["access_token"],
        integration.get("team_id")
    )
