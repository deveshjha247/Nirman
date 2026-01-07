"""
Canva Integration Service
Nirman AI - Canva Design Platform Integration

Features:
- Design creation and editing
- Template browsing
- Asset management
- Export designs
- Brand kit integration
"""

import httpx
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from app.db.mongo import db

# Canva Configuration
CANVA_CLIENT_ID = os.environ.get("CANVA_CLIENT_ID", "")
CANVA_CLIENT_SECRET = os.environ.get("CANVA_CLIENT_SECRET", "")
CANVA_REDIRECT_URI = os.environ.get("CANVA_REDIRECT_URI", "http://localhost:3000/integrations")
CANVA_API_URL = "https://api.canva.com/rest/v1"


def get_canva_oauth_url(state: str) -> str:
    """Generate Canva OAuth URL"""
    scopes = [
        "design:content:read",
        "design:content:write",
        "design:meta:read",
        "asset:read",
        "asset:write",
        "brandtemplate:content:read",
        "brandtemplate:meta:read",
        "folder:read",
        "folder:write",
        "profile:read"
    ]
    
    params = {
        "response_type": "code",
        "client_id": CANVA_CLIENT_ID,
        "redirect_uri": CANVA_REDIRECT_URI,
        "state": state,
        "scope": " ".join(scopes),
        "code_challenge_method": "S256"
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://www.canva.com/api/oauth/authorize?{query}"


async def exchange_canva_code_for_token(code: str, code_verifier: str) -> Dict[str, Any]:
    """Exchange OAuth code for access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.canva.com/rest/v1/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": CANVA_CLIENT_ID,
                "client_secret": CANVA_CLIENT_SECRET,
                "code": code,
                "code_verifier": code_verifier,
                "redirect_uri": CANVA_REDIRECT_URI
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json()


async def refresh_canva_token(refresh_token: str) -> Dict[str, Any]:
    """Refresh access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.canva.com/rest/v1/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": CANVA_CLIENT_ID,
                "client_secret": CANVA_CLIENT_SECRET,
                "refresh_token": refresh_token
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json()


async def save_canva_integration(
    user_id: str,
    access_token: str,
    refresh_token: str,
    expires_in: int,
    user_info: Dict
) -> Dict:
    """Save Canva integration to database"""
    now = datetime.now(timezone.utc)
    expires_at = datetime.fromtimestamp(now.timestamp() + expires_in, tz=timezone.utc)
    
    integration = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "integration_type": "canva",
        "status": "connected",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_expires_at": expires_at.isoformat(),
        "provider_user_id": user_info.get("id"),
        "provider_username": user_info.get("display_name"),
        "provider_email": user_info.get("email"),
        "provider_avatar": user_info.get("profile_photo_url"),
        "scopes": ["design", "asset", "brand", "folder", "profile"],
        "connected_at": now.isoformat(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    await db.user_integrations.update_one(
        {"user_id": user_id, "integration_type": "canva"},
        {"$set": integration},
        upsert=True
    )
    
    return integration


async def get_canva_integration(user_id: str) -> Optional[Dict]:
    """Get user's Canva integration"""
    return await db.user_integrations.find_one(
        {"user_id": user_id, "integration_type": "canva"},
        {"_id": 0}
    )


async def disconnect_canva(user_id: str) -> bool:
    """Disconnect Canva integration"""
    result = await db.user_integrations.delete_one(
        {"user_id": user_id, "integration_type": "canva"}
    )
    return result.deleted_count > 0


class CanvaService:
    """
    Canva API Service
    
    Handles:
    - Design creation and management
    - Template browsing
    - Asset uploads
    - Export operations
    - Brand kit access
    """
    
    DESIGN_TYPES = {
        "poster": {"width": 1080, "height": 1920, "title": "Poster"},
        "instagram_post": {"width": 1080, "height": 1080, "title": "Instagram Post"},
        "instagram_story": {"width": 1080, "height": 1920, "title": "Instagram Story"},
        "facebook_post": {"width": 1200, "height": 630, "title": "Facebook Post"},
        "twitter_post": {"width": 1600, "height": 900, "title": "Twitter Post"},
        "linkedin_post": {"width": 1200, "height": 627, "title": "LinkedIn Post"},
        "youtube_thumbnail": {"width": 1280, "height": 720, "title": "YouTube Thumbnail"},
        "presentation": {"width": 1920, "height": 1080, "title": "Presentation"},
        "logo": {"width": 500, "height": 500, "title": "Logo"},
        "business_card": {"width": 1050, "height": 600, "title": "Business Card"},
        "flyer": {"width": 1275, "height": 1650, "title": "Flyer"},
        "resume": {"width": 816, "height": 1056, "title": "Resume"},
        "infographic": {"width": 800, "height": 2000, "title": "Infographic"},
    }
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = CANVA_API_URL
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Canva API"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=self.headers, timeout=60.0, **kwargs
            )
            response.raise_for_status()
            return response.json() if response.text else {}
    
    # =========================================================================
    # USER OPERATIONS
    # =========================================================================
    
    async def get_user(self) -> Dict[str, Any]:
        """Get authenticated user profile"""
        return await self._request("GET", "/users/me")
    
    # =========================================================================
    # DESIGN OPERATIONS
    # =========================================================================
    
    async def list_designs(self, limit: int = 50, continuation: str = None) -> Dict[str, Any]:
        """List user's designs"""
        params = {"limit": limit}
        if continuation:
            params["continuation"] = continuation
        
        return await self._request("GET", "/designs", params=params)
    
    async def get_design(self, design_id: str) -> Dict[str, Any]:
        """Get design details"""
        return await self._request("GET", f"/designs/{design_id}")
    
    async def create_design(
        self,
        design_type: str = "poster",
        title: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        asset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new design
        
        Args:
            design_type: Preset type (poster, instagram_post, etc.)
            title: Design title
            width: Custom width (overrides preset)
            height: Custom height (overrides preset)
            asset_id: Optional starting asset
        """
        # Get preset dimensions
        preset = self.DESIGN_TYPES.get(design_type, self.DESIGN_TYPES["poster"])
        
        data = {
            "design_type": {
                "width": width or preset["width"],
                "height": height or preset["height"]
            }
        }
        
        if title:
            data["title"] = title
        elif preset:
            data["title"] = f"New {preset['title']}"
        
        if asset_id:
            data["asset_id"] = asset_id
        
        return await self._request("POST", "/designs", json=data)
    
    async def delete_design(self, design_id: str) -> bool:
        """Delete a design"""
        await self._request("DELETE", f"/designs/{design_id}")
        return True
    
    # =========================================================================
    # EXPORT OPERATIONS
    # =========================================================================
    
    async def export_design(
        self,
        design_id: str,
        format: str = "png",
        quality: str = "regular",
        pages: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Export design to image/PDF
        
        Args:
            design_id: Design ID to export
            format: Export format (png, jpg, pdf, svg, gif, pptx, mp4)
            quality: Image quality (regular, high)
            pages: Specific pages to export (for multi-page designs)
        """
        data = {
            "format": format,
            "quality": quality
        }
        
        if pages:
            data["pages"] = pages
        
        return await self._request("POST", f"/designs/{design_id}/exports", json=data)
    
    async def get_export_status(self, design_id: str, export_id: str) -> Dict[str, Any]:
        """Check export job status"""
        return await self._request("GET", f"/designs/{design_id}/exports/{export_id}")
    
    async def wait_for_export(
        self,
        design_id: str,
        export_id: str,
        max_wait: int = 60
    ) -> Dict[str, Any]:
        """Wait for export to complete and return download URL"""
        import asyncio
        
        for _ in range(max_wait):
            result = await self.get_export_status(design_id, export_id)
            status = result.get("status")
            
            if status == "completed":
                return result
            elif status == "failed":
                raise Exception(f"Export failed: {result.get('error', 'Unknown error')}")
            
            await asyncio.sleep(1)
        
        raise TimeoutError("Export timed out")
    
    # =========================================================================
    # ASSET OPERATIONS
    # =========================================================================
    
    async def upload_asset(
        self,
        name: str,
        content: bytes,
        content_type: str = "image/png"
    ) -> Dict[str, Any]:
        """
        Upload an asset (image, video, etc.)
        
        Args:
            name: Asset name/filename
            content: File content as bytes
            content_type: MIME type
        """
        # Start upload job
        job = await self._request(
            "POST",
            "/asset-uploads",
            json={"name": name}
        )
        
        upload_url = job.get("upload_url")
        job_id = job.get("id")
        
        if upload_url:
            # Upload content
            async with httpx.AsyncClient() as client:
                await client.put(
                    upload_url,
                    content=content,
                    headers={"Content-Type": content_type}
                )
        
        return await self._request("GET", f"/asset-uploads/{job_id}")
    
    async def list_assets(
        self,
        asset_type: str = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """List user's assets"""
        params = {"limit": limit}
        if asset_type:
            params["type"] = asset_type
        
        return await self._request("GET", "/assets", params=params)
    
    async def get_asset(self, asset_id: str) -> Dict[str, Any]:
        """Get asset details"""
        return await self._request("GET", f"/assets/{asset_id}")
    
    async def delete_asset(self, asset_id: str) -> bool:
        """Delete an asset"""
        await self._request("DELETE", f"/assets/{asset_id}")
        return True
    
    # =========================================================================
    # FOLDER OPERATIONS
    # =========================================================================
    
    async def list_folders(self, parent_id: str = None, limit: int = 50) -> Dict[str, Any]:
        """List folders"""
        params = {"limit": limit}
        if parent_id:
            params["parent_id"] = parent_id
        
        return await self._request("GET", "/folders", params=params)
    
    async def create_folder(self, name: str, parent_id: str = None) -> Dict[str, Any]:
        """Create a folder"""
        data = {"name": name}
        if parent_id:
            data["parent_id"] = parent_id
        
        return await self._request("POST", "/folders", json=data)
    
    async def move_design_to_folder(self, design_id: str, folder_id: str) -> Dict[str, Any]:
        """Move design to folder"""
        return await self._request(
            "POST",
            f"/designs/{design_id}/move",
            json={"folder_id": folder_id}
        )
    
    # =========================================================================
    # BRAND TEMPLATE OPERATIONS
    # =========================================================================
    
    async def list_brand_templates(self, limit: int = 50) -> Dict[str, Any]:
        """List brand templates"""
        return await self._request("GET", "/brand-templates", params={"limit": limit})
    
    async def get_brand_template(self, template_id: str) -> Dict[str, Any]:
        """Get brand template details"""
        return await self._request("GET", f"/brand-templates/{template_id}")
    
    async def create_design_from_template(
        self,
        template_id: str,
        title: str = None
    ) -> Dict[str, Any]:
        """Create design from brand template"""
        data = {"brand_template_id": template_id}
        if title:
            data["title"] = title
        
        return await self._request("POST", "/designs", json=data)
    
    # =========================================================================
    # AUTOFILL OPERATIONS
    # =========================================================================
    
    async def autofill_design(
        self,
        design_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Autofill design with data
        
        Args:
            design_id: Target design
            data: Key-value pairs for autofill fields
        """
        return await self._request(
            "POST",
            f"/designs/{design_id}/autofill",
            json={"data": data}
        )
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    async def create_social_media_set(
        self,
        title_prefix: str,
        platforms: List[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create designs for multiple social media platforms
        
        Args:
            title_prefix: Prefix for design titles
            platforms: List of platforms (instagram_post, facebook_post, etc.)
        """
        if platforms is None:
            platforms = ["instagram_post", "instagram_story", "facebook_post", "twitter_post"]
        
        designs = {}
        for platform in platforms:
            if platform in self.DESIGN_TYPES:
                design = await self.create_design(
                    design_type=platform,
                    title=f"{title_prefix} - {self.DESIGN_TYPES[platform]['title']}"
                )
                designs[platform] = design
        
        return designs
    
    def get_design_edit_url(self, design_id: str) -> str:
        """Get URL to edit design in Canva"""
        return f"https://www.canva.com/design/{design_id}/edit"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_canva_service(user_id: str) -> Optional[CanvaService]:
    """Get CanvaService for user if connected"""
    integration = await get_canva_integration(user_id)
    if not integration or integration.get("status") != "connected":
        return None
    
    # Check if token needs refresh
    expires_at = integration.get("token_expires_at")
    if expires_at:
        expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) >= expires_dt:
            # Refresh token
            refresh_token = integration.get("refresh_token")
            if refresh_token:
                new_tokens = await refresh_canva_token(refresh_token)
                if "access_token" in new_tokens:
                    await db.user_integrations.update_one(
                        {"user_id": user_id, "integration_type": "canva"},
                        {
                            "$set": {
                                "access_token": new_tokens["access_token"],
                                "refresh_token": new_tokens.get("refresh_token", refresh_token),
                                "token_expires_at": datetime.fromtimestamp(
                                    datetime.now(timezone.utc).timestamp() + new_tokens.get("expires_in", 3600),
                                    tz=timezone.utc
                                ).isoformat(),
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    )
                    return CanvaService(new_tokens["access_token"])
    
    return CanvaService(integration["access_token"])
