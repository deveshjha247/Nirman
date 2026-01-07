"""
AI Router Service - Direct API Integration
Nirman AI Builder - Direct API calls to AI providers (No third-party wrappers)
Supports: OpenAI, Gemini, Claude, Grok, DeepSeek
"""

import traceback
import time
import uuid
import json
import httpx
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load env variables
load_dotenv()

from app.core.config import (
    OPENAI_API_KEY, 
    GEMINI_API_KEY, 
    CLAUDE_API_KEY, 
    GROK_API_KEY,
    DEEPSEEK_API_KEY,
    MISTRAL_API_KEY,
    COHERE_API_KEY,
    GROQ_API_KEY,
    TOGETHER_API_KEY,
    PERPLEXITY_API_KEY,
    FIREWORKS_API_KEY,
    AI21_API_KEY,
    QWEN_API_KEY,
    MOONSHOT_API_KEY,
    YI_API_KEY,
    ZHIPU_API_KEY,
    HUGGINGFACE_API_KEY,
    DEFAULT_AI_PROVIDER
)
from app.db.mongo import db

# Encryption key for BYO API keys (in production, use env var)
ENCRYPTION_KEY = Fernet.generate_key()
cipher = Fernet(ENCRYPTION_KEY)

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are an expert full-stack web developer and AI assistant. Generate clean, modern, responsive HTML/CSS/JavaScript code.

