"""
Agent Chat Routes - Single Chat Interface
SSE Streaming for live progress updates
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator
import uuid
import json
import asyncio

from app.core.security import require_auth
from app.db.mongo import db
from app.models.jobs import BuildJob, BuildEvent, BuildEventType, BuildJobStatus, AgentType
from app.services.ai_router import generate_code

router = APIRouter(tags=["agent"])


# =============================================================================
# Event Queue for SSE Streaming
# =============================================================================

class EventManager:
    """Manages SSE event queues for jobs"""
    def __init__(self):
        self.queues: dict[str, asyncio.Queue] = {}
    
    def get_queue(self, job_id: str) -> asyncio.Queue:
        if job_id not in self.queues:
            self.queues[job_id] = asyncio.Queue()
        return self.queues[job_id]
    
    async def push_event(self, job_id: str, event: dict):
        if job_id in self.queues:
            await self.queues[job_id].put(event)
    
    def cleanup(self, job_id: str):
        if job_id in self.queues:
            del self.queues[job_id]


event_manager = EventManager()


async def create_event(
    job_id: str, 
    event_type: BuildEventType, 
    message: str, 
    payload: dict = None,
    progress: int = None
) -> dict:
    """Create and store a build event"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Get sequence number
    count = await db.build_events.count_documents({"job_id": job_id})
    
    event = {
        "id": str(uuid.uuid4()),
        "job_id": job_id,
        "seq": count + 1,
        "type": event_type.value if isinstance(event_type, BuildEventType) else event_type,
        "message": message,
        "payload": payload or {},
        "progress": progress,
        "created_at": now
    }
    
    # Store in database
    await db.build_events.insert_one(event)
    
    # Push to SSE queue
    await event_manager.push_event(job_id, event)
    
    # Update job progress if provided
    if progress is not None:
        await db.build_jobs.update_one(
            {"id": job_id},
            {"$set": {"progress": progress, "updated_at": now}}
        )
    
    return event


# =============================================================================
# Agent Router Logic
# =============================================================================

def classify_query(query: str) -> AgentType:
    """Classify query to determine which agent to use"""
    query_lower = query.lower()
    
    # Code-related patterns
    code_patterns = [
        "write", "create", "build", "code", "program", "script", "function",
        "class", "api", "website", "app", "application", "html", "css", "js",
        "python", "javascript", "react", "node", "flask", "django", "fastapi",
        "database", "sql", "mongodb", "component", "page", "implement",
        "generate code", "make a", "develop", "frontend", "backend"
    ]
    
    # Browser-related patterns
    browser_patterns = [
        "search", "browse", "find out", "look up", "google", "web search",
        "latest news", "research", "check website", "visit", "open url",
        "navigate to", "who is", "what is the latest"
    ]
    
    # File-related patterns
    file_patterns = [
        "file", "folder", "directory", "organize", "move", "copy", "delete",
        "rename", "find file", "locate", "create folder", "list files"
    ]
    
    # MCP-related patterns
    mcp_patterns = [
        "mcp", "tool", "use mcp", "calendar", "contacts", "stock",
        "market", "weather", "external tool"
    ]
    
    # Planning patterns (complex multi-step tasks)
    planning_patterns = [
        "plan", "step by step", "multiple", "and then", "first", "after that",
        "complex", "comprehensive", "full", "complete project", "entire"
    ]
    
    # Check patterns
    if any(p in query_lower for p in planning_patterns):
        return AgentType.PLANNER
    if any(p in query_lower for p in code_patterns):
        return AgentType.CODER
    if any(p in query_lower for p in browser_patterns):
        return AgentType.BROWSER
    if any(p in query_lower for p in file_patterns):
        return AgentType.FILE
    if any(p in query_lower for p in mcp_patterns):
        return AgentType.MCP
    
    return AgentType.CASUAL


