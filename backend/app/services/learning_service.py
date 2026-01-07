"""
Learning Service - Self-Learning Engine for Nirman.tech
Handles event tracking, preference learning, pattern extraction
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict

from app.db.mongo import db
from app.models.learning import (
    ProjectEvent, EventType, SpecVersion, UserPreferences, ThemePreference,
    PatternLibrary, PatternCategory, ErrorSignature,
    IndustryInsights, UserInsights
)


# =============================================================================
# EVENT TRACKING
# =============================================================================

async def track_event(
    user_id: str,
    project_id: str,
    event_type: EventType,
    payload: Dict[str, Any] = None,
    metadata: Dict[str, Any] = None
) -> ProjectEvent:
    """
    Track any user action for learning.
    This is the core of the self-learning system.
    """
    event = ProjectEvent(
        id=str(uuid.uuid4()),
        user_id=user_id,
        project_id=project_id,
        event_type=event_type,
        payload=sanitize_payload(payload or {}),
        metadata=metadata or {},
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    await db.project_events.insert_one(event.model_dump())
    
    # Trigger real-time preference updates for certain events
    if event_type in [EventType.THEME_CHANGED, EventType.SECTION_ADDED, 
                      EventType.LAYOUT_CHANGED, EventType.BUILD_SUCCEEDED]:
        await update_preferences_from_event(user_id, event)
    
    return event


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove PII and sensitive data from payload.
    Never store: API keys, passwords, emails, phone numbers
    """
    sensitive_keys = ['api_key', 'password', 'secret', 'token', 'email', 
                      'phone', 'address', 'credit_card', 'ssn']
    
    sanitized = {}
    for key, value in payload.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            continue  # Skip sensitive fields
        if isinstance(value, dict):
            sanitized[key] = sanitize_payload(value)
        elif isinstance(value, str) and len(value) > 500:
            sanitized[key] = value[:500] + "..."  # Truncate long strings
        else:
            sanitized[key] = value
    
    return sanitized


async def get_user_events(
    user_id: str,
    event_types: List[EventType] = None,
    project_id: str = None,
    limit: int = 100,
    days_back: int = 30
) -> List[ProjectEvent]:
    """Get user's recent events"""
    query = {
        "user_id": user_id,
        "created_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()}
    }
    
    if event_types:
        query["event_type"] = {"$in": [e.value for e in event_types]}
    if project_id:
        query["project_id"] = project_id
    
    cursor = db.project_events.find(query).sort("created_at", -1).limit(limit)
    events = await cursor.to_list(length=limit)
    return [ProjectEvent(**e) for e in events]


# =============================================================================
# SPEC VERSION TRACKING
# =============================================================================

