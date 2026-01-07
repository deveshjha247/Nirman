from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid

from app.core.security import require_auth
from app.db.mongo import db
from app.services.ai_router import encrypt_api_key, get_key_hint

router = APIRouter(prefix="/ai-keys", tags=["ai-keys"])

@router.get("")
async def get_user_ai_keys(user: dict = Depends(require_auth)):
    """Get user's saved AI API keys (only hints, never full keys)"""
    keys = await db.user_ai_keys.find(
        {"user_id": user["id"]},
        {"_id": 0, "encrypted_key": 0}  # Never expose encrypted key
    ).to_list(10)
    return {"keys": keys}

@router.post("")
async def add_user_ai_key(provider: str, api_key: str, user: dict = Depends(require_auth)):
    """Add or update user's AI API key"""
    valid_providers = [
        "openai", "gemini", "claude", "grok", "deepseek",
        "mistral", "cohere", "groq", "together", "perplexity",
        "fireworks", "ai21", "qwen", "moonshot", "yi", "zhipu",
        "huggingface"
    ]
    if provider not in valid_providers:
        raise HTTPException(status_code=400, detail=f"Invalid provider. Must be one of: {valid_providers}")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Check if key exists for this provider
    existing = await db.user_ai_keys.find_one({"user_id": user["id"], "provider": provider})
    
    key_doc = {
        "user_id": user["id"],
        "provider": provider,
        "encrypted_key": encrypt_api_key(api_key),
        "key_hint": get_key_hint(api_key),
        "is_active": True,
        "last_used_at": None
    }
    
    if existing:
        await db.user_ai_keys.update_one(
            {"id": existing["id"]},
            {"$set": {**key_doc, "updated_at": now}}
        )
        return {"message": f"{provider.capitalize()} key updated", "key_hint": key_doc["key_hint"]}
    else:
        key_doc["id"] = str(uuid.uuid4())
        key_doc["created_at"] = now
        await db.user_ai_keys.insert_one(key_doc)
        return {"message": f"{provider.capitalize()} key added", "key_hint": key_doc["key_hint"]}

@router.delete("/{provider}")
async def delete_user_ai_key(provider: str, user: dict = Depends(require_auth)):
    """Delete user's AI API key"""
    result = await db.user_ai_keys.delete_one({"user_id": user["id"], "provider": provider})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"message": f"{provider.capitalize()} key deleted"}

