"""
Build Service
Handles build job execution, event emission, and SSE streaming.
Includes self-learning integration for personalization.
"""

import asyncio
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, AsyncGenerator
from collections import defaultdict

from app.db.mongo import db
from app.models.jobs import BuildJob, BuildEvent, BuildJobStatus, BuildEventType
from app.models.learning import EventType
from app.services.ai_router import generate_code
from app.services.planner import (
    PLANNER_SYSTEM_PROMPT,
    RENDERER_SYSTEM_PROMPT,
    extract_json_from_response,
    validate_spec,
    create_default_spec,
    generate_build_prompt,
    detect_industry,
    enhance_spec_with_industry,
    build_planner_prompt_with_learning,
    build_renderer_prompt_with_learning,
    apply_preferences_to_spec,
    merge_pattern_into_spec
)
from app.services.learning_service import (
    track_event,
    save_spec_version,
    build_learning_context,
    record_error,
    get_known_fix,
    record_fix_attempt
)

# =============================================================================
# In-Memory PubSub for SSE Streaming
# =============================================================================

class EventPubSub:
    """
    Simple in-memory pub/sub for streaming build events.
    In production, replace with Redis pub/sub for horizontal scaling.
    """
    def __init__(self):
        # job_id -> list of asyncio.Queue subscribers
        self._subscribers: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def subscribe(self, job_id: str) -> asyncio.Queue:
        """Subscribe to events for a job. Returns a Queue to await events."""
        queue = asyncio.Queue()
        async with self._lock:
            self._subscribers[job_id].append(queue)
        return queue
    
    async def unsubscribe(self, job_id: str, queue: asyncio.Queue):
        """Unsubscribe from job events."""
        async with self._lock:
            if job_id in self._subscribers:
                try:
                    self._subscribers[job_id].remove(queue)
                except ValueError:
                    pass
                # Clean up empty subscriber lists
                if not self._subscribers[job_id]:
                    del self._subscribers[job_id]
    
    async def publish(self, job_id: str, event: dict):
        """Publish an event to all subscribers of a job."""
        async with self._lock:
            subscribers = self._subscribers.get(job_id, [])
            for queue in subscribers:
                await queue.put(event)


# Global pubsub instance
pubsub = EventPubSub()


# =============================================================================
# Event Emitter Helper
# =============================================================================

