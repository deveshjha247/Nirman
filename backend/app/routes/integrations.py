"""
Integrations Routes
Nirman AI - GitHub, Vercel, Netlify integration endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
import uuid
import os
import httpx

from app.core.security import require_auth
from app.db.mongo import db
from app.services.github_service import (
    GitHubService,
    get_github_oauth_url,
    exchange_code_for_token,
    save_github_integration,
    get_github_integration,
    get_github_service,
    disconnect_github,
    GITHUB_CLIENT_ID
)

router = APIRouter(prefix="/integrations", tags=["integrations"])

# =============================================================================
# INTEGRATION STATUS
# =============================================================================

@router.get("")
async def get_user_integrations(user: dict = Depends(require_auth)):
    """Get all user integrations and their status"""
    integrations = await db.user_integrations.find(
        {"user_id": user["id"]},
        {"_id": 0, "access_token": 0, "refresh_token": 0}
    ).to_list(20)
    
    # Available integrations
    available = [
        {
            "id": "github",
            "name": "GitHub",
            "icon": "🐙",
            "description": "Push code to GitHub, create repos, enable GitHub Pages",
            "features": ["Push Code", "Create Repos", "GitHub Pages", "Read Repos"],
            "category": "deployment",
            "connected": False
        },
        {
            "id": "vercel",
            "name": "Vercel",
            "icon": "▲",
            "description": "Deploy to Vercel with automatic preview URLs",
            "features": ["Deploy", "Preview URLs", "Custom Domains"],
            "category": "deployment",
            "connected": False
        },
        {
            "id": "supabase",
            "name": "Supabase",
            "icon": "⚡",
            "description": "Connect to Supabase for backend & database",
            "features": ["Database", "Auth", "Storage"],
            "category": "backend",
            "connected": False
        },
        {
            "id": "firebase",
            "name": "Firebase",
            "icon": "🔥",
            "description": "Deploy to Firebase Hosting",
            "features": ["Hosting", "Auth", "Database"],
            "category": "backend",
            "connected": False
        },
        {
            "id": "mongodb",
            "name": "MongoDB Atlas",
            "icon": "🍃",
            "description": "Cloud MongoDB clusters and databases",
            "features": ["Clusters", "Backups", "Data API"],
            "category": "database",
            "connected": False
        },
        {
            "id": "canva",
            "name": "Canva",
            "icon": "🎨",
            "description": "Create and export designs",
            "features": ["Designs", "Export", "Templates"],
            "category": "design",
            "connected": False
        },
        {
            "id": "razorpay",
            "name": "Razorpay",
            "icon": "💳",
            "description": "Accept payments in India",
            "features": ["Payments", "Subscriptions", "Payouts"],
            "category": "payments",
            "connected": False
        },
        {
            "id": "cashfree",
            "name": "Cashfree",
            "icon": "💰",
            "description": "Payment gateway & payouts",
            "features": ["Payments", "Links", "Settlements"],
            "category": "payments",
            "connected": False
        }
    ]
    
    # Mark connected integrations
    connected_map = {i["integration_type"]: i for i in integrations}
    for item in available:
        if item["id"] in connected_map:
            conn = connected_map[item["id"]]
            item["connected"] = conn.get("status") == "connected"
            item["username"] = conn.get("provider_username")
            item["avatar"] = conn.get("provider_avatar")
            item["connected_at"] = conn.get("connected_at")
    
    return {
        "integrations": available,
        "connected_count": len([i for i in available if i.get("connected")])
    }


# =============================================================================
# GITHUB OAUTH
# =============================================================================

@router.get("/github/auth-url")
async def get_github_auth_url(user: dict = Depends(require_auth)):
    """Get GitHub OAuth authorization URL"""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=503, 
            detail="GitHub integration not configured. Set GITHUB_CLIENT_ID in environment."
        )
    
    # Generate state token for security
    state = f"{user['id']}:{uuid.uuid4()}"
    
    # Store state in DB temporarily (expires in 10 minutes)
    await db.oauth_states.insert_one({
        "state": state,
        "user_id": user["id"],
        "provider": "github",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    auth_url = get_github_oauth_url(state)
    return {"auth_url": auth_url}


@router.post("/github/callback")
async def github_oauth_callback(
    code: str,
    state: str,
    user: dict = Depends(require_auth)
):
    """Handle GitHub OAuth callback"""
    # Verify state
    stored_state = await db.oauth_states.find_one({"state": state, "user_id": user["id"]})
    if not stored_state:
        raise HTTPException(status_code=400, detail="Invalid or expired state")
    
    # Clean up state
    await db.oauth_states.delete_one({"_id": stored_state["_id"]})
    
    try:
        # Exchange code for token
        token_data = await exchange_code_for_token(code)
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data.get("error_description", "OAuth failed"))
        
        access_token = token_data["access_token"]
        
        # Get GitHub user info
        github = GitHubService(access_token)
        github_user = await github.get_user()
        
        # Save integration
        integration = await save_github_integration(user["id"], access_token, github_user)
        
        return {
            "success": True,
            "message": f"Successfully connected GitHub as @{github_user['login']}",
            "username": github_user["login"],
            "avatar": github_user.get("avatar_url")
        }
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=400, detail=f"GitHub API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect GitHub: {str(e)}")


@router.delete("/github")
async def disconnect_github_integration(user: dict = Depends(require_auth)):
    """Disconnect GitHub integration"""
    success = await disconnect_github(user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="GitHub integration not found")
    return {"success": True, "message": "GitHub disconnected"}


@router.get("/github/status")
async def get_github_status(user: dict = Depends(require_auth)):
    """Get GitHub integration status and user info"""
    integration = await get_github_integration(user["id"])
    
    if not integration or integration.get("status") != "connected":
        return {"connected": False}
    
    return {
        "connected": True,
        "username": integration.get("provider_username"),
        "avatar": integration.get("provider_avatar"),
        "email": integration.get("provider_email"),
        "connected_at": integration.get("connected_at"),
        "scopes": integration.get("scopes", [])
    }


# =============================================================================
# GITHUB REPOS
# =============================================================================

@router.get("/github/repos")
async def list_github_repos(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    user: dict = Depends(require_auth)
):
    """List user's GitHub repositories"""
    github = await get_github_service(user["id"])
    if not github:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    
    try:
        repos = await github.list_repos(per_page=per_page, page=page)
        return {
            "repos": [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "full_name": r["full_name"],
                    "description": r["description"],
                    "private": r["private"],
                    "html_url": r["html_url"],
                    "default_branch": r.get("default_branch", "main"),
                    "language": r.get("language"),
                    "updated_at": r.get("updated_at"),
                    "size": r.get("size", 0)
                }
                for r in repos
            ],
            "page": page,
            "per_page": per_page
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list repos: {str(e)}")


