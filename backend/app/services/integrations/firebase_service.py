"""
Firebase Integration Service
Nirman AI - Google Firebase Platform Integration

Features:
- Firebase Hosting deployment
- Firestore database operations
- Firebase Authentication
- Cloud Storage
- Cloud Functions
- Real-time Database
"""

import httpx
import os
import json
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from app.db.mongo import db

# Firebase Configuration
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")
FIREBASE_SERVICE_ACCOUNT = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")  # JSON string
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")


async def save_firebase_integration(
    user_id: str,
    service_account: Dict,
    project_id: str
) -> Dict:
    """Save Firebase integration to database"""
    now = datetime.now(timezone.utc).isoformat()
    
    integration = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "integration_type": "firebase",
        "status": "connected",
        "service_account": service_account,
        "project_id": project_id,
        "provider_email": service_account.get("client_email"),
        "scopes": ["hosting", "firestore", "auth", "storage", "functions"],
        "connected_at": now,
        "created_at": now,
        "updated_at": now,
    }
    
    await db.user_integrations.update_one(
        {"user_id": user_id, "integration_type": "firebase"},
        {"$set": integration},
        upsert=True
    )
    
    return integration


async def get_firebase_integration(user_id: str) -> Optional[Dict]:
    """Get user's Firebase integration"""
    return await db.user_integrations.find_one(
        {"user_id": user_id, "integration_type": "firebase"},
        {"_id": 0}
    )


async def disconnect_firebase(user_id: str) -> bool:
    """Disconnect Firebase integration"""
    result = await db.user_integrations.delete_one(
        {"user_id": user_id, "integration_type": "firebase"}
    )
    return result.deleted_count > 0