Core Rules:
1. Always use Tailwind CSS for styling (include CDN link)
2. Create beautiful, modern UI with smooth animations and transitions
3. Make everything fully responsive and mobile-friendly
4. Include all necessary CSS and JS inline in a single HTML file
5. Return ONLY the complete code wrapped in ```html blocks, no explanations
6. Use semantic HTML5 elements
7. Add hover effects, shadows, and micro-interactions for polish
8. Use modern color schemes and gradients
9. Include proper form validation and error handling
10. Add loading states and feedback for user actions

When asked to plan/analyze, return a JSON array of steps.
When asked to build, return complete working HTML code.

Design Philosophy:
- Clean, minimalist layouts with ample whitespace
- Professional typography with good hierarchy
- Subtle shadows and rounded corners
- Smooth hover transitions (200-300ms)
- Consistent spacing (use Tailwind's spacing scale)
- Dark mode support when appropriate"""

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

MODEL_CONFIG = {
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "default_model": "gpt-5.2",
        "models": {
            "gpt-5.2": {"input": 0.002, "output": 0.008},
            "gpt-5": {"input": 0.003, "output": 0.012},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "o1": {"input": 0.015, "output": 0.06},
            "o1-mini": {"input": 0.003, "output": 0.012},
        }
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "default_model": "gemini-2.0-flash",
        "models": {
            "gemini-2.5-flash": {"input": 0.0001, "output": 0.0004},
            "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-2.0-flash": {"input": 0.000075, "output": 0.0003},
            "gemini-2.0-flash-exp": {"input": 0.0001, "output": 0.0004},
        }
    },
    "claude": {
        "url": "https://api.anthropic.com/v1/messages",
        "default_model": "claude-sonnet-4-20250514",
        "models": {
            "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        }
    },
    "grok": {
        "url": "https://api.x.ai/v1/chat/completions",
        "default_model": "grok-2-latest",
        "models": {
            "grok-2-latest": {"input": 0.002, "output": 0.01},
            "grok-beta": {"input": 0.002, "output": 0.01},
        }
    },
    "deepseek": {
        "url": "https://api.deepseek.com/chat/completions",
        "default_model": "deepseek-chat",
        "models": {
            "deepseek-chat": {"input": 0.00014, "output": 0.00028},
            "deepseek-coder": {"input": 0.00014, "output": 0.00028},
            "deepseek-reasoner": {"input": 0.00055, "output": 0.00219},
        }
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/chat/completions",
        "default_model": "mistral-large-latest",
        "models": {
            "mistral-large-latest": {"input": 0.002, "output": 0.006},
            "mistral-medium-latest": {"input": 0.0027, "output": 0.0081},
            "mistral-small-latest": {"input": 0.001, "output": 0.003},
            "codestral-latest": {"input": 0.001, "output": 0.003},
            "pixtral-large-latest": {"input": 0.002, "output": 0.006},
            "ministral-8b-latest": {"input": 0.0001, "output": 0.0001},
        }
    },
    "cohere": {
        "url": "https://api.cohere.ai/v1/chat",
        "default_model": "command-r-plus",
        "models": {
            "command-r-plus": {"input": 0.003, "output": 0.015},
            "command-r": {"input": 0.0005, "output": 0.0015},
            "command": {"input": 0.001, "output": 0.002},
            "command-light": {"input": 0.0003, "output": 0.0006},
        }
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "default_model": "llama-3.3-70b-versatile",
        "models": {
            "llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
            "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008},
            "mixtral-8x7b-32768": {"input": 0.00024, "output": 0.00024},
            "gemma2-9b-it": {"input": 0.0002, "output": 0.0002},
        }
    },
    "together": {
        "url": "https://api.together.xyz/v1/chat/completions",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "models": {
            "meta-llama/Llama-3.3-70B-Instruct-Turbo": {"input": 0.00088, "output": 0.00088},
            "meta-llama/Llama-3.1-405B-Instruct-Turbo": {"input": 0.005, "output": 0.005},
            "Qwen/Qwen2.5-72B-Instruct-Turbo": {"input": 0.0012, "output": 0.0012},
            "mistralai/Mixtral-8x22B-Instruct-v0.1": {"input": 0.0012, "output": 0.0012},
            "deepseek-ai/DeepSeek-R1": {"input": 0.003, "output": 0.007},
        }
    },
    "perplexity": {
        "url": "https://api.perplexity.ai/chat/completions",
        "default_model": "llama-3.1-sonar-large-128k-online",
        "models": {
            "llama-3.1-sonar-large-128k-online": {"input": 0.001, "output": 0.001},
            "llama-3.1-sonar-small-128k-online": {"input": 0.0002, "output": 0.0002},
            "llama-3.1-sonar-huge-128k-online": {"input": 0.005, "output": 0.005},
        }
    },
    "fireworks": {
        "url": "https://api.fireworks.ai/inference/v1/chat/completions",
        "default_model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "models": {
            "accounts/fireworks/models/llama-v3p3-70b-instruct": {"input": 0.0009, "output": 0.0009},
            "accounts/fireworks/models/llama-v3p1-405b-instruct": {"input": 0.003, "output": 0.003},
            "accounts/fireworks/models/qwen2p5-72b-instruct": {"input": 0.0009, "output": 0.0009},
            "accounts/fireworks/models/deepseek-r1": {"input": 0.003, "output": 0.008},
        }
    },
    "ai21": {
        "url": "https://api.ai21.com/studio/v1/chat/completions",
        "default_model": "jamba-1.5-large",
        "models": {
            "jamba-1.5-large": {"input": 0.002, "output": 0.008},
            "jamba-1.5-mini": {"input": 0.0002, "output": 0.0004},
        }
    },
    "qwen": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "default_model": "qwen-max",
        "models": {
            "qwen-max": {"input": 0.0016, "output": 0.0064},
            "qwen-plus": {"input": 0.0004, "output": 0.0012},
            "qwen-turbo": {"input": 0.00008, "output": 0.0002},
            "qwen-coder-plus": {"input": 0.0004, "output": 0.0012},
        }
    },
    "moonshot": {
        "url": "https://api.moonshot.cn/v1/chat/completions",
        "default_model": "moonshot-v1-128k",
        "models": {
            "moonshot-v1-128k": {"input": 0.0008, "output": 0.0008},
            "moonshot-v1-32k": {"input": 0.0004, "output": 0.0004},
            "moonshot-v1-8k": {"input": 0.0002, "output": 0.0002},
        }
    },
    "yi": {
        "url": "https://api.lingyiwanwu.com/v1/chat/completions",
        "default_model": "yi-lightning",
        "models": {
            "yi-lightning": {"input": 0.00017, "output": 0.00017},
            "yi-large": {"input": 0.003, "output": 0.003},
            "yi-medium": {"input": 0.0003, "output": 0.0003},
            "yi-large-turbo": {"input": 0.0006, "output": 0.0006},
        }
    },
    "zhipu": {
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "default_model": "glm-4-plus",
        "models": {
            "glm-4-plus": {"input": 0.007, "output": 0.007},
            "glm-4-air": {"input": 0.0001, "output": 0.0001},
            "glm-4-flash": {"input": 0.00001, "output": 0.00001},
            "glm-4-long": {"input": 0.0001, "output": 0.0001},
        }
    },
    "huggingface": {
        "url": "https://api-inference.huggingface.co/models/{model}/v1/chat/completions",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "models": {
            "meta-llama/Llama-3.3-70B-Instruct": {"input": 0.0007, "output": 0.0007},
            "meta-llama/Llama-3.1-8B-Instruct": {"input": 0.0001, "output": 0.0001},
            "Qwen/Qwen2.5-72B-Instruct": {"input": 0.0007, "output": 0.0007},
            "Qwen/Qwen2.5-Coder-32B-Instruct": {"input": 0.0005, "output": 0.0005},
            "mistralai/Mixtral-8x7B-Instruct-v0.1": {"input": 0.0005, "output": 0.0005},
            "microsoft/Phi-3-mini-4k-instruct": {"input": 0.0001, "output": 0.0001},
            "google/gemma-2-27b-it": {"input": 0.0003, "output": 0.0003},
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": {"input": 0.0005, "output": 0.0005},
        }
    }
}

# Model pricing (approx per 1K tokens)
MODEL_PRICING = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gemini-2.0-flash-exp": {"input": 0.0001, "output": 0.0004},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "grok-2-latest": {"input": 0.002, "output": 0.01},
    "deepseek-chat": {"input": 0.00014, "output": 0.00028},
    "deepseek-coder": {"input": 0.00014, "output": 0.00028},
    "deepseek-reasoner": {"input": 0.00055, "output": 0.00219},
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for storage"""
    return cipher.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key for use"""
    return cipher.decrypt(encrypted_key.encode()).decode()

def get_key_hint(api_key: str) -> str:
    """Get last 4 chars of API key for display"""
    if not api_key or len(api_key) < 4:
        return "****"
    return f"...{api_key[-4:]}"

def get_platform_key(provider: str) -> str:
    """Get platform API key for a provider"""
    # Direct provider keys
    keys = {
        "openai": OPENAI_API_KEY,
        "gemini": GEMINI_API_KEY,
        "claude": CLAUDE_API_KEY,
        "grok": GROK_API_KEY,
        "deepseek": DEEPSEEK_API_KEY,
        "mistral": MISTRAL_API_KEY,
        "cohere": COHERE_API_KEY,
        "groq": GROQ_API_KEY,
        "together": TOGETHER_API_KEY,
        "perplexity": PERPLEXITY_API_KEY,
        "fireworks": FIREWORKS_API_KEY,
        "ai21": AI21_API_KEY,
        "qwen": QWEN_API_KEY,
        "moonshot": MOONSHOT_API_KEY,
        "yi": YI_API_KEY,
        "zhipu": ZHIPU_API_KEY,
        "huggingface": HUGGINGFACE_API_KEY,
    }
    return keys.get(provider, "")

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

async def log_ai_run(
    user_id: str,
    provider: str,
    model: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    latency_ms: int = 0,
    status: str = "success",
    error_message: str = None,
    project_id: str = None,
    job_id: str = None,
    is_byo_key: bool = False
):
    """Log AI run to database"""
    pricing = MODEL_PRICING.get(model, {"input": 0.001, "output": 0.002})
    cost = (tokens_in / 1000 * pricing["input"]) + (tokens_out / 1000 * pricing["output"])
    
    ai_run = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "project_id": project_id,
        "job_id": job_id,
        "provider": provider,
        "model": model,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "latency_ms": latency_ms,
        "status": status,
        "error_message": error_message,
        "cost_estimate": round(cost, 6),
        "is_byo_key": is_byo_key,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.ai_runs.insert_one(ai_run)
    return ai_run

async def log_error(error_type: str, error_message: str, endpoint: str, user_id: str = None, stack_trace: str = None):
    """Log error to database"""
    error_doc = {
        "id": str(uuid.uuid4()),
        "error_type": error_type,
        "error_message": error_message,
        "endpoint": endpoint,
        "user_id": user_id,
        "stack_trace": stack_trace,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.error_logs.insert_one(error_doc)

# =============================================================================
# USER KEY MANAGEMENT
# =============================================================================

async def get_user_ai_key(user_id: str, provider: str) -> Optional[str]:
    """Get user's BYO API key for a provider"""
    key_doc = await db.user_ai_keys.find_one({
        "user_id": user_id,
        "provider": provider,
        "is_active": True
    })
    if key_doc:
        return decrypt_api_key(key_doc["encrypted_key"])
    return None

async def check_provider_health(provider: str) -> dict:
    """Check if AI provider is healthy"""
    config = await db.ai_provider_configs.find_one({"provider": provider})
    if config:
        return {
            "is_enabled": config.get("is_enabled", True),
            "is_blocked": config.get("is_blocked", False),
            "health_status": config.get("health_status", "healthy")
        }
    return {"is_enabled": True, "is_blocked": False, "health_status": "healthy"}

# =============================================================================
# DIRECT API CALLS - NO WRAPPERS
# =============================================================================

async def call_openai(
    prompt: str, 
    system_prompt: str, 
    api_key: str, 
    model: str = "gpt-5.2"
) -> Dict[str, Any]:
    """Direct call to OpenAI API"""
    url = MODEL_CONFIG["openai"]["url"]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 16000,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        return {
            "text": data["choices"][0]["message"]["content"],
            "tokens_in": data.get("usage", {}).get("prompt_tokens", 0),
            "tokens_out": data.get("usage", {}).get("completion_tokens", 0)
        }

async def call_gemini(
    prompt: str, 
    system_prompt: str, 
    api_key: str, 
    model: str = "gemini-2.0-flash-exp"
) -> Dict[str, Any]:
    """Direct call to Google Gemini API"""
    url = MODEL_CONFIG["gemini"]["url"].format(model=model)
    url = f"{url}?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Build contents with optional system instruction
    contents = []
    if system_prompt:
        contents.append({
            "role": "user",
            "parts": [{"text": f"System Instructions: {system_prompt}\n\nUser Request: {prompt}"}]
        })
    else:
        contents.append({
            "role": "user", 
            "parts": [{"text": prompt}]
        })
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 16000,
            "temperature": 0.7
        }
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Extract text from Gemini response
        text = ""
        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                text = candidate["content"]["parts"][0].get("text", "")
        
        # Gemini usage metadata
        usage = data.get("usageMetadata", {})
        
        return {
            "text": text,
            "tokens_in": usage.get("promptTokenCount", len(prompt) // 4),
            "tokens_out": usage.get("candidatesTokenCount", len(text) // 4)
        }

async def call_claude(
    prompt: str, 
    system_prompt: str, 
    api_key: str, 
    model: str = "claude-sonnet-4-20250514"
) -> Dict[str, Any]:
    """Direct call to Anthropic Claude API"""
    url = MODEL_CONFIG["claude"]["url"]
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "max_tokens": 16000,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    if system_prompt:
        payload["system"] = system_prompt
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Extract text from Claude response
        text = ""
        if "content" in data and len(data["content"]) > 0:
            text = data["content"][0].get("text", "")
        
        return {
            "text": text,
            "tokens_in": data.get("usage", {}).get("input_tokens", 0),
            "tokens_out": data.get("usage", {}).get("output_tokens", 0)
        }

async def call_grok(
    prompt: str, 
    system_prompt: str, 
    api_key: str, 
    model: str = "grok-2-latest"
) -> Dict[str, Any]:
    """Direct call to xAI Grok API"""
    url = MODEL_CONFIG["grok"]["url"]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 16000,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        return {
            "text": data["choices"][0]["message"]["content"],
            "tokens_in": data.get("usage", {}).get("prompt_tokens", 0),
            "tokens_out": data.get("usage", {}).get("completion_tokens", 0)
        }

async def call_deepseek(
    prompt: str, 
    system_prompt: str, 
    api_key: str, 
    model: str = "deepseek-chat"
) -> Dict[str, Any]:
    """Direct call to DeepSeek API (OpenAI-compatible)"""
    url = MODEL_CONFIG["deepseek"]["url"]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 16000,
        "temperature": 0.7,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        return {
            "text": data["choices"][0]["message"]["content"],
            "tokens_in": data.get("usage", {}).get("prompt_tokens", 0),
            "tokens_out": data.get("usage", {}).get("completion_tokens", 0)
        }

# =============================================================================
# OPENAI-COMPATIBLE PROVIDERS (Mistral, Groq, Together, Perplexity, Fireworks, AI21, Qwen, Moonshot, Yi, Zhipu)
# =============================================================================

async def call_openai_compatible(
    prompt: str, 
    system_prompt: str, 
    api_key: str, 
    provider: str,
    model: str = None
) -> Dict[str, Any]:
    """Generic call for OpenAI-compatible APIs (Mistral, Groq, Together, Perplexity, Fireworks, AI21, Qwen, Moonshot, Yi, Zhipu)"""
    config = MODEL_CONFIG.get(provider, {})
    url = config.get("url", "")
    if not model:
        model = config.get("default_model", "")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 16000,
        "temperature": 0.7,
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        return {
            "text": data["choices"][0]["message"]["content"],
            "tokens_in": data.get("usage", {}).get("prompt_tokens", 0),
            "tokens_out": data.get("usage", {}).get("completion_tokens", 0)
        }

async def call_cohere(
    prompt: str, 
    system_prompt: str, 
    api_key: str, 
    model: str = "command-r-plus"
) -> Dict[str, Any]:
    """Direct call to Cohere API (different format)"""
    url = MODEL_CONFIG["cohere"]["url"]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "message": prompt,
        "temperature": 0.7,
    }
    
    if system_prompt:
        payload["preamble"] = system_prompt
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        return {
            "text": data.get("text", ""),
            "tokens_in": data.get("meta", {}).get("tokens", {}).get("input_tokens", 0),
            "tokens_out": data.get("meta", {}).get("tokens", {}).get("output_tokens", 0)
        }

async def call_huggingface(
    prompt: str, 
    system_prompt: str, 
    api_key: str, 
    model: str = "meta-llama/Llama-3.3-70B-Instruct"
) -> Dict[str, Any]:
    """Direct call to Hugging Face Inference API"""
    url = MODEL_CONFIG["huggingface"]["url"].format(model=model)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 16000,
        "temperature": 0.7,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        return {
            "text": data["choices"][0]["message"]["content"],
            "tokens_in": data.get("usage", {}).get("prompt_tokens", 0),
            "tokens_out": data.get("usage", {}).get("completion_tokens", 0)
        }

# =============================================================================
# PROVIDER ROUTER
# =============================================================================

async def call_ai_provider(
    provider: str,
    prompt: str,
    system_prompt: str,
    api_key: str,
    model: str = None
) -> Dict[str, Any]:
    """Route to appropriate AI provider"""
    
    # Get default model if not specified
    if not model:
        model = MODEL_CONFIG.get(provider, {}).get("default_model", "gpt-4o")
    
    # Providers with custom API formats
    if provider == "openai":
        return await call_openai(prompt, system_prompt, api_key, model)
    elif provider == "gemini":
        return await call_gemini(prompt, system_prompt, api_key, model)
    elif provider == "claude":
        return await call_claude(prompt, system_prompt, api_key, model)
    elif provider == "cohere":
        return await call_cohere(prompt, system_prompt, api_key, model)
    
    # OpenAI-compatible providers
    elif provider in ["grok", "deepseek", "mistral", "groq", "together", "perplexity", "fireworks", "ai21", "qwen", "moonshot", "yi", "zhipu"]:
        return await call_openai_compatible(prompt, system_prompt, api_key, provider, model)
    
    # Hugging Face Inference API
    elif provider == "huggingface":
        return await call_huggingface(prompt, system_prompt, api_key, model)
    
    else:
        # Default to OpenAI
        return await call_openai(prompt, system_prompt, api_key, model)

# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

async def generate_code(
    prompt: str,
    ai_provider: str,
    existing_code: str = None,
    user_id: str = None,
    project_id: str = None,
    job_id: str = None,
    is_planner: bool = False
) -> str:
    """Generate code using AI provider - Direct API calls
    
    Args:
        prompt: The prompt to send to AI
        ai_provider: Which AI provider to use (openai, gemini, claude, grok)
        existing_code: Optional existing code to modify
        user_id: User ID for logging and BYO key lookup
        project_id: Project ID for logging
        job_id: Job ID for logging
        is_planner: If True, skip adding SYSTEM_PROMPT (prompt already contains full instructions)
    """
    start_time = time.time()
    is_byo_key = False
    model = None
    
    try:
        # Validate provider
        if ai_provider not in MODEL_CONFIG:
            ai_provider = DEFAULT_AI_PROVIDER or "openai"
        
        # Check provider health
        health = await check_provider_health(ai_provider)
        if not health["is_enabled"] or health["is_blocked"]:
            raise Exception(f"Provider {ai_provider} is currently disabled")
        
        # Build full prompt
        full_prompt = prompt
        if existing_code:
            full_prompt = f"{prompt}\n\nExisting code to modify/improve:\n{existing_code}"
        
        # Get API key - check BYO first, then platform key
        api_key = get_platform_key(ai_provider)
        if user_id:
            byo_key = await get_user_ai_key(user_id, ai_provider)
            if byo_key:
                api_key = byo_key
                is_byo_key = True
        
        if not api_key:
            raise Exception(f"No API key configured for {ai_provider}. Please add your API key in settings.")
        
        # Get model
        model = MODEL_CONFIG[ai_provider]["default_model"]
        
        # Use appropriate system prompt
        system_prompt = None if is_planner else SYSTEM_PROMPT
        
        # Call AI provider directly
        result = await call_ai_provider(
            provider=ai_provider,
            prompt=full_prompt,
            system_prompt=system_prompt,
            api_key=api_key,
            model=model
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Log AI run
        await log_ai_run(
            user_id=user_id,
            provider=ai_provider,
            model=model,
            tokens_in=result.get("tokens_in", len(full_prompt) // 4),
            tokens_out=result.get("tokens_out", len(result["text"]) // 4),
            latency_ms=latency_ms,
            status="success",
            project_id=project_id,
            job_id=job_id,
            is_byo_key=is_byo_key
        )
        
        # Update user's BYO key last used
        if is_byo_key and user_id:
            await db.user_ai_keys.update_one(
                {"user_id": user_id, "provider": ai_provider},
                {"$set": {"last_used_at": datetime.now(timezone.utc).isoformat()}}
            )
        
        return result["text"]
        
    except httpx.HTTPStatusError as e:
        latency_ms = int((time.time() - start_time) * 1000)
        error_msg = f"API Error: {e.response.status_code} - {e.response.text[:500]}"
        
        await log_ai_run(
            user_id=user_id,
            provider=ai_provider,
            model=model or "unknown",
            latency_ms=latency_ms,
            status="failed",
            error_message=error_msg,
            project_id=project_id,
            job_id=job_id,
            is_byo_key=is_byo_key
        )
        
        await log_error(
            error_type="AI_API_ERROR",
            error_message=error_msg,
            endpoint="/chat",
            user_id=user_id,
            stack_trace=traceback.format_exc()
        )
        raise Exception(f"AI generation failed: {error_msg}")
        
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        
        await log_ai_run(
            user_id=user_id,
            provider=ai_provider,
            model=model or "unknown",
            latency_ms=latency_ms,
            status="failed",
            error_message=str(e),
            project_id=project_id,
            job_id=job_id,
            is_byo_key=is_byo_key
        )
        
        await log_error(
            error_type="AI_GENERATION_ERROR",
            error_message=str(e),
            endpoint="/chat",
            user_id=user_id,
            stack_trace=traceback.format_exc()
        )
        raise Exception(f"AI generation failed: {str(e)}")