async def process_job(job_id: str, user: dict, query: str, project_id: str = None):
    """Background task to process a job with streaming events"""
    now = datetime.now(timezone.utc).isoformat()
    
    try:
        # Update job status
        await db.build_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": BuildJobStatus.RUNNING.value,
                "started_at": now,
                "updated_at": now
            }}
        )
        
        # Send job started event
        await create_event(job_id, BuildEventType.JOB_STARTED, "Job started", progress=5)
        
        # Classify query and select agent
        agent_type = classify_query(query)
        await db.build_jobs.update_one(
            {"id": job_id},
            {"$set": {"current_agent": agent_type.value, "updated_at": now}}
        )
        
        await create_event(
            job_id, 
            BuildEventType.AGENT_SELECTED, 
            f"Selected {agent_type.value} agent",
            payload={"agent": agent_type.value},
            progress=10
        )
        
        # Thinking phase
        await create_event(job_id, BuildEventType.AGENT_THINKING, "Agent is thinking...", progress=15)
        await asyncio.sleep(0.5)  # Simulate thinking
        
        # Process based on agent type
        response = None
        code_blocks = []
        has_preview = False
        preview_url = None
        
        if agent_type == AgentType.CODER:
            response, code_blocks, has_preview, preview_url = await process_coder_task(
                job_id, user, query, project_id
            )
        elif agent_type == AgentType.BROWSER:
            response = await process_browser_task(job_id, user, query)
        elif agent_type == AgentType.FILE:
            response = await process_file_task(job_id, user, query)
        elif agent_type == AgentType.MCP:
            response = await process_mcp_task(job_id, user, query)
        elif agent_type == AgentType.PLANNER:
            response, code_blocks = await process_planner_task(job_id, user, query, project_id)
        else:
            response = await process_casual_task(job_id, user, query)
        
        # Job completed
        await db.build_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": BuildJobStatus.SUCCESS.value,
                "response": response,
                "code_blocks": code_blocks,
                "has_preview": has_preview,
                "preview_url": preview_url,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "progress": 100,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        await create_event(
            job_id, 
            BuildEventType.JOB_COMPLETED, 
            "Job completed successfully",
            payload={"response": response[:500] if response else None},
            progress=100
        )
        
    except Exception as e:
        error_msg = str(e)
        await db.build_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": BuildJobStatus.FAILED.value,
                "error_message": error_msg,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        await create_event(
            job_id, 
            BuildEventType.ERROR, 
            f"Job failed: {error_msg}",
            payload={"error": error_msg}
        )
    
    finally:
        # Cleanup after delay
        await asyncio.sleep(30)
        event_manager.cleanup(job_id)


async def process_coder_task(job_id: str, user: dict, query: str, project_id: str = None):
    """Process coding task"""
    code_blocks = []
    has_preview = False
    preview_url = None
    
    await create_event(job_id, BuildEventType.CODEGEN_STARTED, "Starting code generation...", progress=20)
    
    # Generate code
    await create_event(job_id, BuildEventType.CODEGEN_PROGRESS, "Generating code...", progress=40)
    
    system_prompt = """You are an expert programmer. Generate clean, well-documented code based on the user's request.
    
For web projects, include:
- HTML structure
- CSS styling  
- JavaScript functionality

Always wrap code in appropriate markdown code blocks with language tags."""
    
    try:
        # Call AI with Gemini as default
        full_prompt = f"{system_prompt}\n\nUser request: {query}"
        response_text = await generate_code(
            prompt=full_prompt,
            ai_provider="gemini",
            user_id=user['id']
        )
        
        await create_event(job_id, BuildEventType.CODEGEN_PROGRESS, "Code generated", progress=60)
        
        # Extract code blocks from response
        import re
        code_pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(code_pattern, response_text, re.DOTALL)
        
        for i, (lang, code) in enumerate(matches):
            block = {
                "id": str(uuid.uuid4()),
                "language": lang or "text",
                "code": code.strip(),
                "filename": f"file_{i+1}.{lang or 'txt'}"
            }
            code_blocks.append(block)
            
            await create_event(
                job_id, 
                BuildEventType.FILE_CREATED, 
                f"Created {block['filename']}",
                payload={"file": block['filename'], "language": lang},
                progress=60 + (i * 5)
            )
        
        # Check if web preview is possible
        has_html = any(b['language'] in ['html', 'htm'] for b in code_blocks)
        if has_html:
            has_preview = True
            preview_url = f"/api/preview/{job_id}"
            await create_event(
                job_id, 
                BuildEventType.PREVIEW_READY, 
                "Preview ready",
                payload={"preview_url": preview_url},
                progress=90
            )
        
        return response_text, code_blocks, has_preview, preview_url
        
    except Exception as e:
        await create_event(job_id, BuildEventType.CODE_ERROR, f"Code generation failed: {str(e)}")
        return f"Error generating code: {str(e)}", [], False, None


