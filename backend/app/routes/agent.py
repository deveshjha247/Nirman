"""
Agent Routes - Build Jobs + SSE Stream + Chat
Single chat interface API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from typing import Optional
import asyncio
import json
import uuid

from app.core.security import require_auth
from app.db.mongo import db
from app.models.build import (
    StartBuildRequest, ChatRequest, StopBuildRequest,
    BuildJob, BuildStatus, ChatMessage, Conversation
)
from app.services.agent_system import orchestrator, AgentRouter


router = APIRouter(prefix="/agent", tags=["agent"])


# =============================================================================
# SSE STREAM - Real-time job events
# =============================================================================

@router.get("/jobs/{job_id}/stream")
async def stream_job_events(job_id: str, user: dict = Depends(require_auth)):
    """Stream job events via Server-Sent Events"""
    
    # Verify job belongs to user
    job = await db.build_jobs.find_one({"id": job_id, "user_id": user['id']})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    async def event_generator():
        """Generate SSE events"""
        last_event_count = 0
        
        while True:
            # Get new events
            events = await db.build_events.find(
                {"job_id": job_id},
                {"_id": 0}
            ).sort("timestamp", 1).to_list(1000)
            
            # Send new events
            for event in events[last_event_count:]:
                yield f"data: {json.dumps(event)}\n\n"
            
            last_event_count = len(events)
            
            # Check if job is complete
            job = await db.build_jobs.find_one({"id": job_id})
            if job and job.get("status") in ["completed", "failed", "cancelled"]:
                yield f"data: {json.dumps({'type': 'stream_end', 'status': job['status']})}\n\n"
                break
            
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# =============================================================================
# BUILD JOBS
# =============================================================================

@router.post("/build")
async def start_build(request: StartBuildRequest, user: dict = Depends(require_auth)):
    """Start a new build job"""
    
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Start job and collect initial events
    events = []
    async for event in orchestrator.start_job(
        prompt=request.prompt,
        user_id=user['id'],
        project_id=request.project_id,
        model=request.model,
        provider=request.provider
    ):
        events.append(event.dict())
    
    return {
        "job_id": events[0]["job_id"] if events else job_id,
        "status": "started",
        "events": events
    }


@router.post("/build/stream")
async def start_build_stream(request: StartBuildRequest, user: dict = Depends(require_auth)):
    """Start build and stream events in real-time"""
    
    async def event_generator():
        async for event in orchestrator.start_job(
            prompt=request.prompt,
            user_id=user['id'],
            project_id=request.project_id,
            model=request.model,
            provider=request.provider
        ):
            yield f"data: {json.dumps(event.dict())}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/build/stop")
async def stop_build(request: StopBuildRequest, user: dict = Depends(require_auth)):
    """Stop a running build job"""
    
    job = await db.build_jobs.find_one({"id": request.job_id, "user_id": user['id']})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    success = await orchestrator.stop_job(request.job_id)
    
    return {"success": success, "message": "Job stopped"}


@router.get("/jobs")
async def get_jobs(
    status: Optional[str] = None,
    limit: int = Query(20, le=100),
    user: dict = Depends(require_auth)
):
    """Get user's build jobs"""
    
    query = {"user_id": user['id']}
    if status:
        query["status"] = status
    
    jobs = await db.build_jobs.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"jobs": jobs}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, user: dict = Depends(require_auth)):
    """Get job details with events"""
    
    job = await db.build_jobs.find_one(
        {"id": job_id, "user_id": user['id']},
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    events = await orchestrator.get_job_events(job_id)
    
    return {
        "job": job,
        "events": events
    }


@router.get("/jobs/{job_id}/events")
async def get_job_events(job_id: str, user: dict = Depends(require_auth)):
    """Get all events for a job"""
    
    job = await db.build_jobs.find_one({"id": job_id, "user_id": user['id']})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    events = await orchestrator.get_job_events(job_id)
    
    return {"events": events}


# =============================================================================
# CHAT / CONVERSATIONS
# =============================================================================

@router.post("/chat")
async def chat(request: ChatRequest, user: dict = Depends(require_auth)):
    """Send a chat message and get response"""
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Get or create conversation
    if request.conversation_id:
        conversation = await db.conversations.find_one({
            "id": request.conversation_id,
            "user_id": user['id']
        })
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = {
            "id": str(uuid.uuid4()),
            "user_id": user['id'],
            "project_id": request.project_id,
            "title": request.message[:50] + "..." if len(request.message) > 50 else request.message,
            "messages": [],
            "created_at": now,
            "updated_at": now
        }
        await db.conversations.insert_one(conversation)
    
    # Save user message
    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        role="user",
        content=request.message,
        timestamp=now
    )
    
    # Determine agent type
    intent = AgentRouter.classify_intent(request.message)
    
    # Start build job
    events = []
    async for event in orchestrator.start_job(
        prompt=request.message,
        user_id=user['id'],
        project_id=request.project_id or conversation.get("project_id")
    ):
        events.append(event.dict())
    
    # Extract AI response
    ai_content = ""
    code_blocks = []
    files = []
    
    for event in events:
        if event.get("type") == "ai_message":
            ai_content = event.get("message", "")
            if event.get("data"):
                code_blocks = event["data"].get("code_blocks", [])
                files = event["data"].get("files_created", [])
    
    # Save AI message
    ai_message = ChatMessage(
        id=str(uuid.uuid4()),
        job_id=events[0]["job_id"] if events else None,
        role="assistant",
        content=ai_content,
        agent=intent,
        code_blocks=code_blocks,
        files=files,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    # Update conversation
    await db.conversations.update_one(
        {"id": conversation["id"]},
        {
            "$push": {
                "messages": {
                    "$each": [user_message.dict(), ai_message.dict()]
                }
            },
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {
        "conversation_id": conversation["id"],
        "message": ai_message.dict(),
        "events": events
    }


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, user: dict = Depends(require_auth)):
    """Chat with streaming response"""
    
    async def event_generator():
        async for event in orchestrator.start_job(
            prompt=request.message,
            user_id=user['id'],
            project_id=request.project_id
        ):
            yield f"data: {json.dumps(event.dict())}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.get("/conversations")
async def get_conversations(
    limit: int = Query(20, le=50),
    user: dict = Depends(require_auth)
):
    """Get user's conversations"""
    
    conversations = await db.conversations.find(
        {"user_id": user['id']},
        {"_id": 0, "messages": {"$slice": -1}}  # Only last message
    ).sort("updated_at", -1).limit(limit).to_list(limit)
    
    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user: dict = Depends(require_auth)):
    """Get full conversation with messages"""
    
    conversation = await db.conversations.find_one(
        {"id": conversation_id, "user_id": user['id']},
        {"_id": 0}
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user: dict = Depends(require_auth)):
    """Delete a conversation"""
    
    result = await db.conversations.delete_one({
        "id": conversation_id,
        "user_id": user['id']
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"success": True}


# =============================================================================
# STATUS & INFO
# =============================================================================

@router.get("/status")
async def get_agent_status(user: dict = Depends(require_auth)):
    """Get agent system status"""
    
    # Count active jobs
    active_jobs = await db.build_jobs.count_documents({
        "user_id": user['id'],
        "status": {"$in": ["queued", "planning", "running"]}
    })
    
    # Recent jobs
    recent_jobs = await db.build_jobs.find(
        {"user_id": user['id']},
        {"_id": 0, "id": 1, "status": 1, "created_at": 1}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "status": "ready",
        "active_jobs": active_jobs,
        "recent_jobs": recent_jobs,
        "agents": ["casual", "coder", "planner", "file", "browser"]
    }


@router.get("/models")
async def get_available_models(user: dict = Depends(require_auth)):
    """Get available AI models"""
    
    # Get from AI keys
    providers = await db.ai_keys.find_one(
        {"user_id": user['id']},
        {"_id": 0}
    )
    
    available_models = []
    
    # System models (always available with platform keys)
    system_models = [
        {"provider": "openai", "model": "gpt-4o-mini", "name": "GPT-4o Mini"},
        {"provider": "openai", "model": "gpt-4o", "name": "GPT-4o"},
        {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
        {"provider": "google", "model": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
        {"provider": "deepseek", "model": "deepseek-chat", "name": "DeepSeek Chat"},
        {"provider": "groq", "model": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B"},
    ]
    
    for model in system_models:
        available_models.append({
            **model,
            "source": "platform",
            "available": True
        })
    
    # User's own keys
    if providers:
        for provider, key in providers.items():
            if provider not in ["user_id", "created_at", "updated_at"] and key:
                available_models.append({
                    "provider": provider,
                    "model": "custom",
                    "name": f"{provider.title()} (Your Key)",
                    "source": "user",
                    "available": True
                })
    
    return {"models": available_models}


@router.get("/agents")
async def get_agents_info(user: dict = Depends(require_auth)):
    """Get information about available agents"""
    
    agents = [
        {
            "type": "casual",
            "name": "Casual Agent",
            "description": "For general conversation and questions",
            "capabilities": ["chat", "answer questions", "explain concepts"]
        },
        {
            "type": "coder",
            "name": "Coder Agent",
            "description": "For writing and executing code",
            "capabilities": ["write code", "debug", "create files", "build websites"]
        },
        {
            "type": "planner",
            "name": "Planner Agent",
            "description": "For complex multi-step tasks",
            "capabilities": ["break down tasks", "coordinate agents", "execute plans"]
        },
        {
            "type": "file",
            "name": "File Agent",
            "description": "For file operations",
            "capabilities": ["create files", "organize", "search"]
        },
        {
            "type": "browser",
            "name": "Browser Agent",
            "description": "For web browsing and research",
            "capabilities": ["search web", "extract info", "browse sites"]
        }
    ]
    
    return {"agents": agents}


# =============================================================================
# PREVIEW
# =============================================================================

@router.get("/preview/{job_id}")
async def get_preview(job_id: str, user: dict = Depends(require_auth)):
    """Get preview data for a job"""
    
    job = await db.build_jobs.find_one(
        {"id": job_id, "user_id": user['id']},
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get file events
    events = await db.build_events.find(
        {"job_id": job_id, "type": "file_created"},
        {"_id": 0}
    ).to_list(100)
    
    files = {}
    for event in events:
        if event.get("data"):
            filename = event["data"].get("filename")
            code = event["data"].get("code")
            if filename and code:
                files[filename] = code
    
    # Check if it's a web project
    has_html = any(f.endswith('.html') for f in files.keys())
    
    return {
        "job_id": job_id,
        "files": files,
        "has_preview": has_html,
        "preview_type": "web" if has_html else "code"
    }
