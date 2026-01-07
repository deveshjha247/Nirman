"""
Learning Routes - Self-Learning API Endpoints
Handles preferences, patterns, and analytics
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timezone

from app.db.mongo import db
from app.core.security import require_auth
from app.models.learning import (
    EventType, UserPreferences, ThemePreference,
    PatternLibrary, PatternCategory
)
from app.services.learning_service import (
    track_event,
    get_user_events,
    get_user_preferences,
    update_user_preferences,
    get_user_insights,
    get_best_patterns,
    get_industry_insights
)

router = APIRouter(prefix="/api/learning", tags=["learning"])


# =============================================================================
# USER PREFERENCES
# =============================================================================

@router.get("/preferences")
async def get_preferences(current_user: dict = Depends(require_auth)):
    """Get current user's learning preferences"""
    user_id = current_user["id"]
    prefs = await get_user_preferences(user_id)
    
    return {
        "success": True,
        "preferences": prefs.model_dump() if prefs else None,
        "personalization_enabled": current_user.get("personalization_enabled", True),
        "global_learning_enabled": current_user.get("global_learning_enabled", False)
    }


@router.put("/preferences")
async def update_preferences(
    theme: Optional[ThemePreference] = None,
    tone: Optional[str] = None,
    sections: Optional[List[str]] = None,
    layouts: Optional[List[str]] = None,
    current_user: dict = Depends(require_auth)
):
    """Update user's preferences manually"""
    user_id = current_user["id"]
    
    updates = {}
    if theme:
        updates["preferred_theme"] = theme.model_dump()
    if tone:
        updates["preferred_tone"] = tone
    if sections:
        updates["preferred_sections"] = sections
    if layouts:
        updates["preferred_layouts"] = layouts
    
    if updates:
        updates["last_updated"] = datetime.now(timezone.utc).isoformat()
        await db.user_preferences.update_one(
            {"user_id": user_id},
            {"$set": updates},
            upsert=True
        )
    
    return {"success": True, "message": "Preferences updated"}


@router.delete("/preferences")
async def reset_preferences(current_user: dict = Depends(require_auth)):
    """Reset all learning preferences"""
    user_id = current_user["id"]
    await db.user_preferences.delete_one({"user_id": user_id})
    return {"success": True, "message": "Preferences reset"}


# =============================================================================
# PRIVACY CONTROLS
# =============================================================================

@router.put("/privacy")
async def update_privacy_settings(
    personalization_enabled: bool = True,
    global_learning_enabled: bool = False,
    current_user: dict = Depends(require_auth)
):
    """
    Toggle learning features:
    - personalization_enabled: Learn from user's own data (default ON)
    - global_learning_enabled: Contribute anonymized patterns to improve Nirman (default OFF)
    """
    user_id = current_user["id"]
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "personalization_enabled": personalization_enabled,
            "global_learning_enabled": global_learning_enabled
        }}
    )
    
    return {
        "success": True,
        "personalization_enabled": personalization_enabled,
        "global_learning_enabled": global_learning_enabled,
        "message": "Privacy settings updated"
    }


# =============================================================================
# USER INSIGHTS & ANALYTICS
# =============================================================================

@router.get("/insights")
async def get_my_insights(current_user: dict = Depends(require_auth)):
    """Get personalized insights about user's building patterns"""
    user_id = current_user["id"]
    insights = await get_user_insights(user_id)
    return {
        "success": True,
        "insights": insights.model_dump() if insights else None
    }


@router.get("/events")
async def get_my_events(
    project_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    current_user: dict = Depends(require_auth)
):
    """Get user's recent events"""
    user_id = current_user["id"]
    
    event_types = [EventType(event_type)] if event_type else None
    events = await get_user_events(
        user_id=user_id,
        event_types=event_types,
        project_id=project_id,
        limit=limit
    )
    
    return {
        "success": True,
        "events": [e.model_dump() for e in events],
        "count": len(events)
    }


# =============================================================================
# PATTERNS (Public - Anonymized)
# =============================================================================

@router.get("/patterns")
async def get_patterns(
    category: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = Query(default=10, le=50)
):
    """Get best patterns for an industry/category (anonymized, public)"""
    patterns = await get_best_patterns(
        category=PatternCategory(category) if category else None,
        industry=industry,
        limit=limit
    )
    
    return {
        "success": True,
        "patterns": [p.model_dump() for p in patterns],
        "count": len(patterns)
    }


@router.get("/industries/{industry}")
async def get_industry_stats(industry: str):
    """Get insights about a specific industry"""
    insights = await get_industry_insights(industry)
    
    if not insights:
        raise HTTPException(status_code=404, detail="Industry not found")
    
    return {
        "success": True,
        "insights": insights.model_dump()
    }


# =============================================================================
# ADMIN ENDPOINTS (for debugging)
# =============================================================================

@router.get("/admin/stats", include_in_schema=False)
async def get_learning_stats(current_user: dict = Depends(require_auth)):
    """Admin: Get overall learning system stats"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    total_events = await db.project_events.count_documents({})
    total_patterns = await db.pattern_library.count_documents({})
    total_preferences = await db.user_preferences.count_documents({})
    total_errors = await db.error_signatures.count_documents({})
    
    # Get event distribution
    pipeline = [
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    event_dist = await db.project_events.aggregate(pipeline).to_list(length=50)
    
    return {
        "success": True,
        "stats": {
            "total_events": total_events,
            "total_patterns": total_patterns,
            "total_user_preferences": total_preferences,
            "total_error_signatures": total_errors,
            "event_distribution": {e["_id"]: e["count"] for e in event_dist}
        }
    }
