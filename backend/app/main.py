from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

# Import routers
from app.routes import auth, projects, plans, wallet, admin, support, ai_keys, build
from app.routes import learning
from app.routes import integrations
from app.routes import integrations_extended
from app.routes import coding_agent
from app.routes import agent
from app.routes import agent_chat
from app.routes import llm_keys

# Import config
from app.core.config import APP_VERSION, APP_NAME

# Import aggregator for background jobs
from app.services.aggregator_jobs import start_aggregator_scheduler, stop_aggregator_scheduler


# Lifespan for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background learning jobs
    print(f"🚀 Starting {APP_NAME} API v{APP_VERSION} with Self-Learning System...")
    await start_aggregator_scheduler()
    yield
    # Shutdown: Stop background jobs
    print(f"🛑 Shutting down {APP_NAME} API...")
    await stop_aggregator_scheduler()


# Create app
app = FastAPI(
    title=f"{APP_NAME} - AI Web App Creator",
    description="Build websites with AI - Now with Self-Learning!",
    version=APP_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(plans.router, prefix="/api")
app.include_router(wallet.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(support.router, prefix="/api")
app.include_router(ai_keys.router, prefix="/api")
# Build routes have their own /api prefix
app.include_router(build.router)
# Learning routes (Self-Learning System)
app.include_router(learning.router)
# Integrations (GitHub, Vercel, etc.)
app.include_router(integrations.router, prefix="/api")
# Extended Integrations (Vercel, Supabase, Firebase, Canva, MongoDB, Razorpay, Cashfree)
app.include_router(integrations_extended.router, prefix="/api")
# Coding Agent (Multi-agent system)
app.include_router(coding_agent.router)
# Agent Chat with SSE streaming
app.include_router(agent_chat.router, prefix="/api")
# LLM Keys (Universal Key System)
app.include_router(llm_keys.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Nirman API", 
        "version": "2.0", 
        "status": "running",
        "features": ["ai-builder", "self-learning", "personalization", "github-integration"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "learning_enabled": True}
