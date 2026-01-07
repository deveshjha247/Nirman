"""
Extended Integrations Routes
Nirman AI - Vercel, Supabase, Firebase, Canva, MongoDB, Razorpay, Cashfree
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from datetime import datetime, timezone
import uuid
import os

from app.core.security import require_auth
from app.db.mongo import db

# Import integration services
from app.services.integrations.vercel_service import (
    VercelService,
    get_vercel_oauth_url,
    exchange_vercel_code_for_token,
    save_vercel_integration,
    get_vercel_integration,
    get_vercel_service,
    disconnect_vercel,
    VERCEL_CLIENT_ID
)
from app.services.integrations.supabase_service import (
    SupabaseService,
    save_supabase_integration,
    get_supabase_integration,
    get_supabase_service,
    disconnect_supabase
)
from app.services.integrations.firebase_service import (
    FirebaseService,
    save_firebase_integration,
    get_firebase_integration,
    get_firebase_service,
    disconnect_firebase
)
from app.services.integrations.canva_service import (
    CanvaService,
    get_canva_oauth_url,
    exchange_canva_code_for_token,
    save_canva_integration,
    get_canva_integration,
    get_canva_service,
    disconnect_canva,
    CANVA_CLIENT_ID
)
from app.services.integrations.mongodb_service import (
    MongoDBService,
    save_mongodb_integration,
    get_mongodb_integration,
    get_mongodb_service,
    disconnect_mongodb
)
from app.services.integrations.razorpay_service import (
    RazorpayService,
    save_razorpay_integration,
    get_razorpay_integration,
    get_razorpay_service,
    disconnect_razorpay,
    get_app_razorpay
)
from app.services.integrations.cashfree_service import (
    CashfreeService,
    save_cashfree_integration,
    get_cashfree_integration,
    get_cashfree_service,
    disconnect_cashfree,
    get_app_cashfree
)

router = APIRouter(prefix="/integrations", tags=["integrations-extended"])


# =============================================================================
# VERCEL INTEGRATION
# =============================================================================

@router.get("/vercel/auth-url")
async def get_vercel_auth_url(user: dict = Depends(require_auth)):
    """Get Vercel OAuth authorization URL"""
    if not VERCEL_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Vercel integration not configured"
        )
    
    state = f"{user['id']}:{uuid.uuid4()}"
    await db.oauth_states.insert_one({
        "state": state,
        "user_id": user["id"],
        "provider": "vercel",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    auth_url = get_vercel_oauth_url(state)
    return {"auth_url": auth_url}


@router.post("/vercel/callback")
async def vercel_oauth_callback(
    code: str,
    state: str,
    user: dict = Depends(require_auth)
):
    """Handle Vercel OAuth callback"""
    stored_state = await db.oauth_states.find_one({"state": state, "user_id": user["id"]})
    if not stored_state:
        raise HTTPException(status_code=400, detail="Invalid or expired state")
    
    await db.oauth_states.delete_one({"_id": stored_state["_id"]})
    
    try:
        token_data = await exchange_vercel_code_for_token(code)
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data.get("error_description", "OAuth failed"))
        
        access_token = token_data["access_token"]
        team_id = token_data.get("team_id")
        
        vercel = VercelService(access_token, team_id)
        vercel_user = await vercel.get_user()
        
        await save_vercel_integration(user["id"], access_token, team_id, vercel_user.get("user", {}))
        
        return {
            "success": True,
            "message": f"Successfully connected Vercel",
            "username": vercel_user.get("user", {}).get("username")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect Vercel: {str(e)}")


@router.delete("/vercel")
async def disconnect_vercel_integration(user: dict = Depends(require_auth)):
    """Disconnect Vercel integration"""
    success = await disconnect_vercel(user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Vercel integration not found")
    return {"success": True, "message": "Vercel disconnected"}


@router.get("/vercel/status")
async def get_vercel_status(user: dict = Depends(require_auth)):
    """Get Vercel integration status"""
    integration = await get_vercel_integration(user["id"])
    if not integration or integration.get("status") != "connected":
        return {"connected": False}
    
    return {
        "connected": True,
        "username": integration.get("provider_username"),
        "connected_at": integration.get("connected_at")
    }


@router.get("/vercel/projects")
async def list_vercel_projects(user: dict = Depends(require_auth)):
    """List Vercel projects"""
    vercel = await get_vercel_service(user["id"])
    if not vercel:
        raise HTTPException(status_code=401, detail="Vercel not connected")
    
    projects = await vercel.list_projects()
    return {"projects": projects}


@router.post("/vercel/deploy")
async def deploy_to_vercel(
    project_id: str,
    user: dict = Depends(require_auth)
):
    """Deploy Nirman project to Vercel"""
    vercel = await get_vercel_service(user["id"])
    if not vercel:
        raise HTTPException(status_code=401, detail="Vercel not connected")
    
    project = await db.projects.find_one({"id": project_id, "user_id": user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    code = project.get("code", {})
    files = []
    
    if isinstance(code, dict):
        for path, content in code.items():
            files.append({"file": path, "data": content})
    elif isinstance(code, str):
        files.append({"file": "index.html", "data": code})
    
    deployment = await vercel.create_deployment(
        name=project.get("name", "nirman-project").lower().replace(" ", "-"),
        files=files,
        target="production"
    )
    
    return {
        "success": True,
        "deployment_id": deployment.get("id"),
        "url": deployment.get("url"),
        "ready_state": deployment.get("readyState")
    }


# =============================================================================
# SUPABASE INTEGRATION
# =============================================================================

@router.post("/supabase/connect")
async def connect_supabase(
    access_token: str,
    org_id: str = None,
    user: dict = Depends(require_auth)
):
    """Connect Supabase with access token"""
    try:
        supabase = SupabaseService(access_token, org_id)
        
        # Verify token by listing projects
        projects = await supabase.list_projects()
        
        await save_supabase_integration(
            user["id"],
            access_token,
            org_id or "",
            {"id": user["id"], "username": user.get("email")}
        )
        
        return {
            "success": True,
            "message": "Successfully connected Supabase",
            "projects_count": len(projects)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {str(e)}")


@router.delete("/supabase")
async def disconnect_supabase_integration(user: dict = Depends(require_auth)):
    """Disconnect Supabase integration"""
    success = await disconnect_supabase(user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Supabase integration not found")
    return {"success": True, "message": "Supabase disconnected"}


@router.get("/supabase/status")
async def get_supabase_status(user: dict = Depends(require_auth)):
    """Get Supabase integration status"""
    integration = await get_supabase_integration(user["id"])
    if not integration or integration.get("status") != "connected":
        return {"connected": False}
    
    return {
        "connected": True,
        "org_id": integration.get("org_id"),
        "connected_at": integration.get("connected_at")
    }


@router.get("/supabase/projects")
async def list_supabase_projects(user: dict = Depends(require_auth)):
    """List Supabase projects"""
    supabase = await get_supabase_service(user["id"])
    if not supabase:
        raise HTTPException(status_code=401, detail="Supabase not connected")
    
    projects = await supabase.list_projects()
    return {"projects": projects}


@router.post("/supabase/projects")
async def create_supabase_project(
    name: str,
    organization_id: str,
    region: str = "us-east-1",
    user: dict = Depends(require_auth)
):
    """Create a new Supabase project"""
    supabase = await get_supabase_service(user["id"])
    if not supabase:
        raise HTTPException(status_code=401, detail="Supabase not connected")
    
    project = await supabase.create_project(name, organization_id, region)
    return {"success": True, "project": project}


# =============================================================================
# FIREBASE INTEGRATION
# =============================================================================

@router.post("/firebase/connect")
async def connect_firebase(
    project_id: str,
    service_account_json: str,
    user: dict = Depends(require_auth)
):
    """Connect Firebase with service account"""
    import json
    
    try:
        service_account = json.loads(service_account_json)
        
        await save_firebase_integration(
            user["id"],
            service_account,
            project_id
        )
        
        return {
            "success": True,
            "message": f"Successfully connected Firebase project: {project_id}"
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid service account JSON")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {str(e)}")


@router.delete("/firebase")
async def disconnect_firebase_integration(user: dict = Depends(require_auth)):
    """Disconnect Firebase integration"""
    success = await disconnect_firebase(user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Firebase integration not found")
    return {"success": True, "message": "Firebase disconnected"}


@router.get("/firebase/status")
async def get_firebase_status(user: dict = Depends(require_auth)):
    """Get Firebase integration status"""
    integration = await get_firebase_integration(user["id"])
    if not integration or integration.get("status") != "connected":
        return {"connected": False}
    
    return {
        "connected": True,
        "project_id": integration.get("project_id"),
        "connected_at": integration.get("connected_at")
    }


@router.post("/firebase/deploy")
async def deploy_to_firebase(
    project_id: str,
    user: dict = Depends(require_auth)
):
    """Deploy Nirman project to Firebase Hosting"""
    firebase = await get_firebase_service(user["id"])
    if not firebase:
        raise HTTPException(status_code=401, detail="Firebase not connected")
    
    project = await db.projects.find_one({"id": project_id, "user_id": user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    code = project.get("code", {})
    files = {}
    
    if isinstance(code, dict):
        files = code
    elif isinstance(code, str):
        files = {"index.html": code}
    
    integration = await get_firebase_integration(user["id"])
    site_id = integration.get("project_id")
    
    result = await firebase.deploy_site(site_id, files)
    
    return {
        "success": True,
        "url": result.get("url"),
        "version": result.get("version")
    }


# =============================================================================
# CANVA INTEGRATION
# =============================================================================

@router.get("/canva/auth-url")
async def get_canva_auth_url(user: dict = Depends(require_auth)):
    """Get Canva OAuth authorization URL"""
    if not CANVA_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Canva integration not configured"
        )
    
    state = f"{user['id']}:{uuid.uuid4()}"
    await db.oauth_states.insert_one({
        "state": state,
        "user_id": user["id"],
        "provider": "canva",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    auth_url = get_canva_oauth_url(state)
    return {"auth_url": auth_url}


@router.delete("/canva")
async def disconnect_canva_integration(user: dict = Depends(require_auth)):
    """Disconnect Canva integration"""
    success = await disconnect_canva(user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Canva integration not found")
    return {"success": True, "message": "Canva disconnected"}


@router.get("/canva/status")
async def get_canva_status(user: dict = Depends(require_auth)):
    """Get Canva integration status"""
    integration = await get_canva_integration(user["id"])
    if not integration or integration.get("status") != "connected":
        return {"connected": False}
    
    return {
        "connected": True,
        "username": integration.get("provider_username"),
        "connected_at": integration.get("connected_at")
    }


@router.get("/canva/designs")
async def list_canva_designs(user: dict = Depends(require_auth)):
    """List Canva designs"""
    canva = await get_canva_service(user["id"])
    if not canva:
        raise HTTPException(status_code=401, detail="Canva not connected")
    
    designs = await canva.list_designs()
    return designs


@router.post("/canva/designs")
async def create_canva_design(
    design_type: str = "poster",
    title: str = None,
    user: dict = Depends(require_auth)
):
    """Create a new Canva design"""
    canva = await get_canva_service(user["id"])
    if not canva:
        raise HTTPException(status_code=401, detail="Canva not connected")
    
    design = await canva.create_design(design_type=design_type, title=title)
    return {
        "success": True,
        "design": design,
        "edit_url": canva.get_design_edit_url(design.get("design", {}).get("id"))
    }


# =============================================================================
# MONGODB ATLAS INTEGRATION
# =============================================================================

@router.post("/mongodb/connect")
async def connect_mongodb(
    public_key: str,
    private_key: str,
    group_id: str,
    org_id: str = None,
    user: dict = Depends(require_auth)
):
    """Connect MongoDB Atlas"""
    try:
        mongodb = MongoDBService(public_key, private_key, group_id)
        
        # Verify credentials by getting project info
        project = await mongodb.get_project()
        
        await save_mongodb_integration(
            user["id"],
            public_key,
            private_key,
            group_id,
            org_id
        )
        
        return {
            "success": True,
            "message": f"Successfully connected MongoDB Atlas project: {project.get('name')}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {str(e)}")


@router.delete("/mongodb")
async def disconnect_mongodb_integration(user: dict = Depends(require_auth)):
    """Disconnect MongoDB Atlas integration"""
    success = await disconnect_mongodb(user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="MongoDB integration not found")
    return {"success": True, "message": "MongoDB Atlas disconnected"}


@router.get("/mongodb/status")
async def get_mongodb_status(user: dict = Depends(require_auth)):
    """Get MongoDB Atlas integration status"""
    integration = await get_mongodb_integration(user["id"])
    if not integration or integration.get("status") != "connected":
        return {"connected": False}
    
    return {
        "connected": True,
        "group_id": integration.get("group_id"),
        "connected_at": integration.get("connected_at")
    }


@router.get("/mongodb/clusters")
async def list_mongodb_clusters(user: dict = Depends(require_auth)):
    """List MongoDB Atlas clusters"""
    mongodb = await get_mongodb_service(user["id"])
    if not mongodb:
        raise HTTPException(status_code=401, detail="MongoDB Atlas not connected")
    
    clusters = await mongodb.list_clusters()
    return {"clusters": clusters}


@router.post("/mongodb/clusters")
async def create_mongodb_cluster(
    name: str,
    tier: str = "M0",
    region: str = "us-east-1",
    user: dict = Depends(require_auth)
):
    """Create a new MongoDB Atlas cluster"""
    mongodb = await get_mongodb_service(user["id"])
    if not mongodb:
        raise HTTPException(status_code=401, detail="MongoDB Atlas not connected")
    
    cluster = await mongodb.create_cluster(name, tier, region)
    return {"success": True, "cluster": cluster}


# =============================================================================
# RAZORPAY INTEGRATION
# =============================================================================

@router.post("/razorpay/connect")
async def connect_razorpay(
    key_id: str,
    key_secret: str,
    user: dict = Depends(require_auth)
):
    """Connect Razorpay"""
    try:
        # Verify credentials by creating a test order
        razorpay = RazorpayService(key_id, key_secret)
        
        await save_razorpay_integration(user["id"], key_id, key_secret)
        
        return {
            "success": True,
            "message": "Successfully connected Razorpay"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {str(e)}")


@router.delete("/razorpay")
async def disconnect_razorpay_integration(user: dict = Depends(require_auth)):
    """Disconnect Razorpay integration"""
    success = await disconnect_razorpay(user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Razorpay integration not found")
    return {"success": True, "message": "Razorpay disconnected"}


@router.get("/razorpay/status")
async def get_razorpay_status(user: dict = Depends(require_auth)):
    """Get Razorpay integration status"""
    integration = await get_razorpay_integration(user["id"])
    if not integration or integration.get("status") != "connected":
        return {"connected": False}
    
    return {
        "connected": True,
        "key_id": integration.get("key_id", "")[:10] + "***",
        "connected_at": integration.get("connected_at")
    }


@router.post("/razorpay/orders")
async def create_razorpay_order(
    amount: int,
    currency: str = "INR",
    receipt: str = None,
    user: dict = Depends(require_auth)
):
    """Create a Razorpay order"""
    razorpay = await get_razorpay_service(user["id"])
    if not razorpay:
        raise HTTPException(status_code=401, detail="Razorpay not connected")
    
    order = await razorpay.create_order(amount, currency, receipt)
    return {"success": True, "order": order}


@router.post("/razorpay/verify")
async def verify_razorpay_payment(
    order_id: str,
    payment_id: str,
    signature: str,
    user: dict = Depends(require_auth)
):
    """Verify Razorpay payment signature"""
    razorpay = await get_razorpay_service(user["id"])
    if not razorpay:
        raise HTTPException(status_code=401, detail="Razorpay not connected")
    
    is_valid = razorpay.verify_payment_signature(order_id, payment_id, signature)
    
    if is_valid:
        # Record successful payment
        await db.payments.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "provider": "razorpay",
            "order_id": order_id,
            "payment_id": payment_id,
            "status": "captured",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return {"valid": is_valid, "payment_id": payment_id}


@router.post("/razorpay/subscriptions/plans")
async def create_razorpay_plan(
    period: str,
    interval: int,
    name: str,
    amount: int,
    user: dict = Depends(require_auth)
):
    """Create a Razorpay subscription plan"""
    razorpay = await get_razorpay_service(user["id"])
    if not razorpay:
        raise HTTPException(status_code=401, detail="Razorpay not connected")
    
    plan = await razorpay.create_plan(period, interval, name, amount)
    return {"success": True, "plan": plan}


# =============================================================================
# CASHFREE INTEGRATION
# =============================================================================

@router.post("/cashfree/connect")
async def connect_cashfree(
    app_id: str,
    secret_key: str,
    user: dict = Depends(require_auth)
):
    """Connect Cashfree"""
    try:
        await save_cashfree_integration(user["id"], app_id, secret_key)
        
        return {
            "success": True,
            "message": "Successfully connected Cashfree"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {str(e)}")


@router.delete("/cashfree")
async def disconnect_cashfree_integration(user: dict = Depends(require_auth)):
    """Disconnect Cashfree integration"""
    success = await disconnect_cashfree(user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Cashfree integration not found")
    return {"success": True, "message": "Cashfree disconnected"}


@router.get("/cashfree/status")
async def get_cashfree_status(user: dict = Depends(require_auth)):
    """Get Cashfree integration status"""
    integration = await get_cashfree_integration(user["id"])
    if not integration or integration.get("status") != "connected":
        return {"connected": False}
    
    return {
        "connected": True,
        "app_id": integration.get("app_id", "")[:10] + "***",
        "connected_at": integration.get("connected_at")
    }


@router.post("/cashfree/orders")
async def create_cashfree_order(
    order_id: str,
    order_amount: float,
    customer_phone: str,
    customer_email: str = None,
    return_url: str = None,
    user: dict = Depends(require_auth)
):
    """Create a Cashfree order"""
    cashfree = await get_cashfree_service(user["id"])
    if not cashfree:
        raise HTTPException(status_code=401, detail="Cashfree not connected")
    
    customer_details = {"customer_phone": customer_phone}
    if customer_email:
        customer_details["customer_email"] = customer_email
    customer_details["customer_id"] = f"cust_{uuid.uuid4().hex[:8]}"
    
    order_meta = {}
    if return_url:
        order_meta["return_url"] = return_url
    
    order = await cashfree.create_order(
        order_id=order_id,
        order_amount=order_amount,
        customer_details=customer_details,
        order_meta=order_meta if order_meta else None
    )
    
    return {
        "success": True,
        "order": order,
        "payment_session_id": order.get("payment_session_id")
    }


@router.post("/cashfree/quick-payment")
async def create_quick_payment(
    amount: float,
    customer_phone: str,
    customer_email: str = None,
    return_url: str = None,
    user: dict = Depends(require_auth)
):
    """Create a quick Cashfree payment"""
    cashfree = await get_cashfree_service(user["id"])
    if not cashfree:
        raise HTTPException(status_code=401, detail="Cashfree not connected")
    
    result = await cashfree.create_quick_payment(
        amount=amount,
        customer_phone=customer_phone,
        customer_email=customer_email,
        return_url=return_url
    )
    
    return result


@router.post("/cashfree/payment-link")
async def create_cashfree_payment_link(
    link_id: str,
    link_amount: float,
    link_purpose: str = "Payment",
    customer_phone: str = None,
    user: dict = Depends(require_auth)
):
    """Create a Cashfree payment link"""
    cashfree = await get_cashfree_service(user["id"])
    if not cashfree:
        raise HTTPException(status_code=401, detail="Cashfree not connected")
    
    customer_details = None
    if customer_phone:
        customer_details = {"customer_phone": customer_phone}
    
    link = await cashfree.create_payment_link(
        link_id=link_id,
        link_amount=link_amount,
        link_purpose=link_purpose,
        customer_details=customer_details
    )
    
    return {"success": True, "link": link}


# =============================================================================
# WEBHOOKS
# =============================================================================

@router.post("/razorpay/webhook")
async def razorpay_webhook(request: Request):
    """Handle Razorpay webhooks"""
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    
    try:
        razorpay = get_app_razorpay()
        if not razorpay.verify_webhook_signature(body.decode(), signature):
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        payload = await request.json()
        event = payload.get("event")
        
        # Handle different events
        if event == "payment.captured":
            payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
            await db.webhook_events.insert_one({
                "provider": "razorpay",
                "event": event,
                "payment_id": payment.get("id"),
                "data": payload,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cashfree/webhook")
async def cashfree_webhook(request: Request):
    """Handle Cashfree webhooks"""
    body = await request.body()
    timestamp = request.headers.get("x-webhook-timestamp", "")
    signature = request.headers.get("x-webhook-signature", "")
    
    try:
        cashfree = get_app_cashfree()
        if not cashfree.verify_webhook_signature(timestamp, body.decode(), signature):
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        payload = await request.json()
        event_type = payload.get("type")
        
        await db.webhook_events.insert_one({
            "provider": "cashfree",
            "event": event_type,
            "data": payload,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# INTEGRATION STATUS OVERVIEW
# =============================================================================

@router.get("/all-status")
async def get_all_integrations_status(user: dict = Depends(require_auth)):
    """Get status of all integrations"""
    integrations = await db.user_integrations.find(
        {"user_id": user["id"]},
        {"_id": 0, "access_token": 0, "secret_key": 0, "key_secret": 0, "private_key": 0}
    ).to_list(20)
    
    status_map = {i["integration_type"]: i for i in integrations}
    
    all_integrations = [
        {
            "id": "github",
            "name": "GitHub",
            "icon": "🐙",
            "category": "deployment",
            "connected": status_map.get("github", {}).get("status") == "connected",
            "description": "Push code, create repos, deploy to GitHub Pages"
        },
        {
            "id": "vercel",
            "name": "Vercel",
            "icon": "▲",
            "category": "deployment",
            "connected": status_map.get("vercel", {}).get("status") == "connected",
            "description": "Deploy with preview URLs and custom domains"
        },
        {
            "id": "supabase",
            "name": "Supabase",
            "icon": "⚡",
            "category": "backend",
            "connected": status_map.get("supabase", {}).get("status") == "connected",
            "description": "PostgreSQL database, auth, storage"
        },
        {
            "id": "firebase",
            "name": "Firebase",
            "icon": "🔥",
            "category": "backend",
            "connected": status_map.get("firebase", {}).get("status") == "connected",
            "description": "Hosting, Firestore, Auth, Storage"
        },
        {
            "id": "mongodb",
            "name": "MongoDB Atlas",
            "icon": "🍃",
            "category": "database",
            "connected": status_map.get("mongodb", {}).get("status") == "connected",
            "description": "Cloud MongoDB clusters and databases"
        },
        {
            "id": "canva",
            "name": "Canva",
            "icon": "🎨",
            "category": "design",
            "connected": status_map.get("canva", {}).get("status") == "connected",
            "description": "Create and export designs"
        },
        {
            "id": "razorpay",
            "name": "Razorpay",
            "icon": "💳",
            "category": "payments",
            "connected": status_map.get("razorpay", {}).get("status") == "connected",
            "description": "Accept payments in India"
        },
        {
            "id": "cashfree",
            "name": "Cashfree",
            "icon": "💰",
            "category": "payments",
            "connected": status_map.get("cashfree", {}).get("status") == "connected",
            "description": "Payment gateway & payouts"
        }
    ]
    
    return {
        "integrations": all_integrations,
        "connected_count": sum(1 for i in all_integrations if i["connected"]),
        "categories": {
            "deployment": [i for i in all_integrations if i["category"] == "deployment"],
            "backend": [i for i in all_integrations if i["category"] == "backend"],
            "database": [i for i in all_integrations if i["category"] == "database"],
            "design": [i for i in all_integrations if i["category"] == "design"],
            "payments": [i for i in all_integrations if i["category"] == "payments"],
        }
    }
