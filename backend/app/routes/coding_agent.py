"""
Coding Agent Routes
API endpoints for the Multi-Agent Coding System
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from app.core.security import require_auth
from app.db.mongo import db
from app.services.coding_agent import (
    process_coding_request,
    get_agent_status,
    AgentType,
    PLAN_MODELS,
)

router = APIRouter(prefix="/api/agent", tags=["coding-agent"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class AgentRequest(BaseModel):
    """Request model for coding agent"""
    prompt: str
    project_id: Optional[str] = None
    provider: str = "auto"  # auto, openai, gemini, claude, deepseek, etc.
    model: Optional[str] = None
    agent_type: Optional[str] = None  # coder, planner, browser, file


class AgentResponse(BaseModel):
    """Response model from coding agent"""
    success: bool
    answer: Optional[str] = None
    reasoning: Optional[str] = None
    code_blocks: List[dict] = []
    tokens_used: int = 0
    cost_estimate: float = 0.0
    agent_type: Optional[str] = None
    error: Optional[str] = None
    limit_reached: bool = False


class AgentStatusResponse(BaseModel):
    """Agent status and usage info"""
    plan: str
    daily_limit: int
    requests_today: int
    requests_remaining: str
    allowed_providers: List[str]
    default_provider: str
    default_model: str
    total_tokens_used: int
    total_cost: float
    total_requests: int


class ConversationMessage(BaseModel):
    """A message in conversation history"""
    role: str
    content: str
    timestamp: str
    agent_type: Optional[str] = None
    code_blocks: List[dict] = []


class ConversationRequest(BaseModel):
    """Request for conversation-style interaction"""
    prompt: str
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None
    provider: str = "auto"


# =============================================================================
# ROUTES
# =============================================================================

@router.post("/process", response_model=AgentResponse)
async def process_agent_request(
    request: AgentRequest,
    current_user: dict = Depends(require_auth),
):
    """
    Process a coding agent request.
    
    The system automatically:
    1. Analyzes the prompt to select the best agent
    2. Uses planner for complex multi-step tasks
    3. Respects plan limits and allowed providers
    4. Tracks usage for billing
    
    Example prompts:
    - "Create a React todo app with Tailwind CSS"
    - "Build a REST API with FastAPI and MongoDB"
    - "Write a Python script to process CSV files"
    
    Agent Types:
    - coder: Code generation, debugging, execution
    - browser: Web research, information extraction
    - file: File operations, organization
    - planner: Complex multi-step tasks
    - casual: General conversation
    """
    user_id = current_user["id"]
    
    result = await process_coding_request(
        prompt=request.prompt,
        user_id=user_id,
        project_id=request.project_id,
        provider=request.provider,
        model=request.model,
        agent_type=request.agent_type,
    )
    
    return AgentResponse(**result)


@router.get("/status", response_model=AgentStatusResponse)
async def get_status(
    current_user: dict = Depends(require_auth),
):
    """
    Get current agent status and usage info.
    
    Returns:
    - Current plan and limits
    - Requests made today
    - Allowed providers/models
    - Total usage statistics
    """
    user_id = current_user["id"]
    status = await get_agent_status(user_id)
    
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    
    return AgentStatusResponse(**status)


@router.get("/models")
async def get_available_models(
    current_user: dict = Depends(require_auth),
):
    """
    Get available AI models based on user's plan.
    """
    user = await db.users.find_one({"id": current_user["id"]})
    user_plan = user.get("plan", "free") if user else "free"
    plan_config = PLAN_MODELS.get(user_plan, PLAN_MODELS["free"])
    
    from app.services.ai_router import MODEL_CONFIG
    
    available_models = {}
    for provider in plan_config["allowed_providers"]:
        if provider in MODEL_CONFIG:
            available_models[provider] = {
                "models": list(MODEL_CONFIG[provider]["models"].keys()),
                "default": MODEL_CONFIG[provider]["default_model"],
            }
    
    return {
        "plan": user_plan,
        "default_provider": plan_config["default_provider"],
        "default_model": plan_config["default_model"],
        "providers": available_models,
    }


@router.get("/agents")
async def get_available_agents():
    """
    Get list of available agents with their capabilities.
    """
    return {
        "agents": [
            {
                "id": "coder",
                "name": "Coder Agent",
                "description": "Writes, debugs, and executes code in multiple languages",
                "icon": "💻",
                "capabilities": [
                    "Python, JavaScript, TypeScript, Go, Java, Rust",
                    "Full-stack web development",
                    "API development",
                    "Database operations",
                    "Code debugging and optimization"
                ],
                "example_prompts": [
                    "Create a React todo app",
                    "Build a REST API with FastAPI",
                    "Write a Python web scraper"
                ]
            },
            {
                "id": "browser",
                "name": "Browser Agent",
                "description": "Searches the web and extracts information",
                "icon": "🌐",
                "capabilities": [
                    "Web search and research",
                    "Extract data from web pages",
                    "Summarize articles and docs",
                    "Find code examples and tutorials",
                    "Compare technologies and solutions"
                ],
                "example_prompts": [
                    "Research best practices for React hooks",
                    "Find top Python libraries for data science",
                    "Search for authentication patterns"
                ]
            },
            {
                "id": "file",
                "name": "File Agent",
                "description": "Manages files and directories",
                "icon": "📁",
                "capabilities": [
                    "Create, read, update, delete files",
                    "Organize files into directories",
                    "Search for files by name/pattern",
                    "Batch file operations",
                    "Generate file listings"
                ],
                "example_prompts": [
                    "Create a project structure for a React app",
                    "Organize my files by type",
                    "Generate a README for my project"
                ]
            },
            {
                "id": "planner",
                "name": "Planner Agent",
                "description": "Plans and coordinates complex multi-step tasks",
                "icon": "🧠",
                "capabilities": [
                    "Break down complex tasks",
                    "Coordinate multiple agents",
                    "Create execution plans",
                    "Handle dependencies between steps",
                    "Manage large projects"
                ],
                "example_prompts": [
                    "Build a complete e-commerce app",
                    "Create a full-stack blog platform",
                    "Design a microservices architecture"
                ]
            },
            {
                "id": "casual",
                "name": "Casual Agent",
                "description": "General conversation and explanations",
                "icon": "💬",
                "capabilities": [
                    "Answer general questions",
                    "Explain concepts clearly",
                    "Provide advice and suggestions",
                    "Brainstorming sessions",
                    "Casual conversation"
                ],
                "example_prompts": [
                    "Explain how React hooks work",
                    "What's the difference between REST and GraphQL?",
                    "Help me brainstorm app ideas"
                ]
            }
        ]
    }


@router.post("/conversation")
async def conversation_interaction(
    request: ConversationRequest,
    current_user: dict = Depends(require_auth),
):
    """
    Handle conversation-style interactions with memory.
    
    Creates or continues a conversation with the coding agent.
    The agent remembers previous messages in the conversation.
    """
    user_id = current_user["id"]
    now = datetime.now(timezone.utc).isoformat()
    
    # Get or create conversation
    if request.conversation_id:
        conversation = await db.agent_conversations.find_one({
            "id": request.conversation_id,
            "user_id": user_id,
        })
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation
        import uuid
        conversation = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "project_id": request.project_id,
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        await db.agent_conversations.insert_one(conversation)
    
    # Add user message
    user_message = {
        "role": "user",
        "content": request.prompt,
        "timestamp": now,
    }
    
    # Process with agent
    result = await process_coding_request(
        prompt=request.prompt,
        user_id=user_id,
        project_id=request.project_id,
        provider=request.provider,
    )
    
    # Add assistant message
    assistant_message = {
        "role": "assistant",
        "content": result.get("answer", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_type": result.get("agent_type"),
        "code_blocks": result.get("code_blocks", []),
    }
    
    # Update conversation
    await db.agent_conversations.update_one(
        {"id": conversation["id"]},
        {
            "$push": {
                "messages": {
                    "$each": [user_message, assistant_message]
                }
            },
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {
        "success": result.get("success", False),
        "conversation_id": conversation["id"],
        "message": assistant_message,
        "tokens_used": result.get("tokens_used", 0),
        "cost_estimate": result.get("cost_estimate", 0),
        "error": result.get("error"),
    }


@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(require_auth),
):
    """Get conversation history."""
    user_id = current_user["id"]
    
    conversation = await db.agent_conversations.find_one({
        "id": conversation_id,
        "user_id": user_id,
    })
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "id": conversation["id"],
        "project_id": conversation.get("project_id"),
        "messages": conversation.get("messages", []),
        "created_at": conversation["created_at"],
        "updated_at": conversation["updated_at"],
    }


@router.get("/conversations")
async def list_conversations(
    project_id: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    current_user: dict = Depends(require_auth),
):
    """List user's conversations."""
    user_id = current_user["id"]
    
    query = {"user_id": user_id}
    if project_id:
        query["project_id"] = project_id
    
    conversations = await db.agent_conversations.find(
        query,
        {"messages": {"$slice": -1}}  # Only last message for preview
    ).sort("updated_at", -1).limit(limit).to_list(limit)
    
    return {
        "conversations": [
            {
                "id": c["id"],
                "project_id": c.get("project_id"),
                "preview": c["messages"][-1]["content"][:100] if c.get("messages") else "",
                "message_count": len(c.get("messages", [])),
                "created_at": c["created_at"],
                "updated_at": c["updated_at"],
            }
            for c in conversations
        ]
    }


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(require_auth),
):
    """Delete a conversation."""
    user_id = current_user["id"]
    
    result = await db.agent_conversations.delete_one({
        "id": conversation_id,
        "user_id": user_id,
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"success": True, "message": "Conversation deleted"}


@router.get("/usage/history")
async def get_usage_history(
    days: int = Query(default=30, le=90),
    current_user: dict = Depends(require_auth),
):
    """Get usage history for the user."""
    from datetime import timedelta
    
    user_id = current_user["id"]
    start_date = (
        datetime.now(timezone.utc) - timedelta(days=days)
    ).isoformat()
    
    # Aggregate by day
    pipeline = [
        {
            "$match": {
                "user_id": user_id,
                "created_at": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": {"$substr": ["$created_at", 0, 10]},  # Group by date
                "requests": {"$sum": 1},
                "tokens": {"$sum": "$tokens_used"},
                "cost": {"$sum": "$cost_estimate"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    
    daily_usage = await db.ai_runs.aggregate(pipeline).to_list(days)
    
    # By provider
    provider_pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": start_date}}},
        {
            "$group": {
                "_id": "$provider",
                "requests": {"$sum": 1},
                "tokens": {"$sum": "$tokens_used"},
                "cost": {"$sum": "$cost_estimate"},
            }
        },
    ]
    
    by_provider = await db.ai_runs.aggregate(provider_pipeline).to_list(20)
    
    return {
        "daily": [
            {
                "date": d["_id"],
                "requests": d["requests"],
                "tokens": d["tokens"],
                "cost": round(d["cost"], 4),
            }
            for d in daily_usage
        ],
        "by_provider": [
            {
                "provider": p["_id"],
                "requests": p["requests"],
                "tokens": p["tokens"],
                "cost": round(p["cost"], 4),
            }
            for p in by_provider
        ],
    }


@router.get("/plans")
async def get_agent_plans():
    """
    Get available plans and their features.
    Public endpoint for displaying pricing.
    """
    plans = []
    for plan_id, config in PLAN_MODELS.items():
        plans.append({
            "id": plan_id,
            "name": plan_id.title(),
            "daily_limit": config["daily_limit"] if config["daily_limit"] != -1 else "Unlimited",
            "max_tokens": config["max_tokens"],
            "default_provider": config["default_provider"],
            "default_model": config["default_model"],
            "providers_count": len(config["allowed_providers"]),
            "allowed_providers": config["allowed_providers"],
        })
    
    return {"plans": plans}