async def process_browser_task(job_id: str, user: dict, query: str):
    """Process browser/search task"""
    await create_event(job_id, BuildEventType.BROWSER_NAVIGATING, "Searching the web...", progress=30)
    
    # Simulate browser search (in production, use actual search)
    await asyncio.sleep(1)
    
    await create_event(job_id, BuildEventType.INFO, "Processing search results...", progress=60)
    
    system_prompt = """You are a helpful assistant that can search and summarize web information.
Based on the user's query, provide a helpful, informative response.
If you don't know something, say so honestly."""
    
    try:
        full_prompt = f"{system_prompt}\n\nWeb search query: {query}"
        response_text = await generate_code(
            prompt=full_prompt,
            ai_provider="gemini",
            user_id=user['id']
        )
        
        await create_event(job_id, BuildEventType.INFO, "Search completed", progress=90)
        return response_text or 'Could not process search'
        
    except Exception as e:
        return f"Search error: {str(e)}"


async def process_file_task(job_id: str, user: dict, query: str):
    """Process file management task"""
    await create_event(job_id, BuildEventType.INFO, "Processing file operation...", progress=30)
    
    system_prompt = """You are a file management assistant. Help users with file operations.
Describe the steps needed or provide guidance for file management tasks."""
    
    try:
        full_prompt = f"{system_prompt}\n\nUser request: {query}"
        response_text = await generate_code(
            prompt=full_prompt,
            ai_provider="gemini",
            user_id=user['id']
        )
        
        await create_event(job_id, BuildEventType.INFO, "File operation completed", progress=90)
        return response_text
        
    except Exception as e:
        return f"File operation error: {str(e)}"


async def process_mcp_task(job_id: str, user: dict, query: str):
    """Process MCP tool task"""
    await create_event(job_id, BuildEventType.MCP_TOOL_CALL, "Calling MCP tool...", progress=30)
    
    # In production, integrate with actual MCP tools
    await asyncio.sleep(0.5)
    
    system_prompt = """You are an AI assistant with access to various tools through MCP (Model Context Protocol).
Help users understand what tools are available and how to use them."""
    
    try:
        full_prompt = f"{system_prompt}\n\nUser request: {query}"
        response_text = await generate_code(
            prompt=full_prompt,
            ai_provider="gemini",
            user_id=user['id']
        )
        
        await create_event(job_id, BuildEventType.MCP_TOOL_RESULT, "MCP tool completed", progress=90)
        return response_text
        
    except Exception as e:
        return f"MCP error: {str(e)}"


