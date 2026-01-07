"""
Supabase Integration Service
Nirman AI - Backend as a Service Integration

Features:
- Project creation and management
- Database operations (PostgreSQL)
- Authentication setup
- Storage bucket management
- Edge Functions
- Real-time subscriptions
"""

import httpx
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from app.db.mongo import db

# Supabase Configuration
SUPABASE_ACCESS_TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
SUPABASE_API_URL = "https://api.supabase.com"


async def save_supabase_integration(
    user_id: str, 
    access_token: str, 
    org_id: str,
    user_info: Dict
) -> Dict:
    """Save Supabase integration to database"""
    now = datetime.now(timezone.utc).isoformat()
    
    integration = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "integration_type": "supabase",
        "status": "connected",
        "access_token": access_token,
        "org_id": org_id,
        "provider_user_id": user_info.get("id"),
        "provider_username": user_info.get("username"),
        "provider_email": user_info.get("email"),
        "scopes": ["database", "auth", "storage", "functions"],
        "connected_at": now,
        "created_at": now,
        "updated_at": now,
    }
    
    await db.user_integrations.update_one(
        {"user_id": user_id, "integration_type": "supabase"},
        {"$set": integration},
        upsert=True
    )
    
    return integration


async def get_supabase_integration(user_id: str) -> Optional[Dict]:
    """Get user's Supabase integration"""
    return await db.user_integrations.find_one(
        {"user_id": user_id, "integration_type": "supabase"},
        {"_id": 0}
    )


async def disconnect_supabase(user_id: str) -> bool:
    """Disconnect Supabase integration"""
    result = await db.user_integrations.delete_one(
        {"user_id": user_id, "integration_type": "supabase"}
    )
    return result.deleted_count > 0