@router.put("/{provider}/toggle")
async def toggle_user_ai_key(provider: str, is_active: bool, user: dict = Depends(require_auth)):
    """Enable/disable user's AI API key"""
    result = await db.user_ai_keys.update_one(
        {"user_id": user["id"], "provider": provider},
        {"$set": {"is_active": is_active}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"message": f"{provider.capitalize()} key {'enabled' if is_active else 'disabled'}"}

@router.get("/usage")
async def get_ai_usage_stats(user: dict = Depends(require_auth)):
    """Get user's AI usage statistics"""
    # Get usage stats
    runs = await db.ai_runs.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Calculate stats
    total_runs = len(runs)
    total_cost = sum(r.get("cost_estimate", 0) for r in runs)
    total_tokens = sum(r.get("tokens_in", 0) + r.get("tokens_out", 0) for r in runs)
    byo_runs = len([r for r in runs if r.get("is_byo_key")])
    
    # By provider
    by_provider = {}
    for r in runs:
        prov = r.get("provider", "unknown")
        by_provider[prov] = by_provider.get(prov, 0) + 1
    
    return {
        "total_runs": total_runs,
        "total_cost": round(total_cost, 4),
        "total_tokens": total_tokens,
        "byo_runs": byo_runs,
        "platform_runs": total_runs - byo_runs,
        "by_provider": by_provider,
        "recent_runs": runs[:10]
    }

@router.get("/providers")
async def get_available_providers(user: dict = Depends(require_auth)):
    """Get available AI providers with status"""
    providers = [
        # === US/Global Providers ===
        {
            "id": "openai",
            "name": "OpenAI",
            "models": ["GPT-5.2", "GPT-4o", "GPT-4o-mini", "o1", "o1-mini"],
            "key_prefix": "sk-",
            "docs_url": "https://platform.openai.com/api-keys",
            "region": "US"
        },
        {
            "id": "gemini",
            "name": "Google Gemini",
            "models": ["Gemini 2.5 Flash", "Gemini 2.5 Pro", "Gemini 2.0 Flash"],
            "key_prefix": "AI",
            "docs_url": "https://makersuite.google.com/app/apikey",
            "region": "US"
        },
        {
            "id": "claude",
            "name": "Anthropic Claude",
            "models": ["Claude Sonnet 4", "Claude 3.5 Sonnet", "Claude 3 Opus", "Claude 3 Haiku"],
            "key_prefix": "sk-ant-",
            "docs_url": "https://console.anthropic.com/settings/keys",
            "region": "US"
        },
        {
            "id": "grok",
            "name": "xAI Grok",
            "models": ["Grok-2", "Grok Beta"],
            "key_prefix": "xai-",
            "docs_url": "https://console.x.ai/",
            "region": "US"
        },
        {
            "id": "mistral",
            "name": "Mistral AI",
            "models": ["Mistral Large", "Mistral Medium", "Mistral Small", "Codestral", "Pixtral"],
            "key_prefix": "",
            "docs_url": "https://console.mistral.ai/api-keys/",
            "region": "EU"
        },
        {
            "id": "cohere",
            "name": "Cohere",
            "models": ["Command R+", "Command R", "Command", "Command Light"],
            "key_prefix": "",
            "docs_url": "https://dashboard.cohere.com/api-keys",
            "region": "US"
        },
        {
            "id": "groq",
            "name": "Groq (Ultra Fast)",
            "models": ["Llama 3.3 70B", "Llama 3.1 8B", "Mixtral 8x7B", "Gemma2 9B"],
            "key_prefix": "gsk_",
            "docs_url": "https://console.groq.com/keys",
            "region": "US"
        },
        {
            "id": "together",
            "name": "Together AI",
            "models": ["Llama 3.3 70B", "Llama 3.1 405B", "Qwen 2.5 72B", "DeepSeek R1"],
            "key_prefix": "",
            "docs_url": "https://api.together.xyz/settings/api-keys",
            "region": "US"
        },
        {
            "id": "perplexity",
            "name": "Perplexity (Search AI)",
            "models": ["Sonar Large Online", "Sonar Small Online", "Sonar Huge Online"],
            "key_prefix": "pplx-",
            "docs_url": "https://www.perplexity.ai/settings/api",
            "region": "US"
        },
        {
            "id": "fireworks",
            "name": "Fireworks AI",
            "models": ["Llama 3.3 70B", "Llama 3.1 405B", "Qwen 2.5 72B", "DeepSeek R1"],
            "key_prefix": "fw_",
            "docs_url": "https://fireworks.ai/api-keys",
            "region": "US"
        },
        {
            "id": "ai21",
            "name": "AI21 Labs",
            "models": ["Jamba 1.5 Large", "Jamba 1.5 Mini"],
            "key_prefix": "",
            "docs_url": "https://studio.ai21.com/account/api-key",
            "region": "US"
        },
        # === Chinese AI Providers ===
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "models": ["DeepSeek Chat", "DeepSeek Coder", "DeepSeek Reasoner (R1)"],
            "key_prefix": "sk-",
            "docs_url": "https://platform.deepseek.com/api_keys",
            "region": "CN"
        },
        {
            "id": "qwen",
            "name": "Alibaba Qwen",
            "models": ["Qwen Max", "Qwen Plus", "Qwen Turbo", "Qwen Coder"],
            "key_prefix": "sk-",
            "docs_url": "https://dashscope.console.aliyun.com/apiKey",
            "region": "CN"
        },
        {
            "id": "moonshot",
            "name": "Moonshot (Kimi)",
            "models": ["Moonshot 128K", "Moonshot 32K", "Moonshot 8K"],
            "key_prefix": "sk-",
            "docs_url": "https://platform.moonshot.cn/console/api-keys",
            "region": "CN"
        },
        {
            "id": "yi",
            "name": "01.AI (Yi)",
            "models": ["Yi Lightning", "Yi Large", "Yi Medium", "Yi Large Turbo"],
            "key_prefix": "",
            "docs_url": "https://platform.lingyiwanwu.com/apikeys",
            "region": "CN"
        },
        {
            "id": "zhipu",
            "name": "Zhipu AI (GLM)",
            "models": ["GLM-4 Plus", "GLM-4 Air", "GLM-4 Flash", "GLM-4 Long"],
            "key_prefix": "",
            "docs_url": "https://open.bigmodel.cn/usercenter/apikeys",
            "region": "CN"
        },
        # === Open Source / Hugging Face ===
        {
            "id": "huggingface",
            "name": "Hugging Face",
            "models": ["Llama 3.3 70B", "Llama 3.1 8B", "Qwen 2.5 72B", "Qwen Coder 32B", "Mixtral 8x7B", "Phi-3", "Gemma 2", "DeepSeek R1"],
            "key_prefix": "hf_",
            "docs_url": "https://huggingface.co/settings/tokens",
            "region": "Open Source"
        }
    ]
    
    # Check user's saved keys
    user_keys = await db.user_ai_keys.find(
        {"user_id": user["id"]},
        {"_id": 0, "provider": 1, "is_active": 1, "key_hint": 1, "last_used_at": 1}
    ).to_list(20)
    
    user_keys_map = {k["provider"]: k for k in user_keys}
    
    for prov in providers:
        if prov["id"] in user_keys_map:
            prov["has_key"] = True
            prov["is_active"] = user_keys_map[prov["id"]].get("is_active", True)
            prov["key_hint"] = user_keys_map[prov["id"]].get("key_hint")
            prov["last_used"] = user_keys_map[prov["id"]].get("last_used_at")
        else:
            prov["has_key"] = False
            prov["is_active"] = False
    
    return {"providers": providers}