async def process_planner_task(job_id: str, user: dict, query: str, project_id: str = None):
    """Process planning task with multiple steps"""
    await create_event(job_id, BuildEventType.PLANNING_STARTED, "Creating plan...", progress=15)
    
    code_blocks = []
    
    # Create plan
    plan_prompt = f"""Create a step-by-step plan for: {query}

Return a JSON plan like:
```json
{{
    "plan": [
        {{"step": 1, "task": "Description", "agent": "coder|browser|file"}},
        {{"step": 2, "task": "Description", "agent": "coder|browser|file"}}
    ]
}}
```"""
    
    try:
        plan_prompt_full = f"You are a planning assistant. Create clear step-by-step plans.\n\n{plan_prompt}"
        plan_response = await generate_code(
            prompt=plan_prompt_full,
            ai_provider="gemini",
            user_id=user['id'],
            is_planner=True
        )
        
        await create_event(
            job_id, 
            BuildEventType.PLANNING_DONE, 
            "Plan created",
            payload={"plan": plan_response[:500] if plan_response else ''},
            progress=25
        )
        
        # Execute the main task
        await create_event(job_id, BuildEventType.CODEGEN_STARTED, "Executing plan...", progress=40)
        
        main_prompt = f"You are an expert programmer and assistant. Complete the user's task.\n\n{query}"
        main_response = await generate_code(
            prompt=main_prompt,
            ai_provider="gemini",
            user_id=user['id']
        )
        
        # Extract code blocks
        import re
        code_pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(code_pattern, main_response or '', re.DOTALL)
        
        for i, (lang, code) in enumerate(matches):
            block = {
                "id": str(uuid.uuid4()),
                "language": lang or "text",
                "code": code.strip(),
                "filename": f"file_{i+1}.{lang or 'txt'}"
            }
            code_blocks.append(block)
        
        await create_event(job_id, BuildEventType.CODEGEN_DONE, "Plan executed", progress=90)
        
        return main_response or '', code_blocks
        
    except Exception as e:
        return f"Planning error: {str(e)}", []


async def process_casual_task(job_id: str, user: dict, query: str):
    """Process casual conversation"""
    await create_event(job_id, BuildEventType.INFO, "Processing...", progress=30)
    
    try:
        full_prompt = f"You are a helpful AI assistant. Be friendly and informative.\n\nUser: {query}"
        response_text = await generate_code(
            prompt=full_prompt,
            ai_provider="gemini",
            user_id=user['id'],
            is_planner=True
        )
        
        await create_event(job_id, BuildEventType.INFO, "Response ready", progress=90)
        return response_text or ''
        
    except Exception as e:
        return f"Error: {str(e)}"


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/agent/chat")
async def agent_chat(
    message: str,
    project_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    user: dict = Depends(require_auth)
):
    """
    Main chat endpoint - Routes to appropriate agent
    Returns job_id for SSE streaming
    """
    now = datetime.now(timezone.utc).isoformat()
    job_id = str(uuid.uuid4())
    
    # Create job
    job = {
        "id": job_id,
        "user_id": user['id'],
        "project_id": project_id,
        "prompt": message,
        "status": BuildJobStatus.QUEUED.value,
        "progress": 0,
        "ai_provider": "auto",
        "code_blocks": [],
        "files_created": [],
        "files_modified": [],
        "has_preview": False,
        "created_at": now,
        "updated_at": now
    }
    
    await db.build_jobs.insert_one(job)
    
    # Create initial chat message
    chat_message = {
        "id": str(uuid.uuid4()),
        "job_id": job_id,
        "user_id": user['id'],
        "role": "user",
        "content": message,
        "timestamp": now
    }
    await db.chat_messages.insert_one(chat_message)
    
    # Start background processing
    background_tasks.add_task(process_job, job_id, user, message, project_id)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Job created, connect to stream for updates",
        "stream_url": f"/api/jobs/{job_id}/stream"
    }