@router.post("/github/repos")
async def create_github_repo(
    name: str,
    description: str = "",
    private: bool = False,
    user: dict = Depends(require_auth)
):
    """Create a new GitHub repository"""
    github = await get_github_service(user["id"])
    if not github:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    
    try:
        repo = await github.create_repo(name, description, private, auto_init=True)
        return {
            "success": True,
            "repo": {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
                "html_url": repo["html_url"],
                "clone_url": repo["clone_url"],
                "default_branch": repo.get("default_branch", "main")
            }
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            raise HTTPException(status_code=400, detail="Repository name already exists")
        raise HTTPException(status_code=500, detail=f"Failed to create repo: {str(e)}")


@router.get("/github/repos/{owner}/{repo}")
async def get_github_repo(owner: str, repo: str, user: dict = Depends(require_auth)):
    """Get repository details"""
    github = await get_github_service(user["id"])
    if not github:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    
    try:
        repo_data = await github.get_repo(owner, repo)
        return repo_data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/github/repos/{owner}/{repo}/contents")
async def get_repo_contents(
    owner: str, 
    repo: str, 
    path: str = "",
    ref: str = None,
    user: dict = Depends(require_auth)
):
    """Get repository file/directory contents"""
    github = await get_github_service(user["id"])
    if not github:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    
    try:
        contents = await github.get_contents(owner, repo, path, ref)
        return {"contents": contents}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Path not found")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/github/repos/{owner}/{repo}/file")
async def get_file_content(
    owner: str,
    repo: str,
    path: str,
    ref: str = None,
    user: dict = Depends(require_auth)
):
    """Get decoded file content"""
    github = await get_github_service(user["id"])
    if not github:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    
    try:
        content = await github.get_file_content(owner, repo, path, ref)
        return {"content": content, "path": path}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="File not found")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PUSH CODE TO GITHUB
# =============================================================================

