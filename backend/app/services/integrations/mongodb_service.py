"""
MongoDB Atlas Integration Service
Nirman AI - MongoDB Cloud Database Integration

Features:
- Cluster management
- Database/collection operations
- User management
- Backup/restore
- Performance monitoring
- Data API access
"""

import httpx
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
import base64

from app.db.mongo import db

# MongoDB Atlas Configuration
MONGODB_ATLAS_PUBLIC_KEY = os.environ.get("MONGODB_ATLAS_PUBLIC_KEY", "")
MONGODB_ATLAS_PRIVATE_KEY = os.environ.get("MONGODB_ATLAS_PRIVATE_KEY", "")
MONGODB_ATLAS_GROUP_ID = os.environ.get("MONGODB_ATLAS_GROUP_ID", "")  # Project ID
MONGODB_DATA_API_KEY = os.environ.get("MONGODB_DATA_API_KEY", "")
MONGODB_DATA_API_URL = os.environ.get("MONGODB_DATA_API_URL", "")


async def save_mongodb_integration(
    user_id: str,
    public_key: str,
    private_key: str,
    group_id: str,
    org_id: Optional[str] = None
) -> Dict:
    """Save MongoDB Atlas integration to database"""
    now = datetime.now(timezone.utc).isoformat()
    
    integration = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "integration_type": "mongodb",
        "status": "connected",
        "public_key": public_key,
        "private_key": private_key,  # Encrypt in production!
        "group_id": group_id,
        "org_id": org_id,
        "scopes": ["clusters", "databases", "users", "backups"],
        "connected_at": now,
        "created_at": now,
        "updated_at": now,
    }
    
    await db.user_integrations.update_one(
        {"user_id": user_id, "integration_type": "mongodb"},
        {"$set": integration},
        upsert=True
    )
    
    return integration


async def get_mongodb_integration(user_id: str) -> Optional[Dict]:
    """Get user's MongoDB Atlas integration"""
    return await db.user_integrations.find_one(
        {"user_id": user_id, "integration_type": "mongodb"},
        {"_id": 0}
    )


async def disconnect_mongodb(user_id: str) -> bool:
    """Disconnect MongoDB Atlas integration"""
    result = await db.user_integrations.delete_one(
        {"user_id": user_id, "integration_type": "mongodb"}
    )
    return result.deleted_count > 0