async def emit_event(
    job_id: str,
    event_type: BuildEventType,
    message: str,
    payload: Optional[Dict[str, Any]] = None
) -> BuildEvent:
    """
    Emit a build event:
    1. Store in build_events collection
    2. Push to in-memory pubsub for SSE streaming
    
    Args:
        job_id: The job this event belongs to
        event_type: Type of event (planning_started, codegen_done, etc.)
        message: Human-readable message
        payload: Optional dict with additional data (provider, model, url, code)
    
    Returns:
        The created BuildEvent
    """
    # Get next sequence number for this job
    last_event = await db.build_events.find_one(
        {"job_id": job_id},
        sort=[("seq", -1)]
    )
    seq = (last_event["seq"] + 1) if last_event else 1
    
    # Create event document
    event = BuildEvent(
        id=str(uuid.uuid4()),
        job_id=job_id,
        seq=seq,
        type=event_type,
        message=message,
        payload=payload,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    # Store in database
    await db.build_events.insert_one(event.model_dump())
    
    # Publish to subscribers
    event_dict = event.model_dump()
    await pubsub.publish(job_id, event_dict)
    
    return event


async def update_job_status(
    job_id: str,
    status: BuildJobStatus,
    progress: int = None,
    artifact_url: str = None,
    error_message: str = None
):
    """Update job status in database."""
    update_data = {
        "status": status.value,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if progress is not None:
        update_data["progress"] = progress
    if artifact_url is not None:
        update_data["artifact_url"] = artifact_url
    if error_message is not None:
        update_data["error_message"] = error_message
    
    await db.build_jobs.update_one(
        {"id": job_id},
        {"$set": update_data}
    )


# =============================================================================
# Build Worker Logic
# =============================================================================

async def run_build_worker(job_id: str, user_id: str, project_id: str, prompt: str, ai_provider: str):
    """
    Background worker that executes a build job.
    Emits events at each step for SSE streaming.
    Integrates with self-learning system for personalization.
    
    Steps:
    1. Job started + fetch learning context
    2. Planning (analyze prompt, create JSON spec using Planner Agent)
    3. Apply personalization from learning context
    4. Code generation (use Renderer Agent with spec)
    5. Packaging
    6. Artifact ready
    7. Track events for learning
    """
    learning_context = None
    spec = None
    industry = "general"
    
    try:
        # Update status to running
        await update_job_status(job_id, BuildJobStatus.RUNNING, progress=0)
        
        # Step 1: Job started
        await emit_event(
            job_id=job_id,
            event_type=BuildEventType.JOB_STARTED,
            message="🚀 Build job started",
            payload={"prompt": prompt}
        )
        
        # Track build started event for learning
        await track_event(
            user_id=user_id,
            project_id=project_id,
            event_type=EventType.BUILD_STARTED,
            payload={"prompt": prompt, "job_id": job_id}
        )
        
        await asyncio.sleep(0.3)
        
        # Step 2: Planning with Planner Agent
        await emit_event(
            job_id=job_id,
            event_type=BuildEventType.PLANNING_STARTED,
            message="🧠 Planner Agent analyzing your request..."
        )
        await update_job_status(job_id, BuildJobStatus.RUNNING, progress=10)
        
        # Choose AI provider
        selected_provider = choose_ai_provider(prompt) if ai_provider == "auto" else ai_provider
        selected_model = get_model_for_provider(selected_provider)
        
        # Detect industry from prompt
        industry = detect_industry(prompt)
        
        await emit_event(
            job_id=job_id,
            event_type=BuildEventType.CODEGEN_PROGRESS,
            message=f"📋 Detected industry: {industry.replace('_', ' ').title()}",
            payload={"industry": industry}
        )
        
        # Fetch learning context for personalization
        try:
            learning_context = await build_learning_context(
                user_id=user_id,
                industry=industry,
                sections=["hero", "features", "pricing", "testimonials", "cta", "footer"]
            )
            
            if learning_context.get("personalization_enabled"):
                await emit_event(
                    job_id=job_id,
                    event_type=BuildEventType.CODEGEN_PROGRESS,
                    message="✨ Applying your personalized preferences...",
                    payload={"personalization": True}
                )
        except Exception:
            learning_context = None
        
        # Build planner prompt with learning context
        if learning_context:
            planner_prompt = build_planner_prompt_with_learning(prompt, learning_context)
        else:
            planner_prompt = f"{PLANNER_SYSTEM_PROMPT}\n\nUser request: {prompt}"
        
        # Call AI to generate spec using Planner prompt
        spec = None
        try:
            planner_response = await generate_code(
                prompt=planner_prompt,
                ai_provider=selected_provider,
                user_id=user_id,
                project_id=project_id,
                job_id=job_id,
                is_planner=True
            )
            
            # Extract JSON from response
            spec = extract_json_from_response(planner_response)
            
            if spec:
                # Validate spec
                is_valid, errors = validate_spec(spec)
                if not is_valid:
                    await emit_event(
                        job_id=job_id,
                        event_type=BuildEventType.CODEGEN_PROGRESS,
                        message=f"⚠️ Spec validation warnings: {', '.join(errors[:2])}",
                        payload={"warnings": errors}
                    )
                
                # Enhance with industry templates
                spec = enhance_spec_with_industry(spec, industry)
                
                # Apply user preferences from learning context
                if learning_context and learning_context.get("user_preferences"):
                    spec = apply_preferences_to_spec(spec, learning_context["user_preferences"])
                
                # Merge winning patterns if available
                if learning_context and learning_context.get("pattern_snippets"):
                    spec = merge_pattern_into_spec(spec, learning_context["pattern_snippets"])
                
                # Save spec version for learning
                await save_spec_version(
                    project_id=project_id,
                    user_id=user_id,
                    spec_json=spec,
                    source="planner"
                )
                
                # Track plan generated event
                await track_event(
                    user_id=user_id,
                    project_id=project_id,
                    event_type=EventType.PLAN_GENERATED,
                    payload={
                        "industry": industry,
                        "tone": spec.get("theme", {}).get("tone"),
                        "sections": spec.get("website", {}).get("pages", [{}])[0].get("sections", [])
                    }
                )
            else:
                spec = create_default_spec(prompt)
                spec = enhance_spec_with_industry(spec, industry)
                
        except Exception:
            # Fallback to default spec
            spec = create_default_spec(prompt)
            spec = enhance_spec_with_industry(spec, industry)
        
        await update_job_status(job_id, BuildJobStatus.RUNNING, progress=25)
        
        # Planning done - emit spec summary
        project_name = spec.get("project", {}).get("name", "Project")
        project_type = spec.get("project", {}).get("type", "website")
        theme = spec.get("theme", {})
        
        await emit_event(
            job_id=job_id,
            event_type=BuildEventType.PLANNING_DONE,
            message=f"✅ Plan ready: {project_name} ({project_type})",
            payload={
                "provider": selected_provider,
                "model": selected_model,
                "spec": spec,
                "theme": theme
            }
        )
        await update_job_status(job_id, BuildJobStatus.RUNNING, progress=30)
        
        # Step 3: Code Generation with Renderer Agent
        await emit_event(
            job_id=job_id,
            event_type=BuildEventType.CODEGEN_STARTED,
            message=f"⚡ Builder Agent generating code with {selected_provider.upper()}..."
        )
        
        # Generate build prompt from spec with learning context
        if learning_context:
            build_prompt = build_renderer_prompt_with_learning(spec, learning_context)
        else:
            build_prompt = f"{RENDERER_SYSTEM_PROMPT}\n\n{generate_build_prompt(spec)}"
        
        # Actually generate code using AI with Renderer prompt
        try:
            generated_code = await generate_code(
                prompt=build_prompt,
                ai_provider=selected_provider,
                user_id=user_id,
                project_id=project_id,
                job_id=job_id
            )
            
            # Progress update during generation
            await emit_event(
                job_id=job_id,
                event_type=BuildEventType.CODEGEN_PROGRESS,
                message="💻 Code generation in progress...",
                payload={"progress": 60}
            )
            await update_job_status(job_id, BuildJobStatus.RUNNING, progress=60)
            
        except Exception as e:
            # Record error for auto-fix learning
            await record_error(
                error_text=str(e),
                error_category="codegen",
                context={"spec": spec, "provider": selected_provider}
            )
            
            # Check if we have a known fix
            known_fix = await get_known_fix(str(e))
            if known_fix and known_fix.fix_instructions:
                await emit_event(
                    job_id=job_id,
                    event_type=BuildEventType.CODEGEN_PROGRESS,
                    message=f"🔧 Applying known fix: {known_fix.fix_instructions[:50]}...",
                    payload={"auto_fix": True}
                )
            
            # If AI generation fails, use a fallback template
            generated_code = generate_fallback_template_from_spec(spec)
            await emit_event(
                job_id=job_id,
                event_type=BuildEventType.CODEGEN_PROGRESS,
                message="🔧 Using template generation (AI unavailable)",
                payload={"fallback": True}
            )
        
        await asyncio.sleep(0.3)
        
        # Code generation done
        lines_count = len(generated_code.split('\n'))
        await emit_event(
            job_id=job_id,
            event_type=BuildEventType.CODEGEN_DONE,
            message=f"✨ Code generation complete! ({lines_count} lines)",
            payload={
                "lines_of_code": lines_count,
                "preview": generated_code[:500] + "..." if len(generated_code) > 500 else generated_code
            }
        )
        await update_job_status(job_id, BuildJobStatus.RUNNING, progress=80)
        
        # Step 4: Packaging
        await emit_event(
            job_id=job_id,
            event_type=BuildEventType.PACKAGING,
            message="📦 Packaging your application..."
        )
        await asyncio.sleep(0.5)
        
        # Save generated code and spec to project
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {
                "html_code": generated_code,
                "build_spec": spec,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        await update_job_status(job_id, BuildJobStatus.RUNNING, progress=90)
        
        # Step 5: Artifact ready
        artifact_url = f"/api/projects/{project_id}/download"
        await emit_event(
            job_id=job_id,
            event_type=BuildEventType.ARTIFACT_READY,
            message="Your app is ready to download!",
            payload={
                "download_url": artifact_url,
                "project_id": project_id
            }
        )
        
        # Job completed successfully
        await update_job_status(
            job_id, 
            BuildJobStatus.SUCCESS, 
            progress=100,
            artifact_url=artifact_url
        )
        
        await emit_event(
            job_id=job_id,
            event_type=BuildEventType.JOB_COMPLETED,
            message="Build completed successfully! 🎉",
            payload={"status": "success"}
        )
        
    except Exception as e:
        # Handle errors
        error_msg = str(e)
        await emit_event(
            job_id=job_id,
            event_type=BuildEventType.ERROR,
            message=f"Build failed: {error_msg}",
            payload={"error": error_msg}
        )
        await update_job_status(
            job_id,
            BuildJobStatus.FAILED,
            error_message=error_msg
        )


# =============================================================================
# Helper Functions
# =============================================================================

def choose_ai_provider(prompt: str) -> str:
    """Choose the best AI provider based on the prompt content."""
    prompt_lower = prompt.lower()
    
    # Claude is great for design/UI tasks
    if any(word in prompt_lower for word in ['design', 'beautiful', 'ui', 'ux', 'style', 'modern']):
        return "claude"
    
    # GPT-4 for complex logic
    if any(word in prompt_lower for word in ['complex', 'algorithm', 'logic', 'function', 'api']):
        return "openai"
    
    # Gemini for speed/simple tasks
    if any(word in prompt_lower for word in ['simple', 'quick', 'fast', 'basic']):
        return "gemini"
    
    # Default to OpenAI
    return "openai"


def get_model_for_provider(provider: str) -> str:
    """Get the model name for a provider."""
    models = {
        "openai": "gpt-4o",
        "gemini": "gemini-2.0-flash",
        "claude": "claude-sonnet-4-20250514"
    }
    return models.get(provider, "gpt-4o")


def extract_features(prompt: str) -> list:
    """Extract features from the prompt for the build spec."""
    features = []
    prompt_lower = prompt.lower()
    
    feature_keywords = {
        "form": "contact_form",
        "login": "authentication",
        "signup": "authentication",
        "dark mode": "dark_mode",
        "responsive": "responsive",
        "animation": "animations",
        "chart": "charts",
        "dashboard": "dashboard",
        "gallery": "image_gallery",
        "pricing": "pricing_table",
        "testimonial": "testimonials",
    }
    
    for keyword, feature in feature_keywords.items():
        if keyword in prompt_lower:
            features.append(feature)
    
    return features if features else ["basic_layout"]


def generate_fallback_template(prompt: str) -> str:
    """Generate a fallback HTML template if AI fails."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated App</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 py-6">
            <h1 class="text-2xl font-bold text-gray-900">Your App</h1>
        </div>
    </header>
    <main class="max-w-7xl mx-auto px-4 py-8">
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">Welcome!</h2>
            <p class="text-gray-600">This is a placeholder. Your prompt was: {prompt[:100]}...</p>
        </div>
    </main>
</body>
</html>'''


def generate_fallback_template_from_spec(spec: dict) -> str:
    """Generate a fallback HTML template from spec if AI fails."""
    project = spec.get("project", {})
    theme = spec.get("theme", {})
    name = project.get("name", "My App")
    primary = theme.get("primary", "#6366f1")
    secondary = theme.get("secondary", "#8b5cf6")
    font = theme.get("font", "Inter")
    
    # Get sections if website
    sections = []
    if "website" in spec:
        pages = spec["website"].get("pages", [])
        if pages:
            sections = pages[0].get("sections", [])
    
    # Build sections HTML
    sections_html = ""
    
    if "hero" in sections or "hero_search" in sections:
        sections_html += f'''
    <section class="py-20 bg-gradient-to-r from-[{primary}] to-[{secondary}]">
        <div class="max-w-7xl mx-auto px-4 text-center text-white">
            <h1 class="text-5xl font-bold mb-6">{name}</h1>
            <p class="text-xl mb-8 opacity-90">Welcome to our amazing platform</p>
            <button class="px-8 py-3 bg-white text-gray-900 rounded-lg font-semibold hover:bg-gray-100 transition">
                Get Started
            </button>
        </div>
    </section>'''
    
    if "features" in sections:
        sections_html += '''
    <section class="py-16 bg-white">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-3xl font-bold text-center mb-12">Features</h2>
            <div class="grid md:grid-cols-3 gap-8">
                <div class="p-6 bg-gray-50 rounded-xl">
                    <div class="w-12 h-12 bg-indigo-100 rounded-lg mb-4"></div>
                    <h3 class="text-xl font-semibold mb-2">Feature One</h3>
                    <p class="text-gray-600">Description of the first amazing feature.</p>
                </div>
                <div class="p-6 bg-gray-50 rounded-xl">
                    <div class="w-12 h-12 bg-indigo-100 rounded-lg mb-4"></div>
                    <h3 class="text-xl font-semibold mb-2">Feature Two</h3>
                    <p class="text-gray-600">Description of the second amazing feature.</p>
                </div>
                <div class="p-6 bg-gray-50 rounded-xl">
                    <div class="w-12 h-12 bg-indigo-100 rounded-lg mb-4"></div>
                    <h3 class="text-xl font-semibold mb-2">Feature Three</h3>
                    <p class="text-gray-600">Description of the third amazing feature.</p>
                </div>
            </div>
        </div>
    </section>'''
    
    if "pricing" in sections:
        sections_html += f'''
    <section class="py-16 bg-gray-50">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-3xl font-bold text-center mb-12">Pricing</h2>
            <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                <div class="p-8 bg-white rounded-2xl shadow-sm border">
                    <h3 class="text-xl font-semibold mb-2">Basic</h3>
                    <p class="text-4xl font-bold mb-4">$9<span class="text-lg text-gray-500">/mo</span></p>
                    <ul class="space-y-3 mb-8">
                        <li class="text-gray-600">✓ Feature 1</li>
                        <li class="text-gray-600">✓ Feature 2</li>
                    </ul>
                    <button class="w-full py-3 border-2 border-[{primary}] text-[{primary}] rounded-lg font-semibold hover:bg-gray-50">
                        Get Started
                    </button>
                </div>
                <div class="p-8 bg-[{primary}] text-white rounded-2xl shadow-lg scale-105">
                    <h3 class="text-xl font-semibold mb-2">Pro</h3>
                    <p class="text-4xl font-bold mb-4">$29<span class="text-lg opacity-75">/mo</span></p>
                    <ul class="space-y-3 mb-8">
                        <li>✓ Everything in Basic</li>
                        <li>✓ Feature 3</li>
                        <li>✓ Feature 4</li>
                    </ul>
                    <button class="w-full py-3 bg-white text-gray-900 rounded-lg font-semibold hover:bg-gray-100">
                        Get Started
                    </button>
                </div>
                <div class="p-8 bg-white rounded-2xl shadow-sm border">
                    <h3 class="text-xl font-semibold mb-2">Enterprise</h3>
                    <p class="text-4xl font-bold mb-4">$99<span class="text-lg text-gray-500">/mo</span></p>
                    <ul class="space-y-3 mb-8">
                        <li class="text-gray-600">✓ Everything in Pro</li>
                        <li class="text-gray-600">✓ Priority Support</li>
                    </ul>
                    <button class="w-full py-3 border-2 border-[{primary}] text-[{primary}] rounded-lg font-semibold hover:bg-gray-50">
                        Contact Sales
                    </button>
                </div>
            </div>
        </div>
    </section>'''
    
    if "testimonials" in sections:
        sections_html += '''
    <section class="py-16 bg-white">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-3xl font-bold text-center mb-12">What Our Customers Say</h2>
            <div class="grid md:grid-cols-3 gap-8">
                <div class="p-6 bg-gray-50 rounded-xl">
                    <p class="text-gray-600 mb-4">"Amazing product! It has transformed how we work."</p>
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-gray-300 rounded-full"></div>
                        <div>
                            <p class="font-semibold">John Doe</p>
                            <p class="text-sm text-gray-500">CEO, Company</p>
                        </div>
                    </div>
                </div>
                <div class="p-6 bg-gray-50 rounded-xl">
                    <p class="text-gray-600 mb-4">"Best decision we made this year!"</p>
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-gray-300 rounded-full"></div>
                        <div>
                            <p class="font-semibold">Jane Smith</p>
                            <p class="text-sm text-gray-500">CTO, Startup</p>
                        </div>
                    </div>
                </div>
                <div class="p-6 bg-gray-50 rounded-xl">
                    <p class="text-gray-600 mb-4">"Incredible support and features."</p>
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-gray-300 rounded-full"></div>
                        <div>
                            <p class="font-semibold">Mike Johnson</p>
                            <p class="text-sm text-gray-500">Founder</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>'''
    
    if "cta" in sections:
        sections_html += f'''
    <section class="py-16 bg-[{primary}]">
        <div class="max-w-4xl mx-auto px-4 text-center text-white">
            <h2 class="text-3xl font-bold mb-4">Ready to Get Started?</h2>
            <p class="text-xl mb-8 opacity-90">Join thousands of happy customers today.</p>
            <button class="px-8 py-3 bg-white text-gray-900 rounded-lg font-semibold hover:bg-gray-100 transition">
                Start Free Trial
            </button>
        </div>
    </section>'''
    
    # Default sections if none specified
    if not sections_html:
        sections_html = f'''
    <section class="py-20 bg-gradient-to-r from-[{primary}] to-[{secondary}]">
        <div class="max-w-7xl mx-auto px-4 text-center text-white">
            <h1 class="text-5xl font-bold mb-6">{name}</h1>
            <p class="text-xl mb-8 opacity-90">Welcome to our platform</p>
            <button class="px-8 py-3 bg-white text-gray-900 rounded-lg font-semibold hover:bg-gray-100 transition">
                Get Started
            </button>
        </div>
    </section>
    <section class="py-16 bg-white">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <h2 class="text-3xl font-bold mb-8">Welcome</h2>
            <p class="text-gray-600 max-w-2xl mx-auto">This is a generated template. Start customizing!</p>
        </div>
    </section>'''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family={font.replace(" ", "+")}:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: '{font}', sans-serif; }}
    </style>
</head>
<body class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <a href="#" class="text-xl font-bold text-gray-900">{name}</a>
            <div class="hidden md:flex items-center gap-6">
                <a href="#" class="text-gray-600 hover:text-gray-900">Home</a>
                <a href="#" class="text-gray-600 hover:text-gray-900">Features</a>
                <a href="#" class="text-gray-600 hover:text-gray-900">Pricing</a>
                <a href="#" class="text-gray-600 hover:text-gray-900">Contact</a>
                <button class="px-4 py-2 bg-[{primary}] text-white rounded-lg hover:opacity-90 transition">
                    Get Started
                </button>
            </div>
        </div>
    </nav>
    
    {sections_html}
    
    <footer class="bg-gray-900 text-white py-12">
        <div class="max-w-7xl mx-auto px-4">
            <div class="grid md:grid-cols-4 gap-8">
                <div>
                    <h3 class="text-xl font-bold mb-4">{name}</h3>
                    <p class="text-gray-400">Building amazing products.</p>
                </div>
                <div>
                    <h4 class="font-semibold mb-4">Product</h4>
                    <ul class="space-y-2 text-gray-400">
                        <li><a href="#" class="hover:text-white">Features</a></li>
                        <li><a href="#" class="hover:text-white">Pricing</a></li>
                    </ul>
                </div>
                <div>
                    <h4 class="font-semibold mb-4">Company</h4>
                    <ul class="space-y-2 text-gray-400">
                        <li><a href="#" class="hover:text-white">About</a></li>
                        <li><a href="#" class="hover:text-white">Contact</a></li>
                    </ul>
                </div>
                <div>
                    <h4 class="font-semibold mb-4">Legal</h4>
                    <ul class="space-y-2 text-gray-400">
                        <li><a href="#" class="hover:text-white">Privacy</a></li>
                        <li><a href="#" class="hover:text-white">Terms</a></li>
                    </ul>
                </div>
            </div>
            <div class="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
                <p>&copy; 2026 {name}. All rights reserved.</p>
            </div>
        </div>
    </footer>
</body>
</html>'''


# =============================================================================
# SSE Stream Generator
# =============================================================================

async def stream_job_events(job_id: str) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE events for a build job.
    Used by the /api/jobs/{job_id}/stream endpoint.
    """
    # First, send any existing events
    existing_events = await db.build_events.find(
        {"job_id": job_id}
    ).sort("seq", 1).to_list(100)
    
    for event in existing_events:
        # Remove MongoDB _id for JSON serialization
        event.pop('_id', None)
        yield f"data: {json.dumps(event)}\n\n"
    
    # Check if job is already completed
    job = await db.build_jobs.find_one({"id": job_id})
    if job and job["status"] in [BuildJobStatus.SUCCESS.value, BuildJobStatus.FAILED.value, BuildJobStatus.CANCELLED.value]:
        # Send end event and close
        yield f"data: {json.dumps({'type': 'stream_end', 'status': job['status']})}\n\n"
        return
    
    # Subscribe to new events
    queue = await pubsub.subscribe(job_id)
    
    try:
        while True:
            try:
                # Wait for new event with timeout
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                event.pop('_id', None)
                yield f"data: {json.dumps(event)}\n\n"
                
                # Check if this is a terminal event
                if event.get('type') in [BuildEventType.JOB_COMPLETED.value, BuildEventType.ERROR.value]:
                    yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
                    break
                    
            except asyncio.TimeoutError:
                # Send keepalive ping
                yield ": keepalive\n\n"
                
    finally:
        await pubsub.unsubscribe(job_id, queue)
