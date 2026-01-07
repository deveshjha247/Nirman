"""
Build Routes
Endpoints for creating and monitoring build jobs with SSE streaming.
"""

import uuid
import asyncio
from datetime import datetime, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.db.mongo import db
from app.core.security import require_auth
from app.core.config import JWT_SECRET, JWT_ALGORITHM
from app.models.jobs import (
    BuildJob, BuildJobStatus, CreateBuildRequest, BuildJobResponse
)
from app.services.build_service import (
    run_build_worker, stream_job_events, emit_event, update_job_status
)
from app.models.jobs import BuildEventType

router = APIRouter(prefix="/api", tags=["build"])


# =============================================================================
# Request/Response Models
# =============================================================================

class StartBuildRequest(BaseModel):
    prompt: str
    ai_provider: str = "auto"  # auto, openai, gemini, claude


class JobStatusResponse(BaseModel):
    id: str
    project_id: str
    status: str
    progress: int
    ai_provider: Optional[str] = None
    artifact_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    events: list = []


# =============================================================================
# Routes
# =============================================================================

@router.post("/projects/{project_id}/build", response_model=BuildJobResponse)
async def start_build(
    project_id: str,
    request: StartBuildRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_auth)
):
    """
    Start a new build job for a project.
    
    Creates a job, enqueues it for background processing, and returns the job_id.
    The client can then connect to /api/jobs/{job_id}/stream for SSE updates.
    """
    user_id = current_user["id"]
    
    # Verify project exists and belongs to user
    project = await db.projects.find_one({
        "id": project_id,
        "user_id": user_id
    })
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create job
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    job = BuildJob(
        id=job_id,
        user_id=user_id,
        project_id=project_id,
        prompt=request.prompt,
        status=BuildJobStatus.QUEUED,
        progress=0,
        ai_provider=request.ai_provider,
        created_at=now,
        updated_at=now
    )
    
    # Store in database
    await db.build_jobs.insert_one(job.model_dump())
    
    # Enqueue background worker
    background_tasks.add_task(
        run_build_worker,
        job_id=job_id,
        user_id=user_id,
        project_id=project_id,
        prompt=request.prompt,
        ai_provider=request.ai_provider
    )
    
    now = datetime.now(timezone.utc).isoformat()
    return BuildJobResponse(
        id=job_id,
        status=BuildJobStatus.QUEUED.value,
        progress=0,
        message="Build job queued successfully",
        created_at=now,
        updated_at=now
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(require_auth)
):
    """
    Get the status of a build job along with recent events.
    """
    user_id = current_user["id"]
    
    # Find job
    job = await db.build_jobs.find_one({
        "id": job_id,
        "user_id": user_id
    })
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get recent events
    events = await db.build_events.find(
        {"job_id": job_id}
    ).sort("seq", -1).limit(20).to_list(20)
    
    # Clean up _id fields
    for event in events:
        event.pop('_id', None)
    
    events.reverse()  # Return in chronological order
    
    return JobStatusResponse(
        id=job["id"],
        project_id=job["project_id"],
        status=job["status"],
        progress=job["progress"],
        ai_provider=job.get("ai_provider"),
        artifact_url=job.get("artifact_url"),
        error_message=job.get("error_message"),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        events=events
    )


@router.get("/jobs/{job_id}/stream")
async def stream_job(
    job_id: str,
    token: Optional[str] = Query(None)
):
    """
    SSE endpoint for streaming build job events.
    
    Accepts auth token via query parameter for EventSource compatibility.
    
    Returns a Server-Sent Events stream with JSON events.
    Each event has: id, job_id, seq, type, message, payload, created_at
    
    Event types:
    - job_started: Build has started
    - planning_started/done: Planning phase
    - codegen_started/progress/done: Code generation
    - packaging: Packaging artifacts
    - artifact_ready: Download available
    - error: Build failed
    - job_completed: Build finished successfully
    """
    # Authenticate via query token (EventSource doesn't support headers)
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Verify job belongs to user
    job = await db.build_jobs.find_one({
        "id": job_id,
        "user_id": user_id
    })
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return StreamingResponse(
        stream_job_events(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(require_auth)
):
    """
    Cancel a running build job.
    """
    user_id = current_user["id"]
    
    # Find job
    job = await db.build_jobs.find_one({
        "id": job_id,
        "user_id": user_id
    })
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] not in [BuildJobStatus.QUEUED.value, BuildJobStatus.RUNNING.value]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job with status: {job['status']}"
        )
    
    # Update status
    await update_job_status(job_id, BuildJobStatus.CANCELLED)
    
    # Emit cancel event
    await emit_event(
        job_id=job_id,
        event_type=BuildEventType.ERROR,
        message="Build cancelled by user",
        payload={"cancelled": True}
    )
    
    return {"message": "Job cancelled successfully"}


@router.get("/projects/{project_id}/jobs")
async def list_project_jobs(
    project_id: str,
    limit: int = 10,
    current_user: dict = Depends(require_auth)
):
    """
    List recent build jobs for a project.
    """
    user_id = current_user["id"]
    
    # Verify project belongs to user
    project = await db.projects.find_one({
        "id": project_id,
        "user_id": user_id
    })
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get jobs
    jobs = await db.build_jobs.find({
        "project_id": project_id,
        "user_id": user_id
    }).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Clean up
    for job in jobs:
        job.pop('_id', None)
    
    return {"jobs": jobs}