@router.post("/github/repos/{owner}/{repo}/push")
async def push_file_to_github(
    owner: str,
    repo: str,
    path: str,
    content: str,
    message: str = "Update from Nirman AI",
    branch: str = "main",
    user: dict = Depends(require_auth)
):
    """Push a single file to GitHub"""
    github = await get_github_service(user["id"])
    if not github:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    
    try:
        result = await github.create_or_update_file(
            owner=owner,
            repo=repo,
            path=path,
            content=content,
            message=message,
            branch=branch
        )
        return {
            "success": True,
            "commit": result["commit"]["sha"],
            "message": f"Successfully pushed {path}",
            "url": result["content"]["html_url"]
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Failed to push: {str(e)}")


@router.post("/github/repos/{owner}/{repo}/push-multiple")
async def push_multiple_files(
    owner: str,
    repo: str,
    files: list,  # [{"path": "...", "content": "..."}]
    message: str = "Update from Nirman AI",
    branch: str = "main",
    user: dict = Depends(require_auth)
):
    """Push multiple files in a single commit"""
    github = await get_github_service(user["id"])
    if not github:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    
    try:
        result = await github.push_multiple_files(
            owner=owner,
            repo=repo,
            files=files,
            message=message,
            branch=branch
        )
        return {
            "success": True,
            **result
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Failed to push: {str(e)}")


# =============================================================================
# DEPLOY PROJECT TO GITHUB
# =============================================================================

@router.post("/github/deploy/{project_id}")
async def deploy_project_to_github(
    project_id: str,
    repo_name: str = None,
    create_new: bool = True,
    private: bool = False,
    enable_pages: bool = True,
    user: dict = Depends(require_auth)
):
    """Deploy a Nirman project to GitHub"""
    github = await get_github_service(user["id"])
    if not github:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    
    # Get project
    project = await db.projects.find_one({"id": project_id, "user_id": user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get GitHub username
    integration = await get_github_integration(user["id"])
    owner = integration["provider_username"]
    
    # Repo name defaults to project name
    if not repo_name:
        repo_name = project["name"].lower().replace(" ", "-").replace("_", "-")
        # Remove special characters
        repo_name = "".join(c for c in repo_name if c.isalnum() or c == "-")
    
    try:
        # Create repo if needed
        if create_new:
            try:
                await github.create_repo(
                    name=repo_name,
                    description=f"Built with Nirman AI - {project.get('description', '')}",
                    private=private,
                    auto_init=True
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code != 422:  # 422 = already exists
                    raise
        
        # Prepare files to push
        html_content = project.get("html_code", "")
        
        files = [
            {
                "path": "index.html",
                "content": html_content
            },
            {
                "path": "README.md",
                "content": f"""# {project['name']}

Built with [Nirman AI](https://nirman.ai) 🚀

## Description
{project.get('description', 'A website built with Nirman AI')}

## Deployment
This project is automatically deployed to GitHub Pages.

---
*Generated by Nirman AI - सोच लो, बना दो*
"""
            }
        ]
        
        # Push files
        result = await github.push_multiple_files(
            owner=owner,
            repo=repo_name,
            files=files,
            message=f"Deploy: {project['name']} via Nirman AI 🚀"
        )
        
        # Enable GitHub Pages
        pages_url = None
        if enable_pages:
            try:
                await github.enable_pages(owner, repo_name, "main", "/")
                pages_url = f"https://{owner}.github.io/{repo_name}/"
            except:
                pass  # Pages might already be enabled
        
        # Save deployment info
        deployment = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "project_id": project_id,
            "integration_type": "github",
            "repo_name": repo_name,
            "repo_url": f"https://github.com/{owner}/{repo_name}",
            "deploy_url": pages_url,
            "deployment_status": "deployed",
            "last_deployed_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.deployments.update_one(
            {"project_id": project_id, "integration_type": "github"},
            {"$set": deployment},
            upsert=True
        )
        
        return {
            "success": True,
            "repo_url": f"https://github.com/{owner}/{repo_name}",
            "pages_url": pages_url,
            "commit": result.get("commit_sha"),
            "files_pushed": result.get("files_pushed", 1)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.get("/github/deployments/{project_id}")
async def get_project_deployment(project_id: str, user: dict = Depends(require_auth)):
    """Get deployment status for a project"""
    deployment = await db.deployments.find_one({
        "project_id": project_id,
        "user_id": user["id"],
        "integration_type": "github"
    }, {"_id": 0})
    
    if not deployment:
        return {"deployed": False}
    
    return {
        "deployed": True,
        **deployment
    }


# =============================================================================
# GITHUB PAGES
# =============================================================================

@router.get("/github/repos/{owner}/{repo}/pages")
async def get_github_pages_status(owner: str, repo: str, user: dict = Depends(require_auth)):
    """Get GitHub Pages status for a repository"""
    github = await get_github_service(user["id"])
    if not github:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    
    try:
        status = await github.get_pages_status(owner, repo)
        return status
    except Exception as e:
        return {"enabled": False, "error": str(e)}


@router.post("/github/repos/{owner}/{repo}/pages")
async def enable_github_pages(
    owner: str, 
    repo: str,
    branch: str = "main",
    user: dict = Depends(require_auth)
):
    """Enable GitHub Pages for a repository"""
    github = await get_github_service(user["id"])
    if not github:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    
    try:
        result = await github.enable_pages(owner, repo, branch, "/")
        return {
            "success": True,
            "url": result.get("html_url"),
            "status": result.get("status")
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 409:
            return {"success": True, "message": "GitHub Pages already enabled"}
        raise HTTPException(status_code=500, detail=f"Failed to enable Pages: {str(e)}")