class FirebaseService:
    """
    Firebase Admin Service
    
    Handles:
    - Hosting deployments
    - Firestore CRUD operations
    - Auth user management
    - Storage operations
    - Cloud Functions deployment
    """
    
    def __init__(self, project_id: str, access_token: str):
        self.project_id = project_id
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make authenticated request"""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=self.headers, timeout=60.0, **kwargs
            )
            response.raise_for_status()
            return response.json() if response.text else {}
    
    # =========================================================================
    # HOSTING OPERATIONS
    # =========================================================================
    
    async def list_sites(self) -> List[Dict[str, Any]]:
        """List hosting sites"""
        url = f"https://firebasehosting.googleapis.com/v1beta1/projects/{self.project_id}/sites"
        result = await self._request("GET", url)
        return result.get("sites", [])
    
    async def create_site(self, site_id: str) -> Dict[str, Any]:
        """Create a new hosting site"""
        url = f"https://firebasehosting.googleapis.com/v1beta1/projects/{self.project_id}/sites"
        return await self._request("POST", url, params={"siteId": site_id})
    
    async def create_version(self, site_id: str) -> Dict[str, Any]:
        """Create a new version for deployment"""
        url = f"https://firebasehosting.googleapis.com/v1beta1/sites/{site_id}/versions"
        return await self._request("POST", url, json={"config": {}})
    
    async def upload_files(
        self,
        site_id: str,
        version_name: str,
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Upload files for deployment
        
        Args:
            site_id: Hosting site ID
            version_name: Version resource name
            files: Dict of {path: content}
        """
        # Populate files
        file_hashes = {}
        for path, content in files.items():
            # Calculate SHA256 hash
            import hashlib
            content_bytes = content.encode() if isinstance(content, str) else content
            hash_value = hashlib.sha256(content_bytes).hexdigest()
            file_hashes[f"/{path}"] = hash_value
        
        url = f"https://firebasehosting.googleapis.com/v1beta1/{version_name}:populateFiles"
        result = await self._request("POST", url, json={"files": file_hashes})
        
        # Upload each file to the upload URL
        upload_url = result.get("uploadUrl")
        if upload_url:
            for path, content in files.items():
                content_bytes = content.encode() if isinstance(content, str) else content
                hash_value = hashlib.sha256(content_bytes).hexdigest()
                
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{upload_url}/{hash_value}",
                        content=content_bytes,
                        headers={
                            "Authorization": f"Bearer {self.access_token}",
                            "Content-Type": "application/octet-stream"
                        }
                    )
        
        return result
    
    async def finalize_version(self, version_name: str) -> Dict[str, Any]:
        """Finalize version after upload"""
        url = f"https://firebasehosting.googleapis.com/v1beta1/{version_name}?update_mask=status"
        return await self._request("PATCH", url, json={"status": "FINALIZED"})
    
    async def release_version(self, site_id: str, version_name: str) -> Dict[str, Any]:
        """Release version to live"""
        url = f"https://firebasehosting.googleapis.com/v1beta1/sites/{site_id}/releases"
        return await self._request("POST", url, json={"version": {"name": version_name}})
    
    async def deploy_site(
        self,
        site_id: str,
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Full deployment flow: create version -> upload -> finalize -> release
        
        Args:
            site_id: Hosting site ID
            files: Dict of {path: content}
        
        Returns:
            Deployment result with URL
        """
        # Create version
        version = await self.create_version(site_id)
        version_name = version["name"]
        
        # Upload files
        await self.upload_files(site_id, version_name, files)
        
        # Finalize
        await self.finalize_version(version_name)
        
        # Release
        release = await self.release_version(site_id, version_name)
        
        return {
            "success": True,
            "version": version_name,
            "url": f"https://{site_id}.web.app",
            "release": release
        }
    
    # =========================================================================
    # FIRESTORE OPERATIONS
    # =========================================================================
    
    @property
    def firestore_url(self) -> str:
        return f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents"
    
    async def get_document(self, collection: str, doc_id: str) -> Dict[str, Any]:
        """Get a Firestore document"""
        url = f"{self.firestore_url}/{collection}/{doc_id}"
        return await self._request("GET", url)
    
    async def create_document(
        self,
        collection: str,
        data: Dict[str, Any],
        doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Firestore document
        
        Args:
            collection: Collection name
            data: Document data
            doc_id: Optional document ID (auto-generated if not provided)
        """
        # Convert Python dict to Firestore fields format
        fields = self._to_firestore_fields(data)
        
        url = f"{self.firestore_url}/{collection}"
        params = {}
        if doc_id:
            params["documentId"] = doc_id
        
        return await self._request("POST", url, json={"fields": fields}, params=params)
    
    async def update_document(
        self,
        collection: str,
        doc_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a Firestore document"""
        fields = self._to_firestore_fields(data)
        url = f"{self.firestore_url}/{collection}/{doc_id}"
        
        # Build update mask
        update_mask = ",".join(data.keys())
        
        return await self._request(
            "PATCH",
            url,
            json={"fields": fields},
            params={"updateMask.fieldPaths": list(data.keys())}
        )
    
    async def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a Firestore document"""
        url = f"{self.firestore_url}/{collection}/{doc_id}"
        await self._request("DELETE", url)
        return True
    
    async def query_collection(
        self,
        collection: str,
        filters: List[Dict] = None,
        order_by: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query Firestore collection
        
        Args:
            collection: Collection name
            filters: [{"field": "name", "op": "==", "value": "test"}]
            order_by: Field to order by
            limit: Max documents to return
        """
        query = {
            "structuredQuery": {
                "from": [{"collectionId": collection}],
                "limit": limit
            }
        }
        
        if filters:
            where_clauses = []
            for f in filters:
                where_clauses.append({
                    "fieldFilter": {
                        "field": {"fieldPath": f["field"]},
                        "op": self._get_firestore_op(f["op"]),
                        "value": self._to_firestore_value(f["value"])
                    }
                })
            
            if len(where_clauses) == 1:
                query["structuredQuery"]["where"] = where_clauses[0]
            else:
                query["structuredQuery"]["where"] = {
                    "compositeFilter": {
                        "op": "AND",
                        "filters": where_clauses
                    }
                }
        
        if order_by:
            query["structuredQuery"]["orderBy"] = [
                {"field": {"fieldPath": order_by}, "direction": "ASCENDING"}
            ]
        
        url = f"{self.firestore_url}:runQuery"
        result = await self._request("POST", url, json=query)
        
        documents = []
        for item in result:
            if "document" in item:
                doc = item["document"]
                doc_data = self._from_firestore_fields(doc.get("fields", {}))
                doc_data["_id"] = doc["name"].split("/")[-1]
                documents.append(doc_data)
        
        return documents
    
    def _to_firestore_fields(self, data: Dict) -> Dict:
        """Convert Python dict to Firestore fields format"""
        fields = {}
        for key, value in data.items():
            fields[key] = self._to_firestore_value(value)
        return fields
    
    def _to_firestore_value(self, value: Any) -> Dict:
        """Convert Python value to Firestore value"""
        if value is None:
            return {"nullValue": None}
        elif isinstance(value, bool):
            return {"booleanValue": value}
        elif isinstance(value, int):
            return {"integerValue": str(value)}
        elif isinstance(value, float):
            return {"doubleValue": value}
        elif isinstance(value, str):
            return {"stringValue": value}
        elif isinstance(value, list):
            return {"arrayValue": {"values": [self._to_firestore_value(v) for v in value]}}
        elif isinstance(value, dict):
            return {"mapValue": {"fields": self._to_firestore_fields(value)}}
        else:
            return {"stringValue": str(value)}
    
    def _from_firestore_fields(self, fields: Dict) -> Dict:
        """Convert Firestore fields to Python dict"""
        result = {}
        for key, value in fields.items():
            result[key] = self._from_firestore_value(value)
        return result
    
    def _from_firestore_value(self, value: Dict) -> Any:
        """Convert Firestore value to Python value"""
        if "nullValue" in value:
            return None
        elif "booleanValue" in value:
            return value["booleanValue"]
        elif "integerValue" in value:
            return int(value["integerValue"])
        elif "doubleValue" in value:
            return value["doubleValue"]
        elif "stringValue" in value:
            return value["stringValue"]
        elif "arrayValue" in value:
            return [self._from_firestore_value(v) for v in value["arrayValue"].get("values", [])]
        elif "mapValue" in value:
            return self._from_firestore_fields(value["mapValue"].get("fields", {}))
        return None
    
    def _get_firestore_op(self, op: str) -> str:
        """Convert operator to Firestore operator"""
        ops = {
            "==": "EQUAL",
            "!=": "NOT_EQUAL",
            "<": "LESS_THAN",
            "<=": "LESS_THAN_OR_EQUAL",
            ">": "GREATER_THAN",
            ">=": "GREATER_THAN_OR_EQUAL",
            "in": "IN",
            "not-in": "NOT_IN",
            "array-contains": "ARRAY_CONTAINS",
            "array-contains-any": "ARRAY_CONTAINS_ANY"
        }
        return ops.get(op, "EQUAL")
    
    # =========================================================================
    # AUTH OPERATIONS
    # =========================================================================
    
    @property
    def auth_url(self) -> str:
        return f"https://identitytoolkit.googleapis.com/v1"
    
    async def list_users(self, max_results: int = 100) -> List[Dict[str, Any]]:
        """List Firebase Auth users"""
        url = f"https://identitytoolkit.googleapis.com/v1/projects/{self.project_id}/accounts:batchGet"
        result = await self._request("POST", url, json={"maxResults": max_results})
        return result.get("users", [])
    
    async def get_user(self, uid: str) -> Dict[str, Any]:
        """Get user by UID"""
        url = f"https://identitytoolkit.googleapis.com/v1/projects/{self.project_id}/accounts:lookup"
        result = await self._request("POST", url, json={"localId": [uid]})
        users = result.get("users", [])
        return users[0] if users else None
    
    async def create_user(
        self,
        email: str,
        password: str,
        display_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        disabled: bool = False
    ) -> Dict[str, Any]:
        """Create a new Firebase Auth user"""
        url = f"https://identitytoolkit.googleapis.com/v1/projects/{self.project_id}/accounts"
        
        data = {
            "email": email,
            "password": password,
            "disabled": disabled
        }
        if display_name:
            data["displayName"] = display_name
        if phone_number:
            data["phoneNumber"] = phone_number
        
        return await self._request("POST", url, json=data)
    
    async def update_user(self, uid: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user properties"""
        url = f"https://identitytoolkit.googleapis.com/v1/projects/{self.project_id}/accounts:update"
        updates["localId"] = uid
        return await self._request("POST", url, json=updates)
    
    async def delete_user(self, uid: str) -> bool:
        """Delete a user"""
        url = f"https://identitytoolkit.googleapis.com/v1/projects/{self.project_id}/accounts:delete"
        await self._request("POST", url, json={"localId": uid})
        return True
    
    # =========================================================================
    # STORAGE OPERATIONS
    # =========================================================================
    
    @property
    def storage_bucket(self) -> str:
        return f"{self.project_id}.appspot.com"
    
    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in storage"""
        url = f"https://storage.googleapis.com/storage/v1/b/{self.storage_bucket}/o"
        params = {"prefix": prefix} if prefix else {}
        result = await self._request("GET", url, params=params)
        return result.get("items", [])
    
    async def upload_file(
        self,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream"
    ) -> Dict[str, Any]:
        """Upload file to storage"""
        url = f"https://storage.googleapis.com/upload/storage/v1/b/{self.storage_bucket}/o"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params={"uploadType": "media", "name": path},
                content=content,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": content_type
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_file_url(self, path: str) -> str:
        """Get public URL for file"""
        return f"https://storage.googleapis.com/{self.storage_bucket}/{path}"
    
    async def delete_file(self, path: str) -> bool:
        """Delete file from storage"""
        url = f"https://storage.googleapis.com/storage/v1/b/{self.storage_bucket}/o/{path}"
        await self._request("DELETE", url)
        return True
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_client_config(self) -> Dict[str, str]:
        """Get client-side Firebase configuration"""
        return {
            "js_config": f"""
// Firebase configuration
const firebaseConfig = {{
    apiKey: "{FIREBASE_API_KEY}",
    authDomain: "{self.project_id}.firebaseapp.com",
    projectId: "{self.project_id}",
    storageBucket: "{self.project_id}.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
}};

// Initialize Firebase
import {{ initializeApp }} from 'firebase/app';
import {{ getFirestore }} from 'firebase/firestore';
import {{ getAuth }} from 'firebase/auth';
import {{ getStorage }} from 'firebase/storage';

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
export const auth = getAuth(app);
export const storage = getStorage(app);
"""
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_firebase_service(user_id: str) -> Optional[FirebaseService]:
    """Get FirebaseService for user if connected"""
    integration = await get_firebase_integration(user_id)
    if not integration or integration.get("status") != "connected":
        return None
    
    # Get access token from service account
    # In production, use google-auth library to generate token
    return FirebaseService(
        integration["project_id"],
        integration.get("access_token", "")
    )
