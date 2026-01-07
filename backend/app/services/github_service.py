"""
GitHub Integration Service
Nirman AI - Full GitHub API integration for code push/pull
"""

import httpx
import base64
import uuid
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode

from app.db.mongo import db
from app.services.ai_router import encrypt_api_key, decrypt_api_key

# GitHub OAuth Config (from environment)
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.environ.get("GITHUB_REDIRECT_URI", "http://localhost:3000/integrations/github/callback")
GITHUB_SCOPES = ["repo", "read:user", "user:email"]

GITHUB_API_BASE = "https://api.github.com"
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"


class GitHubService:
    """GitHub API Service"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    # =========================================================================
    # USER & AUTH
    # =========================================================================
    
    async def get_user(self) -> Dict[str, Any]:
        """Get authenticated user info"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/user",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_emails(self) -> List[Dict[str, Any]]:
        """Get user's email addresses"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/user/emails",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    # =========================================================================
    # REPOSITORIES
    # =========================================================================
    
    async def list_repos(self, per_page: int = 30, page: int = 1, sort: str = "updated") -> List[Dict[str, Any]]:
        """List user's repositories"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/user/repos",
                headers=self.headers,
                params={
                    "per_page": per_page,
                    "page": page,
                    "sort": sort,
                    "affiliation": "owner,collaborator"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository details"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def create_repo(
        self, 
        name: str, 
        description: str = "", 
        private: bool = False,
        auto_init: bool = True
    ) -> Dict[str, Any]:
        """Create a new repository"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/user/repos",
                headers=self.headers,
                json={
                    "name": name,
                    "description": description,
                    "private": private,
                    "auto_init": auto_init,
                    "has_issues": True,
                    "has_projects": False,
                    "has_wiki": False
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_repo(self, owner: str, repo: str) -> bool:
        """Delete a repository"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
                headers=self.headers
            )
            return response.status_code == 204
    
    # =========================================================================
    # FILE OPERATIONS
    # =========================================================================
    
    async def get_contents(
        self, 
        owner: str, 
        repo: str, 
        path: str = "",
        ref: str = None
    ) -> Dict[str, Any]:
        """Get file or directory contents"""
        params = {}
        if ref:
            params["ref"] = ref
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def get_file_content(
        self, 
        owner: str, 
        repo: str, 
        path: str,
        ref: str = None
    ) -> str:
        """Get decoded file content"""
        content_data = await self.get_contents(owner, repo, path, ref)
        if content_data.get("encoding") == "base64":
            return base64.b64decode(content_data["content"]).decode("utf-8")
        return content_data.get("content", "")
    
    async def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
        sha: str = None
    ) -> Dict[str, Any]:
        """Create or update a file in the repository"""
        # Encode content to base64
        content_base64 = base64.b64encode(content.encode()).decode()
        
        payload = {
            "message": message,
            "content": content_base64,
            "branch": branch
        }
        
        # If updating, we need the SHA of the existing file
        if sha:
            payload["sha"] = sha
        else:
            # Try to get existing file SHA
            try:
                existing = await self.get_contents(owner, repo, path, branch)
                if isinstance(existing, dict) and "sha" in existing:
                    payload["sha"] = existing["sha"]
            except:
                pass  # File doesn't exist, create new
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_file(
        self,
        owner: str,
        repo: str,
        path: str,
        message: str,
        sha: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Delete a file from the repository"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers,
                json={
                    "message": message,
                    "sha": sha,
                    "branch": branch
                }
            )
            response.raise_for_status()
            return response.json()
    
    # =========================================================================
    # BULK OPERATIONS (Push multiple files)
    # =========================================================================
    
    async def push_multiple_files(
        self,
        owner: str,
        repo: str,
        files: List[Dict[str, str]],  # [{"path": "...", "content": "..."}]
        message: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Push multiple files in a single commit using Git Data API"""
        
        # 1. Get the latest commit SHA
        async with httpx.AsyncClient(timeout=60.0) as client:
            ref_response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/refs/heads/{branch}",
                headers=self.headers
            )
            ref_response.raise_for_status()
            latest_commit_sha = ref_response.json()["object"]["sha"]
            
            # 2. Get the tree SHA of the latest commit
            commit_response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/commits/{latest_commit_sha}",
                headers=self.headers
            )
            commit_response.raise_for_status()
            base_tree_sha = commit_response.json()["tree"]["sha"]
            
            # 3. Create blobs for each file
            tree_items = []
            for file in files:
                blob_response = await client.post(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/blobs",
                    headers=self.headers,
                    json={
                        "content": file["content"],
                        "encoding": "utf-8"
                    }
                )
                blob_response.raise_for_status()
                blob_sha = blob_response.json()["sha"]
                
                tree_items.append({
                    "path": file["path"],
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                })
            
            # 4. Create a new tree
            tree_response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees",
                headers=self.headers,
                json={
                    "base_tree": base_tree_sha,
                    "tree": tree_items
                }
            )
            tree_response.raise_for_status()
            new_tree_sha = tree_response.json()["sha"]
            
            # 5. Create a new commit
            new_commit_response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/commits",
                headers=self.headers,
                json={
                    "message": message,
                    "tree": new_tree_sha,
                    "parents": [latest_commit_sha]
                }
            )
            new_commit_response.raise_for_status()
            new_commit_sha = new_commit_response.json()["sha"]
            
            # 6. Update the reference
            update_ref_response = await client.patch(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/refs/heads/{branch}",
                headers=self.headers,
                json={"sha": new_commit_sha}
            )
            update_ref_response.raise_for_status()
            
            return {
                "commit_sha": new_commit_sha,
                "files_pushed": len(files),
                "branch": branch,
                "url": f"https://github.com/{owner}/{repo}/commit/{new_commit_sha}"
            }
    
    # =========================================================================
    # BRANCHES
    # =========================================================================
    
    async def list_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List repository branches"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/branches",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def create_branch(
        self, 
        owner: str, 
        repo: str, 
        branch_name: str,
        from_branch: str = "main"
    ) -> Dict[str, Any]:
        """Create a new branch"""
        async with httpx.AsyncClient() as client:
            # Get the SHA of the source branch
            ref_response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/refs/heads/{from_branch}",
                headers=self.headers
            )
            ref_response.raise_for_status()
            sha = ref_response.json()["object"]["sha"]
            
            # Create new branch
            response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/refs",
                headers=self.headers,
                json={
                    "ref": f"refs/heads/{branch_name}",
                    "sha": sha
                }
            )
            response.raise_for_status()
            return response.json()
    
    # =========================================================================
    # COMMITS
    # =========================================================================
    
    async def list_commits(
        self, 
        owner: str, 
        repo: str,
        branch: str = None,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """List repository commits"""
        params = {"per_page": per_page}
        if branch:
            params["sha"] = branch
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    # =========================================================================
    # GITHUB PAGES
    # =========================================================================
    
    async def enable_pages(
        self, 
        owner: str, 
        repo: str,
        branch: str = "main",
        path: str = "/"
    ) -> Dict[str, Any]:
        """Enable GitHub Pages for a repository"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pages",
                headers=self.headers,
                json={
                    "source": {
                        "branch": branch,
                        "path": path
                    }
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_pages_status(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get GitHub Pages status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pages",
                headers=self.headers
            )
            if response.status_code == 404:
                return {"enabled": False}
            response.raise_for_status()
            return {**response.json(), "enabled": True}


# =============================================================================
# OAUTH FLOW HELPERS
# =============================================================================

def get_github_oauth_url(state: str) -> str:
    """Generate GitHub OAuth authorization URL"""
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": " ".join(GITHUB_SCOPES),
        "state": state
    }
    return f"{GITHUB_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """Exchange OAuth code for access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI
            }
        )
        response.raise_for_status()
        return response.json()