class MongoDBService:
    """
    MongoDB Atlas Admin API Service
    
    Handles:
    - Cluster management
    - Database operations
    - User/role management
    - Backup management
    - Monitoring and alerts
    """
    
    CLUSTER_TIERS = {
        "M0": {"name": "Shared (Free)", "ram": "Shared", "storage": "512MB"},
        "M2": {"name": "Shared", "ram": "Shared", "storage": "2GB"},
        "M5": {"name": "Shared", "ram": "Shared", "storage": "5GB"},
        "M10": {"name": "Dedicated", "ram": "2GB", "storage": "10GB"},
        "M20": {"name": "Dedicated", "ram": "4GB", "storage": "20GB"},
        "M30": {"name": "Dedicated", "ram": "8GB", "storage": "40GB"},
        "M40": {"name": "Dedicated", "ram": "16GB", "storage": "80GB"},
    }
    
    REGIONS = {
        "us-east-1": "US East (N. Virginia)",
        "us-west-2": "US West (Oregon)",
        "eu-west-1": "EU (Ireland)",
        "eu-central-1": "EU (Frankfurt)",
        "ap-south-1": "Asia Pacific (Mumbai)",
        "ap-southeast-1": "Asia Pacific (Singapore)",
    }
    
    def __init__(self, public_key: str, private_key: str, group_id: str):
        self.public_key = public_key
        self.private_key = private_key
        self.group_id = group_id
        self.base_url = "https://cloud.mongodb.com/api/atlas/v1.0"
        
        # Digest authentication credentials
        self.auth = httpx.DigestAuth(public_key, private_key)
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Atlas API"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, auth=self.auth, timeout=30.0, **kwargs
            )
            response.raise_for_status()
            return response.json() if response.text else {}
    
    # =========================================================================
    # ORGANIZATION & PROJECT OPERATIONS
    # =========================================================================
    
    async def list_organizations(self) -> List[Dict[str, Any]]:
        """List all organizations"""
        result = await self._request("GET", "/orgs")
        return result.get("results", [])
    
    async def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects in organization"""
        result = await self._request("GET", "/groups")
        return result.get("results", [])
    
    async def get_project(self, group_id: str = None) -> Dict[str, Any]:
        """Get project details"""
        gid = group_id or self.group_id
        return await self._request("GET", f"/groups/{gid}")
    
    async def create_project(self, name: str, org_id: str) -> Dict[str, Any]:
        """Create a new project"""
        return await self._request(
            "POST",
            "/groups",
            json={"name": name, "orgId": org_id}
        )
    
    # =========================================================================
    # CLUSTER OPERATIONS
    # =========================================================================
    
    async def list_clusters(self, group_id: str = None) -> List[Dict[str, Any]]:
        """List all clusters in project"""
        gid = group_id or self.group_id
        result = await self._request("GET", f"/groups/{gid}/clusters")
        return result.get("results", [])
    
    async def get_cluster(self, cluster_name: str, group_id: str = None) -> Dict[str, Any]:
        """Get cluster details"""
        gid = group_id or self.group_id
        return await self._request("GET", f"/groups/{gid}/clusters/{cluster_name}")
    
    async def create_cluster(
        self,
        name: str,
        tier: str = "M0",
        region: str = "us-east-1",
        provider: str = "AWS",
        disk_size_gb: int = None,
        group_id: str = None
    ) -> Dict[str, Any]:
        """
        Create a new cluster
        
        Args:
            name: Cluster name
            tier: Instance size (M0, M2, M5, M10, etc.)
            region: Cloud region
            provider: Cloud provider (AWS, GCP, AZURE)
            disk_size_gb: Disk size in GB (for dedicated tiers)
        """
        gid = group_id or self.group_id
        
        data = {
            "name": name,
            "providerSettings": {
                "providerName": provider,
                "instanceSizeName": tier,
                "regionName": region
            }
        }
        
        # Free tier specific settings
        if tier == "M0":
            data["providerSettings"]["backingProviderName"] = provider
        
        if disk_size_gb and tier not in ["M0", "M2", "M5"]:
            data["diskSizeGB"] = disk_size_gb
        
        return await self._request("POST", f"/groups/{gid}/clusters", json=data)
    
    async def modify_cluster(
        self,
        cluster_name: str,
        updates: Dict[str, Any],
        group_id: str = None
    ) -> Dict[str, Any]:
        """Modify cluster settings"""
        gid = group_id or self.group_id
        return await self._request(
            "PATCH",
            f"/groups/{gid}/clusters/{cluster_name}",
            json=updates
        )
    
    async def delete_cluster(self, cluster_name: str, group_id: str = None) -> bool:
        """Delete a cluster"""
        gid = group_id or self.group_id
        await self._request("DELETE", f"/groups/{gid}/clusters/{cluster_name}")
        return True
    
    async def pause_cluster(self, cluster_name: str, group_id: str = None) -> Dict[str, Any]:
        """Pause a cluster (dedicated tiers only)"""
        return await self.modify_cluster(cluster_name, {"paused": True}, group_id)
    
    async def resume_cluster(self, cluster_name: str, group_id: str = None) -> Dict[str, Any]:
        """Resume a paused cluster"""
        return await self.modify_cluster(cluster_name, {"paused": False}, group_id)
    
    # =========================================================================
    # DATABASE USER OPERATIONS
    # =========================================================================
    
    async def list_database_users(self, group_id: str = None) -> List[Dict[str, Any]]:
        """List database users"""
        gid = group_id or self.group_id
        result = await self._request("GET", f"/groups/{gid}/databaseUsers")
        return result.get("results", [])
    
    async def create_database_user(
        self,
        username: str,
        password: str,
        database: str = "admin",
        roles: List[Dict] = None,
        group_id: str = None
    ) -> Dict[str, Any]:
        """
        Create a database user
        
        Args:
            username: Username
            password: Password
            database: Auth database
            roles: List of roles [{"roleName": "readWrite", "databaseName": "mydb"}]
        """
        gid = group_id or self.group_id
        
        if roles is None:
            roles = [{"roleName": "readWriteAnyDatabase", "databaseName": "admin"}]
        
        data = {
            "databaseName": database,
            "username": username,
            "password": password,
            "roles": roles
        }
        
        return await self._request("POST", f"/groups/{gid}/databaseUsers", json=data)
    
    async def delete_database_user(
        self,
        username: str,
        database: str = "admin",
        group_id: str = None
    ) -> bool:
        """Delete a database user"""
        gid = group_id or self.group_id
        await self._request("DELETE", f"/groups/{gid}/databaseUsers/{database}/{username}")
        return True
    
    # =========================================================================
    # IP WHITELIST OPERATIONS
    # =========================================================================
    
    async def list_ip_whitelist(self, group_id: str = None) -> List[Dict[str, Any]]:
        """List IP whitelist entries"""
        gid = group_id or self.group_id
        result = await self._request("GET", f"/groups/{gid}/accessList")
        return result.get("results", [])
    
    async def add_ip_to_whitelist(
        self,
        ip_address: str,
        comment: str = "Added by Nirman",
        group_id: str = None
    ) -> Dict[str, Any]:
        """Add IP to whitelist"""
        gid = group_id or self.group_id
        
        # Handle CIDR notation
        if "/" not in ip_address:
            ip_address = f"{ip_address}/32"
        
        return await self._request(
            "POST",
            f"/groups/{gid}/accessList",
            json=[{"cidrBlock": ip_address, "comment": comment}]
        )
    
    async def allow_all_ips(self, group_id: str = None) -> Dict[str, Any]:
        """Allow access from anywhere (0.0.0.0/0)"""
        return await self.add_ip_to_whitelist("0.0.0.0/0", "Allow all IPs", group_id)
    
    async def remove_ip_from_whitelist(self, ip_address: str, group_id: str = None) -> bool:
        """Remove IP from whitelist"""
        gid = group_id or self.group_id
        entry = ip_address.replace("/", "%2F")
        await self._request("DELETE", f"/groups/{gid}/accessList/{entry}")
        return True
    
    # =========================================================================
    # BACKUP OPERATIONS
    # =========================================================================
    
    async def list_snapshots(
        self,
        cluster_name: str,
        group_id: str = None
    ) -> List[Dict[str, Any]]:
        """List cluster snapshots"""
        gid = group_id or self.group_id
        result = await self._request(
            "GET",
            f"/groups/{gid}/clusters/{cluster_name}/backup/snapshots"
        )
        return result.get("results", [])
    
    async def create_snapshot(
        self,
        cluster_name: str,
        description: str = "Manual snapshot",
        retention_days: int = 7,
        group_id: str = None
    ) -> Dict[str, Any]:
        """Create a manual snapshot"""
        gid = group_id or self.group_id
        return await self._request(
            "POST",
            f"/groups/{gid}/clusters/{cluster_name}/backup/snapshots",
            json={"description": description, "retentionInDays": retention_days}
        )
    
    async def restore_snapshot(
        self,
        cluster_name: str,
        snapshot_id: str,
        target_cluster: str = None,
        group_id: str = None
    ) -> Dict[str, Any]:
        """Restore from snapshot"""
        gid = group_id or self.group_id
        
        data = {
            "snapshotId": snapshot_id,
            "targetClusterName": target_cluster or cluster_name,
            "targetGroupId": gid
        }
        
        return await self._request(
            "POST",
            f"/groups/{gid}/clusters/{cluster_name}/backup/restoreJobs",
            json=data
        )
    
    # =========================================================================
    # MONITORING OPERATIONS
    # =========================================================================
    
    async def get_cluster_metrics(
        self,
        cluster_name: str,
        metric: str = "CONNECTIONS",
        period: str = "PT1H",  # ISO 8601 duration
        granularity: str = "PT5M",
        group_id: str = None
    ) -> Dict[str, Any]:
        """
        Get cluster performance metrics
        
        Metrics: CONNECTIONS, OPCOUNTERS_CMD, OPCOUNTERS_QUERY, OPCOUNTERS_INSERT,
                 OPCOUNTERS_UPDATE, OPCOUNTERS_DELETE, MEMORY_RESIDENT, etc.
        """
        gid = group_id or self.group_id
        return await self._request(
            "GET",
            f"/groups/{gid}/clusters/{cluster_name}/performanceAdvisor/namespaces",
            params={"period": period, "granularity": granularity}
        )
    
    async def get_slow_queries(
        self,
        cluster_name: str,
        duration_ms: int = 100,
        group_id: str = None
    ) -> List[Dict[str, Any]]:
        """Get slow query logs"""
        gid = group_id or self.group_id
        result = await self._request(
            "GET",
            f"/groups/{gid}/clusters/{cluster_name}/performanceAdvisor/slowQueryLogs",
            params={"duration": duration_ms}
        )
        return result.get("slowQueries", [])
    
    # =========================================================================
    # CONNECTION STRING
    # =========================================================================
    
    async def get_connection_string(
        self,
        cluster_name: str,
        group_id: str = None
    ) -> Dict[str, str]:
        """Get connection strings for cluster"""
        cluster = await self.get_cluster(cluster_name, group_id)
        
        return {
            "standard": cluster.get("connectionStrings", {}).get("standard", ""),
            "standard_srv": cluster.get("connectionStrings", {}).get("standardSrv", ""),
            "private": cluster.get("connectionStrings", {}).get("private", ""),
            "private_srv": cluster.get("connectionStrings", {}).get("privateSrv", ""),
        }
    
    # =========================================================================
    # DATA API OPERATIONS (For app-level data access)
    # =========================================================================
    
    async def data_api_find(
        self,
        database: str,
        collection: str,
        filter: Dict = None,
        projection: Dict = None,
        sort: Dict = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find documents using Data API
        
        Requires MONGODB_DATA_API_KEY and MONGODB_DATA_API_URL
        """
        if not MONGODB_DATA_API_URL or not MONGODB_DATA_API_KEY:
            raise ValueError("MongoDB Data API not configured")
        
        data = {
            "dataSource": "Cluster0",  # Default cluster name
            "database": database,
            "collection": collection,
            "filter": filter or {},
            "limit": limit
        }
        
        if projection:
            data["projection"] = projection
        if sort:
            data["sort"] = sort
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MONGODB_DATA_API_URL}/action/find",
                json=data,
                headers={
                    "Content-Type": "application/json",
                    "api-key": MONGODB_DATA_API_KEY
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("documents", [])
    
    async def data_api_insert(
        self,
        database: str,
        collection: str,
        documents: List[Dict]
    ) -> Dict[str, Any]:
        """Insert documents using Data API"""
        if not MONGODB_DATA_API_URL or not MONGODB_DATA_API_KEY:
            raise ValueError("MongoDB Data API not configured")
        
        data = {
            "dataSource": "Cluster0",
            "database": database,
            "collection": collection,
            "documents": documents
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MONGODB_DATA_API_URL}/action/insertMany",
                json=data,
                headers={
                    "Content-Type": "application/json",
                    "api-key": MONGODB_DATA_API_KEY
                }
            )
            response.raise_for_status()
            return response.json()
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    async def quick_setup_cluster(
        self,
        name: str,
        username: str,
        password: str,
        tier: str = "M0"
    ) -> Dict[str, Any]:
        """
        Quick setup: Create cluster + user + allow all IPs
        """
        # Create cluster
        cluster = await self.create_cluster(name, tier)
        
        # Create database user
        await self.create_database_user(username, password)
        
        # Allow all IPs (for development)
        await self.allow_all_ips()
        
        return {
            "cluster": cluster,
            "username": username,
            "note": "Cluster is being provisioned. Connection string will be available once ready."
        }
    
    def get_client_code(self, connection_string: str, database: str) -> Dict[str, str]:
        """Generate client connection code"""
        return {
            "python": f'''
from pymongo import MongoClient

client = MongoClient("{connection_string}")
db = client["{database}"]

# Example: Insert document
result = db.users.insert_one({{"name": "John", "email": "john@example.com"}})
print(f"Inserted: {{result.inserted_id}}")

# Example: Find documents
users = db.users.find({{}})
for user in users:
    print(user)
''',
            "javascript": f'''
const {{ MongoClient }} = require('mongodb');

const uri = "{connection_string}";
const client = new MongoClient(uri);

async function run() {{
    await client.connect();
    const db = client.db("{database}");
    
    // Example: Insert document
    const result = await db.collection('users').insertOne({{
        name: "John",
        email: "john@example.com"
    }});
    console.log("Inserted:", result.insertedId);
    
    // Example: Find documents
    const users = await db.collection('users').find({{}}).toArray();
    console.log(users);
}}

run().catch(console.dir);
'''
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_mongodb_service(user_id: str) -> Optional[MongoDBService]:
    """Get MongoDBService for user if connected"""
    integration = await get_mongodb_integration(user_id)
    if not integration or integration.get("status") != "connected":
        return None
    
    return MongoDBService(
        integration["public_key"],
        integration["private_key"],
        integration["group_id"]
    )
