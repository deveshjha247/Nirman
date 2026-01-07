from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import List
import uuid

from app.core.security import require_auth
from app.db.mongo import db
from app.models.project import Project, ProjectCreate, ProjectUpdate, ChatMessage, ChatRequest
from app.services.ai_router import generate_code
from app.core.config import PLANS

router = APIRouter(tags=["projects"])

# ========== PROJECTS ==========
@router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate, user: dict = Depends(require_auth)):
    # Check project limit
    user_plan = user.get('plan', 'free')
    plan_limits = PLANS.get(user_plan, PLANS['free'])['limits']
    
    if plan_limits['projects'] != -1:
        project_count = await db.projects.count_documents({"user_id": user['id']})
        if project_count >= plan_limits['projects']:
            raise HTTPException(status_code=403, detail="Project limit reached. Upgrade to create more projects.")
    
    now = datetime.now(timezone.utc).isoformat()
    project_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user['id'],
        "name": project_data.name,
        "description": project_data.description,
        "framework": project_data.framework,
        "html_code": None,
        "css_code": None,
        "js_code": None,
        "created_at": now,
        "updated_at": now
    }
    
    await db.projects.insert_one(project_doc)
    return Project(**project_doc)

@router.get("/projects", response_model=List[Project])
async def get_projects(user: dict = Depends(require_auth)):
    projects = await db.projects.find(
        {"user_id": user['id']},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(100)
    return [Project(**p) for p in projects]

@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, user: dict = Depends(require_auth)):
    project = await db.projects.find_one(
        {"id": project_id, "user_id": user['id']},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return Project(**project)

@router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, update_data: ProjectUpdate, user: dict = Depends(require_auth)):
    project = await db.projects.find_one({"id": project_id, "user_id": user['id']})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.projects.update_one({"id": project_id}, {"$set": update_dict})
    
    updated_project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    return Project(**updated_project)

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(require_auth)):
    result = await db.projects.delete_one({"id": project_id, "user_id": user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete chat history
    await db.chat_messages.delete_many({"project_id": project_id})
    return {"message": "Project deleted successfully"}

# ========== CHAT ==========
@router.post("/chat")
async def chat_with_ai(request: ChatRequest, user: dict = Depends(require_auth)):
    # Check generation limit
    generations_limit = user.get('generations_limit', 100)
    generations_used = user.get('generations_used', 0)
    
    if generations_limit != -1 and generations_used >= generations_limit:
        raise HTTPException(status_code=403, detail="Generation limit reached. Upgrade your plan for more.")
    
    # Verify project ownership
    project = await db.projects.find_one({"id": request.project_id, "user_id": user['id']})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get recent chat history
    recent_messages = await db.chat_messages.find(
        {"project_id": request.project_id}
    ).sort("created_at", -1).limit(5).to_list(5)
    recent_messages.reverse()
    
    # Build context
    context = "\n".join([f"{m['role']}: {m['content'][:500]}" for m in recent_messages])
    full_prompt = f"Previous context:\n{context}\n\nUser request: {request.message}" if context else request.message
    
    # Generate code
    generated_code = await generate_code(
        prompt=full_prompt,
        ai_provider=request.ai_provider,
        existing_code=project.get('html_code'),
        user_id=user['id']
    )
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Save user message
    user_msg = {
        "id": str(uuid.uuid4()),
        "project_id": request.project_id,
        "role": "user",
        "content": request.message,
        "created_at": now
    }
    await db.chat_messages.insert_one(user_msg)
    
    # Save assistant message
    assistant_msg_id = str(uuid.uuid4())
    assistant_msg = {
        "id": assistant_msg_id,
        "project_id": request.project_id,
        "role": "assistant",
        "content": generated_code,
        "code_generated": generated_code,
        "ai_provider": request.ai_provider,
        "created_at": now
    }
    await db.chat_messages.insert_one(assistant_msg)
    
    # Update project code
    await db.projects.update_one(
        {"id": request.project_id},
        {"$set": {"html_code": generated_code, "updated_at": now}}
    )
    
    # Update generation count
    new_generations_used = generations_used + 1
    await db.users.update_one(
        {"id": user['id']},
        {"$set": {"generations_used": new_generations_used}}
    )
    
    return {
        "message": generated_code,
        "message_id": assistant_msg_id,
        "generations_used": new_generations_used,
        "generations_limit": generations_limit
    }

@router.get("/chat/{project_id}", response_model=List[ChatMessage])
async def get_chat_history(project_id: str, user: dict = Depends(require_auth)):
    project = await db.projects.find_one({"id": project_id, "user_id": user['id']})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    messages = await db.chat_messages.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    return [ChatMessage(**m) for m in messages]

# ========== TEMPLATES ==========
@router.get("/templates")
async def get_templates():
    return [
        {"id": "landing", "name": "Landing Page", "description": "Modern landing page with hero section", "icon": "🚀", "prompt": "Create a modern landing page with a hero section, features grid, and call-to-action"},
        {"id": "dashboard", "name": "Dashboard", "description": "Admin dashboard with charts and stats", "icon": "📊", "prompt": "Create a dashboard with sidebar navigation, stat cards, and data visualization areas"},
        {"id": "ecommerce", "name": "E-commerce", "description": "Online store product page", "icon": "🛒", "prompt": "Create an e-commerce product listing page with product cards, filters, and shopping cart"},
        {"id": "portfolio", "name": "Portfolio", "description": "Personal portfolio website", "icon": "💼", "prompt": "Create a personal portfolio with about section, project showcase, and contact form"},
        {"id": "blog", "name": "Blog", "description": "Blog with articles list", "icon": "📝", "prompt": "Create a blog homepage with featured article, article cards, and categories sidebar"},
        {"id": "saas", "name": "SaaS Landing", "description": "SaaS product landing page", "icon": "💻", "prompt": "Create a SaaS landing page with features, pricing table, testimonials, and CTA sections"}
    ]