@router.get("/jobs/{job_id}/stream")
async def stream_job_events(
    job_id: str,
    user: dict = Depends(require_auth)
):
    """
    SSE endpoint for streaming job events
    Connect to this endpoint to receive real-time updates
    """
    # Verify job belongs to user
    job = await db.build_jobs.find_one({"id": job_id, "user_id": user['id']})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    async def event_generator() -> AsyncGenerator[str, None]:
        queue = event_manager.get_queue(job_id)
        
        # Send existing events first
        existing_events = await db.build_events.find(
            {"job_id": job_id}
        ).sort("seq", 1).to_list(100)
        
        for event in existing_events:
            event.pop('_id', None)
            yield f"data: {json.dumps(event)}\n\n"
        
        # Stream new events
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                event.pop('_id', None)
                yield f"data: {json.dumps(event)}\n\n"
                
                # Check if job is complete
                if event.get('type') in ['job_completed', 'job_failed', 'error']:
                    yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
                    break
                    
            except asyncio.TimeoutError:
                # Send keepalive
                yield f": keepalive\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, user: dict = Depends(require_auth)):
    """Get job status and details"""
    job = await db.build_jobs.find_one(
        {"id": job_id, "user_id": user['id']},
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get events
    events = await db.build_events.find(
        {"job_id": job_id},
        {"_id": 0}
    ).sort("seq", -1).limit(50).to_list(50)
    
    return {
        **job,
        "events": list(reversed(events))
    }


@router.get("/jobs/{job_id}/events")
async def get_job_events(
    job_id: str,
    limit: int = Query(50, le=200),
    user: dict = Depends(require_auth)
):
    """Get events for a job"""
    job = await db.build_jobs.find_one({"id": job_id, "user_id": user['id']})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    events = await db.build_events.find(
        {"job_id": job_id},
        {"_id": 0}
    ).sort("seq", -1).limit(limit).to_list(limit)
    
    return {"events": list(reversed(events)), "total": len(events)}


@router.post("/jobs/{job_id}/stop")
async def stop_job(job_id: str, user: dict = Depends(require_auth)):
    """Stop a running job"""
    job = await db.build_jobs.find_one({"id": job_id, "user_id": user['id']})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job['status'] not in ['queued', 'running']:
        raise HTTPException(status_code=400, detail="Job is not running")
    
    await db.build_jobs.update_one(
        {"id": job_id},
        {"$set": {
            "status": BuildJobStatus.CANCELLED.value,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await create_event(job_id, BuildEventType.INFO, "Job cancelled by user")
    
    return {"message": "Job stop requested"}


@router.get("/agent/history")
async def get_chat_history(
    limit: int = Query(50, le=200),
    user: dict = Depends(require_auth)
):
    """Get user's chat history"""
    messages = await db.chat_messages.find(
        {"user_id": user['id']},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {"messages": list(reversed(messages))}


@router.get("/agent/jobs")
async def get_user_jobs(
    status: Optional[str] = None,
    limit: int = Query(20, le=100),
    user: dict = Depends(require_auth)
):
    """Get user's jobs"""
    query = {"user_id": user['id']}
    if status:
        query["status"] = status
    
    jobs = await db.build_jobs.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"jobs": jobs}


@router.get("/preview/{job_id}")
async def get_preview(job_id: str, user: dict = Depends(require_auth)):
    """Get preview HTML for a job"""
    job = await db.build_jobs.find_one(
        {"id": job_id, "user_id": user['id']},
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.get('has_preview'):
        raise HTTPException(status_code=404, detail="No preview available")
    
    # Find HTML code block
    html_content = ""
    css_content = ""
    js_content = ""
    
    for block in job.get('code_blocks', []):
        if block.get('language') in ['html', 'htm']:
            html_content = block.get('code', '')
        elif block.get('language') == 'css':
            css_content = block.get('code', '')
        elif block.get('language') in ['javascript', 'js']:
            js_content = block.get('code', '')
    
    # Combine into full HTML
    if not html_content:
        raise HTTPException(status_code=404, detail="No HTML content found")
    
    # Inject CSS and JS if HTML doesn't have them
    if css_content and '<style>' not in html_content:
        html_content = html_content.replace('</head>', f'<style>{css_content}</style></head>')
    if js_content and '<script>' not in html_content:
        html_content = html_content.replace('</body>', f'<script>{js_content}</script></body>')
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)