async def save_spec_version(
    project_id: str,
    user_id: str,
    spec_json: Dict[str, Any],
    source: str = "planner",
    diff_summary: str = None
) -> SpecVersion:
    """Save a new version of project spec"""
    # Get current version number
    latest = await db.spec_versions.find_one(
        {"project_id": project_id},
        sort=[("version", -1)]
    )
    version = (latest["version"] + 1) if latest else 1
    
    spec_version = SpecVersion(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=user_id,
        version=version,
        spec_json=spec_json,
        diff_summary=diff_summary,
        source=source,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    await db.spec_versions.insert_one(spec_version.model_dump())
    return spec_version


async def get_spec_versions(project_id: str, limit: int = 10) -> List[SpecVersion]:
    """Get version history of a project's spec"""
    cursor = db.spec_versions.find({"project_id": project_id}).sort("version", -1).limit(limit)
    versions = await cursor.to_list(length=limit)
    return [SpecVersion(**v) for v in versions]


# =============================================================================
# USER PREFERENCES (PERSONALIZATION)
# =============================================================================

async def get_user_preferences(user_id: str) -> UserPreferences:
    """Get or create user preferences"""
    prefs = await db.user_preferences.find_one({"user_id": user_id})
    
    if prefs:
        return UserPreferences(**prefs)
    
    # Create default preferences
    now = datetime.now(timezone.utc).isoformat()
    default_prefs = UserPreferences(
        user_id=user_id,
        created_at=now,
        last_updated=now
    )
    await db.user_preferences.insert_one(default_prefs.model_dump())
    return default_prefs


async def update_user_preferences(
    user_id: str,
    updates: Dict[str, Any]
) -> UserPreferences:
    """Update user preferences"""
    updates["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    await db.user_preferences.update_one(
        {"user_id": user_id},
        {"$set": updates},
        upsert=True
    )
    
    return await get_user_preferences(user_id)


async def update_preferences_from_event(user_id: str, event: ProjectEvent):
    """
    Auto-update preferences based on user actions.
    This is the "learning from behavior" part.
    """
    prefs = await get_user_preferences(user_id)
    
    # Skip if personalization is disabled
    if not prefs.personalization_enabled:
        return
    
    updates = {}
    
    # Learn theme preferences
    if event.event_type == EventType.THEME_CHANGED:
        theme_data = event.payload.get("theme", {})
        if theme_data:
            current_theme = prefs.preferred_theme.model_dump()
            # Merge new theme preferences
            for key, value in theme_data.items():
                if value:
                    current_theme[key] = value
            updates["preferred_theme"] = current_theme
    
    # Learn section preferences
    if event.event_type == EventType.SECTION_ADDED:
        section = event.payload.get("section_type")
        if section:
            sections = prefs.preferred_sections.copy()
            if section not in sections:
                sections.append(section)
            updates["preferred_sections"] = sections[-10:]  # Keep last 10
            
            # Update section weights
            weights = prefs.section_weights.copy()
            weights[section] = weights.get(section, 0) + 0.1
            # Normalize weights
            max_weight = max(weights.values()) if weights else 1
            weights = {k: min(v / max_weight, 1.0) for k, v in weights.items()}
            updates["section_weights"] = weights
    
    # Learn layout preferences
    if event.event_type == EventType.LAYOUT_CHANGED:
        layout = event.payload.get("layout_type")
        if layout:
            layouts = prefs.preferred_layouts.copy()
            if layout not in layouts:
                layouts.append(layout)
            updates["preferred_layouts"] = layouts[-5:]  # Keep last 5
    
    # Learn industry affinity from successful builds
    if event.event_type == EventType.BUILD_SUCCEEDED:
        industry = event.payload.get("industry")
        if industry:
            affinity = prefs.industry_affinity.copy()
            affinity[industry] = affinity.get(industry, 0) + 0.15
            # Normalize
            max_aff = max(affinity.values()) if affinity else 1
            affinity = {k: min(v / max_aff, 1.0) for k, v in affinity.items()}
            updates["industry_affinity"] = affinity
    
    if updates:
        await update_user_preferences(user_id, updates)


# =============================================================================
# PATTERN LIBRARY (GLOBAL LEARNING)
# =============================================================================

async def get_best_patterns(
    category: PatternCategory = None,
    industry: str = None,
    limit: int = 5,
    min_success_score: float = 0.5
) -> List[PatternLibrary]:
    """Get best performing patterns for a category/industry"""
    query = {"success_score": {"$gte": min_success_score}}
    
    if category:
        query["category"] = category.value
    if industry:
        query["industry"] = industry
    
    cursor = db.pattern_library.find(query).sort("success_score", -1).limit(limit)
    patterns = await cursor.to_list(length=limit)
    return [PatternLibrary(**p) for p in patterns]


async def get_pattern_for_context(
    industry: str,
    sections: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Get best patterns for each section in the given industry.
    Returns: {section_type: pattern_snippet}
    """
    patterns = {}
    
    for section in sections:
        try:
            category = PatternCategory(section.lower())
        except ValueError:
            continue
        
        best = await get_best_patterns(category=category, industry=industry, limit=1)
        if best:
            patterns[section] = best[0].spec_snippet
    
    return patterns


async def record_pattern_usage(
    pattern_id: str,
    outcome: str  # "approved", "deployed", "regenerated"
):
    """Update pattern metrics based on usage"""
    updates = {"$inc": {"total_uses": 1}}
    
    if outcome == "approved":
        updates["$inc"]["approval_count"] = 1
    elif outcome == "deployed":
        updates["$inc"]["deploy_count"] = 1
    elif outcome == "regenerated":
        updates["$inc"]["regenerate_count"] = 1
    
    await db.pattern_library.update_one({"id": pattern_id}, updates)
    
    # Recalculate success score
    pattern = await db.pattern_library.find_one({"id": pattern_id})
    if pattern and pattern.get("total_uses", 0) > 0:
        # Success = (approvals + deploys*2) / (total + regenerates)
        # Higher weight for deploys, penalty for regenerations
        score = (
            (pattern.get("approval_count", 0) + pattern.get("deploy_count", 0) * 2) /
            (pattern.get("total_uses", 1) + pattern.get("regenerate_count", 0))
        )
        score = min(score, 1.0)
        
        await db.pattern_library.update_one(
            {"id": pattern_id},
            {"$set": {"success_score": score, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )


async def extract_and_save_pattern(
    project_id: str,
    category: PatternCategory,
    industry: str,
    spec_snippet: Dict[str, Any],
    tags: List[str] = None
) -> PatternLibrary:
    """
    Extract a successful pattern from a project.
    Called when a project gets deployed successfully.
    """
    # Check if similar pattern exists
    existing = await db.pattern_library.find_one({
        "category": category.value,
        "industry": industry,
        # Simple similarity check - could be improved with embeddings
    })
    
    if existing:
        # Update existing pattern
        await record_pattern_usage(existing["id"], "deployed")
        return PatternLibrary(**existing)
    
    # Create new pattern
    now = datetime.now(timezone.utc).isoformat()
    pattern = PatternLibrary(
        id=str(uuid.uuid4()),
        category=category,
        industry=industry,
        pattern_name=f"{industry.title()} {category.value.title()} Pattern",
        spec_snippet=spec_snippet,
        success_score=0.5,  # Start neutral
        approval_count=1,
        deploy_count=1,
        total_uses=1,
        tags=tags or [],
        example_project_ids=[project_id],
        created_at=now,
        updated_at=now
    )
    
    await db.pattern_library.insert_one(pattern.model_dump())
    return pattern


# =============================================================================
# ERROR SIGNATURES (AUTO-FIX LEARNING)
# =============================================================================

def normalize_error(error_text: str) -> str:
    """Normalize error text for consistent hashing"""
    import re
    # Remove line numbers, file paths, timestamps
    normalized = re.sub(r'line \d+', 'line N', error_text.lower())
    normalized = re.sub(r'at .*?:\d+:\d+', 'at FILE:N:N', normalized)
    normalized = re.sub(r'/[\w/.-]+\.(js|ts|py|html|css)', 'FILE', normalized)
    normalized = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized[:500]  # Limit length


def hash_error(error_text: str) -> str:
    """Create signature hash for error"""
    normalized = normalize_error(error_text)
    return hashlib.md5(normalized.encode()).hexdigest()


async def record_error(
    error_text: str,
    error_category: str,
    context: Dict[str, Any] = None
) -> ErrorSignature:
    """
    Record an error occurrence.
    If signature exists, increment count. Otherwise create new.
    """
    sig_hash = hash_error(error_text)
    now = datetime.now(timezone.utc).isoformat()
    
    existing = await db.error_signatures.find_one({"signature_hash": sig_hash})
    
    if existing:
        await db.error_signatures.update_one(
            {"signature_hash": sig_hash},
            {
                "$inc": {"occurrence_count": 1},
                "$set": {"last_seen": now, "updated_at": now}
            }
        )
        existing["occurrence_count"] += 1
        return ErrorSignature(**existing)
    
    # Create new error signature
    error_sig = ErrorSignature(
        id=str(uuid.uuid4()),
        signature_hash=sig_hash,
        error_pattern=normalize_error(error_text)[:100],
        error_category=error_category,
        error_sample=error_text[:500],
        trigger_context=json.dumps(context)[:200] if context else None,
        fix_type="unknown",
        occurrence_count=1,
        fix_success_count=0,
        success_rate=0.0,
        first_seen=now,
        last_seen=now,
        updated_at=now
    )
    
    await db.error_signatures.insert_one(error_sig.model_dump())
    return error_sig


async def get_known_fix(error_text: str) -> Optional[ErrorSignature]:
    """
    Check if we have a known fix for this error.
    Returns fix if success_rate > 0.5
    """
    sig_hash = hash_error(error_text)
    
    error_sig = await db.error_signatures.find_one({
        "signature_hash": sig_hash,
        "success_rate": {"$gte": 0.5},
        "fix_patch": {"$ne": None}
    })
    
    if error_sig:
        return ErrorSignature(**error_sig)
    return None


async def record_fix_attempt(
    error_text: str,
    success: bool,
    fix_patch: str = None,
    fix_instructions: str = None
):
    """Record whether a fix attempt worked"""
    sig_hash = hash_error(error_text)
    now = datetime.now(timezone.utc).isoformat()
    
    updates = {"updated_at": now}
    
    if success:
        updates["$inc"] = {"fix_success_count": 1}
        if fix_patch:
            updates["$set"] = {
                "fix_patch": fix_patch,
                "fix_type": "auto",
                "updated_at": now
            }
        if fix_instructions:
            updates.setdefault("$set", {})["fix_instructions"] = fix_instructions
    
    await db.error_signatures.update_one(
        {"signature_hash": sig_hash},
        updates
    )
    
    # Recalculate success rate
    error_sig = await db.error_signatures.find_one({"signature_hash": sig_hash})
    if error_sig and error_sig.get("occurrence_count", 0) > 0:
        rate = error_sig.get("fix_success_count", 0) / error_sig.get("occurrence_count", 1)
        await db.error_signatures.update_one(
            {"signature_hash": sig_hash},
            {"$set": {"success_rate": rate}}
        )


async def get_frequent_errors(limit: int = 10, min_occurrences: int = 3) -> List[ErrorSignature]:
    """Get most frequent errors that need fixes"""
    cursor = db.error_signatures.find({
        "occurrence_count": {"$gte": min_occurrences},
        "success_rate": {"$lt": 0.5}  # Still problematic
    }).sort("occurrence_count", -1).limit(limit)
    
    errors = await cursor.to_list(length=limit)
    return [ErrorSignature(**e) for e in errors]


# =============================================================================
# INSIGHTS & ANALYTICS
# =============================================================================

async def get_industry_insights(industry: str) -> IndustryInsights:
    """Get aggregated insights for an industry"""
    # Count projects
    total = await db.project_events.count_documents({
        "event_type": EventType.PROJECT_CREATED.value,
        "payload.industry": industry
    })
    
    # Approval rate
    approved = await db.project_events.count_documents({
        "event_type": EventType.PLAN_APPROVED.value,
        "payload.industry": industry
    })
    
    # Deploy rate
    deployed = await db.project_events.count_documents({
        "event_type": EventType.DEPLOY_SUCCEEDED.value,
        "payload.industry": industry
    })
    
    # Get top sections
    pipeline = [
        {"$match": {"event_type": EventType.SECTION_ADDED.value, "payload.industry": industry}},
        {"$group": {"_id": "$payload.section_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    section_counts = await db.project_events.aggregate(pipeline).to_list(length=5)
    top_sections = [s["_id"] for s in section_counts if s["_id"]]
    
    # Get top patterns
    patterns = await get_best_patterns(industry=industry, limit=5)
    top_patterns = [p.id for p in patterns]
    
    return IndustryInsights(
        industry=industry,
        total_projects=total,
        approval_rate=approved / max(total, 1),
        deploy_rate=deployed / max(total, 1),
        top_sections=top_sections,
        top_patterns=top_patterns
    )


async def get_user_insights(user_id: str) -> UserInsights:
    """Get personalized insights for a user"""
    # Count projects
    total = await db.project_events.count_documents({
        "user_id": user_id,
        "event_type": EventType.PROJECT_CREATED.value
    })
    
    # Get preferred industry
    pipeline = [
        {"$match": {"user_id": user_id, "payload.industry": {"$exists": True}}},
        {"$group": {"_id": "$payload.industry", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    industry_counts = await db.project_events.aggregate(pipeline).to_list(length=1)
    preferred_industry = industry_counts[0]["_id"] if industry_counts else None
    
    # Get top sections
    prefs = await get_user_preferences(user_id)
    top_sections = sorted(
        prefs.section_weights.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    return UserInsights(
        user_id=user_id,
        total_projects=total,
        preferred_industry=preferred_industry,
        top_sections=[s[0] for s in top_sections]
    )


# =============================================================================
# CONTEXT BUILDER FOR AI PROMPTS
# =============================================================================

async def build_learning_context(
    user_id: str,
    industry: str = None,
    sections: List[str] = None
) -> Dict[str, Any]:
    """
    Build learning context to inject into AI prompts.
    This is what makes the AI "personalized" and "smart".
    """
    context = {
        "user_preferences": None,
        "pattern_snippets": {},
        "personalization_enabled": False,
        "global_learning_enabled": False
    }
    
    # Get user preferences
    prefs = await get_user_preferences(user_id)
    context["personalization_enabled"] = prefs.personalization_enabled
    context["global_learning_enabled"] = prefs.global_learning_enabled
    
    # Add preferences if enabled
    if prefs.personalization_enabled:
        context["user_preferences"] = {
            "theme": prefs.preferred_theme.model_dump(),
            "tone": prefs.preferred_tone,
            "density": prefs.preferred_density,
            "sections": prefs.preferred_sections,
            "layouts": prefs.preferred_layouts
        }
    
    # Add patterns if global learning enabled OR using internal patterns
    if industry and sections:
        patterns = await get_pattern_for_context(industry, sections)
        if patterns:
            context["pattern_snippets"] = patterns
    
    return context