class SupabaseService:
    """
    Supabase Management API Service
    
    Handles:
    - Organization and project management
    - Database operations
    - Auth configuration
    - Storage management
    - Edge functions
    """
    
    def __init__(self, access_token: str, org_id: Optional[str] = None):
        self.access_token = access_token
        self.org_id = org_id
        self.base_url = SUPABASE_API_URL
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Supabase Management API"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=self.headers, timeout=30.0, **kwargs
            )
            response.raise_for_status()
            return response.json() if response.text else {}
    
    # =========================================================================
    # ORGANIZATION OPERATIONS
    # =========================================================================
    
    async def list_organizations(self) -> List[Dict[str, Any]]:
        """List all organizations"""
        return await self._request("GET", "/v1/organizations")
    
    async def create_organization(self, name: str) -> Dict[str, Any]:
        """Create a new organization"""
        return await self._request("POST", "/v1/organizations", json={"name": name})
    
    # =========================================================================
    # PROJECT OPERATIONS
    # =========================================================================
    
    async def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        return await self._request("GET", "/v1/projects")
    
    async def get_project(self, project_ref: str) -> Dict[str, Any]:
        """Get project details"""
        return await self._request("GET", f"/v1/projects/{project_ref}")
    
    async def create_project(
        self,
        name: str,
        organization_id: str,
        region: str = "us-east-1",
        db_password: str = None,
        plan: str = "free"
    ) -> Dict[str, Any]:
        """
        Create a new Supabase project
        
        Args:
            name: Project name
            organization_id: Organization ID
            region: Database region
            db_password: Database password (auto-generated if not provided)
            plan: Pricing plan (free, pro, team, enterprise)
        """
        import secrets
        
        data = {
            "name": name,
            "organization_id": organization_id,
            "region": region,
            "plan": plan,
            "db_pass": db_password or secrets.token_urlsafe(16)
        }
        
        return await self._request("POST", "/v1/projects", json=data)
    
    async def delete_project(self, project_ref: str) -> bool:
        """Delete a project"""
        await self._request("DELETE", f"/v1/projects/{project_ref}")
        return True
    
    async def pause_project(self, project_ref: str) -> Dict[str, Any]:
        """Pause a project (free tier)"""
        return await self._request("POST", f"/v1/projects/{project_ref}/pause")
    
    async def restore_project(self, project_ref: str) -> Dict[str, Any]:
        """Restore a paused project"""
        return await self._request("POST", f"/v1/projects/{project_ref}/restore")
    
    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================
    
    async def get_database_config(self, project_ref: str) -> Dict[str, Any]:
        """Get database configuration"""
        return await self._request("GET", f"/v1/projects/{project_ref}/database")
    
    async def run_sql(self, project_ref: str, query: str) -> Dict[str, Any]:
        """
        Execute SQL query on project database
        
        Args:
            project_ref: Project reference ID
            query: SQL query to execute
        """
        return await self._request(
            "POST",
            f"/v1/projects/{project_ref}/database/query",
            json={"query": query}
        )
    
    async def create_table(
        self,
        project_ref: str,
        table_name: str,
        columns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a database table
        
        Args:
            project_ref: Project reference ID
            table_name: Name of the table
            columns: List of column definitions
                [{"name": "id", "type": "uuid", "primary": True}, ...]
        """
        # Build CREATE TABLE SQL
        col_defs = []
        for col in columns:
            col_def = f"{col['name']} {col['type']}"
            if col.get("primary"):
                col_def += " PRIMARY KEY"
            if col.get("unique"):
                col_def += " UNIQUE"
            if col.get("not_null"):
                col_def += " NOT NULL"
            if col.get("default"):
                col_def += f" DEFAULT {col['default']}"
            col_defs.append(col_def)
        
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)});"
        return await self.run_sql(project_ref, sql)
    
    async def enable_rls(self, project_ref: str, table_name: str) -> Dict[str, Any]:
        """Enable Row Level Security on table"""
        sql = f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"
        return await self.run_sql(project_ref, sql)
    
    async def create_rls_policy(
        self,
        project_ref: str,
        table_name: str,
        policy_name: str,
        operation: str,  # SELECT, INSERT, UPDATE, DELETE, ALL
        expression: str
    ) -> Dict[str, Any]:
        """
        Create RLS policy
        
        Args:
            table_name: Target table
            policy_name: Policy name
            operation: SQL operation
            expression: Policy expression (e.g., "auth.uid() = user_id")
        """
        sql = f"""
        CREATE POLICY {policy_name} ON {table_name}
        FOR {operation}
        USING ({expression});
        """
        return await self.run_sql(project_ref, sql)
    
    # =========================================================================
    # AUTH OPERATIONS
    # =========================================================================
    
    async def get_auth_config(self, project_ref: str) -> Dict[str, Any]:
        """Get auth configuration"""
        return await self._request("GET", f"/v1/projects/{project_ref}/config/auth")
    
    async def update_auth_config(
        self,
        project_ref: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update auth configuration
        
        Config options:
        - site_url: Redirect URL
        - jwt_expiry: JWT expiration (seconds)
        - external_email_enabled: Enable email auth
        - external_phone_enabled: Enable phone auth
        - external_google_enabled: Enable Google OAuth
        """
        return await self._request(
            "PATCH",
            f"/v1/projects/{project_ref}/config/auth",
            json=config
        )
    
    async def enable_oauth_provider(
        self,
        project_ref: str,
        provider: str,
        client_id: str,
        client_secret: str
    ) -> Dict[str, Any]:
        """
        Enable OAuth provider (Google, GitHub, etc.)
        
        Providers: google, github, gitlab, discord, twitter, facebook, apple, azure, etc.
        """
        config = {
            f"external_{provider}_enabled": True,
            f"external_{provider}_client_id": client_id,
            f"external_{provider}_secret": client_secret
        }
        return await self.update_auth_config(project_ref, config)
    
    # =========================================================================
    # STORAGE OPERATIONS
    # =========================================================================
    
    async def list_buckets(self, project_ref: str) -> List[Dict[str, Any]]:
        """List storage buckets"""
        return await self._request("GET", f"/v1/projects/{project_ref}/storage/buckets")
    
    async def create_bucket(
        self,
        project_ref: str,
        name: str,
        public: bool = False,
        file_size_limit: int = 52428800,  # 50MB
        allowed_mime_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create storage bucket"""
        data = {
            "name": name,
            "public": public,
            "file_size_limit": file_size_limit
        }
        if allowed_mime_types:
            data["allowed_mime_types"] = allowed_mime_types
        
        return await self._request(
            "POST",
            f"/v1/projects/{project_ref}/storage/buckets",
            json=data
        )
    
    async def delete_bucket(self, project_ref: str, bucket_id: str) -> bool:
        """Delete storage bucket"""
        await self._request(
            "DELETE",
            f"/v1/projects/{project_ref}/storage/buckets/{bucket_id}"
        )
        return True
    
    # =========================================================================
    # EDGE FUNCTIONS
    # =========================================================================
    
    async def list_functions(self, project_ref: str) -> List[Dict[str, Any]]:
        """List edge functions"""
        return await self._request("GET", f"/v1/projects/{project_ref}/functions")
    
    async def create_function(
        self,
        project_ref: str,
        name: str,
        body: str,
        verify_jwt: bool = True
    ) -> Dict[str, Any]:
        """
        Create edge function
        
        Args:
            name: Function name (slug)
            body: Function code (TypeScript/JavaScript)
            verify_jwt: Require JWT authentication
        """
        return await self._request(
            "POST",
            f"/v1/projects/{project_ref}/functions",
            json={
                "slug": name,
                "name": name,
                "body": body,
                "verify_jwt": verify_jwt
            }
        )
    
    async def delete_function(self, project_ref: str, function_slug: str) -> bool:
        """Delete edge function"""
        await self._request(
            "DELETE",
            f"/v1/projects/{project_ref}/functions/{function_slug}"
        )
        return True
    
    # =========================================================================
    # SECRETS/ENV VARS
    # =========================================================================
    
    async def list_secrets(self, project_ref: str) -> List[Dict[str, Any]]:
        """List project secrets"""
        return await self._request("GET", f"/v1/projects/{project_ref}/secrets")
    
    async def create_secrets(
        self,
        project_ref: str,
        secrets: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Create project secrets
        
        Args:
            secrets: [{"name": "KEY", "value": "secret"}]
        """
        return await self._request(
            "POST",
            f"/v1/projects/{project_ref}/secrets",
            json=secrets
        )
    
    async def delete_secrets(
        self,
        project_ref: str,
        secret_names: List[str]
    ) -> bool:
        """Delete secrets by name"""
        await self._request(
            "DELETE",
            f"/v1/projects/{project_ref}/secrets",
            json=secret_names
        )
        return True
    
    # =========================================================================
    # API SETTINGS
    # =========================================================================
    
    async def get_api_settings(self, project_ref: str) -> Dict[str, Any]:
        """Get project API settings including keys"""
        return await self._request("GET", f"/v1/projects/{project_ref}/api-keys")
    
    async def get_postgrest_config(self, project_ref: str) -> Dict[str, Any]:
        """Get PostgREST configuration"""
        return await self._request("GET", f"/v1/projects/{project_ref}/config/postgrest")
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    async def setup_basic_project(
        self,
        name: str,
        organization_id: str,
        tables: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Quick setup a Supabase project with common configuration
        
        Args:
            name: Project name
            organization_id: Org ID
            tables: Optional table definitions
        """
        # Create project
        project = await self.create_project(name, organization_id)
        project_ref = project["ref"]
        
        # Create default tables if provided
        if tables:
            for table in tables:
                await self.create_table(
                    project_ref,
                    table["name"],
                    table["columns"]
                )
                if table.get("enable_rls"):
                    await self.enable_rls(project_ref, table["name"])
        
        # Create default storage bucket
        await self.create_bucket(project_ref, "uploads", public=False)
        
        return project
    
    def get_client_config(self, project_ref: str, anon_key: str) -> Dict[str, str]:
        """Get client-side configuration for Supabase SDK"""
        return {
            "supabase_url": f"https://{project_ref}.supabase.co",
            "supabase_anon_key": anon_key,
            "js_client": f"""
import {{ createClient }} from '@supabase/supabase-js'

const supabase = createClient(
    'https://{project_ref}.supabase.co',
    '{anon_key}'
)

export default supabase
""",
            "python_client": f"""
from supabase import create_client

supabase = create_client(
    "https://{project_ref}.supabase.co",
    "{anon_key}"
)
"""
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_supabase_service(user_id: str) -> Optional[SupabaseService]:
    """Get SupabaseService for user if connected"""
    integration = await get_supabase_integration(user_id)
    if not integration or integration.get("status") != "connected":
        return None
    return SupabaseService(
        integration["access_token"],
        integration.get("org_id")
    )