# =============================================================================
# DATABASE HELPERS
# =============================================================================

async def save_github_integration(
    user_id: str,
    access_token: str,
    github_user: Dict[str, Any]
) -> Dict[str, Any]:
    """Save GitHub integration to database"""
    now = datetime.now(timezone.utc).isoformat()
    
    integration = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "integration_type": "github",
        "status": "connected",
        "access_token": encrypt_api_key(access_token),
        "provider_user_id": str(github_user["id"]),
        "provider_username": github_user["login"],
        "provider_email": github_user.get("email"),
        "provider_avatar": github_user.get("avatar_url"),
        "scopes": GITHUB_SCOPES,
        "connected_at": now,
        "created_at": now,
        "updated_at": now
    }
    
    # Upsert - update if exists, insert if not
    await db.user_integrations.update_one(
        {"user_id": user_id, "integration_type": "github"},
        {"$set": integration},
        upsert=True
    )
    
    return integration


async def get_github_integration(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user's GitHub integration"""
    integration = await db.user_integrations.find_one({
        "user_id": user_id,
        "integration_type": "github"
    })
    return integration


async def get_github_service(user_id: str) -> Optional[GitHubService]:
    """Get authenticated GitHub service for user"""
    integration = await get_github_integration(user_id)
    if not integration or integration.get("status") != "connected":
        return None
    
    access_token = decrypt_api_key(integration["access_token"])
    return GitHubService(access_token)


async def disconnect_github(user_id: str) -> bool:
    """Disconnect GitHub integration"""
    result = await db.user_integrations.update_one(
        {"user_id": user_id, "integration_type": "github"},
        {"$set": {"status": "disconnected", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return result.modified_count > 0
