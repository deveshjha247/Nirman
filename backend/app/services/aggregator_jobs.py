"""
Aggregator Jobs - Background tasks for learning pipeline
Runs hourly/nightly to extract patterns and build auto-fix library
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from collections import defaultdict
import json

from app.db.mongo import db
from app.models.learning import (
    EventType, PatternCategory, PatternLibrary, ErrorSignature
)
from app.services.learning_service import (
    extract_and_save_pattern, record_error, get_user_preferences,
    update_user_preferences
)


# =============================================================================
# STEP B: PATTERN EXTRACTION (Nightly Job)
# =============================================================================

async def extract_winning_patterns(days_back: int = 7, min_success_count: int = 3):
    """
    Extract winning patterns from successful projects.
    Run this nightly.
    
    Looks for:
    - Projects that were approved without major modifications
    - Projects that were deployed successfully
    - Sections that weren't regenerated (first attempt was good)
    """
    print(f"[Aggregator] Starting pattern extraction for last {days_back} days...")
    
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
    
    # Find successfully deployed projects
    deployed_events = await db.project_events.find({
        "event_type": EventType.DEPLOY_SUCCEEDED.value,
        "created_at": {"$gte": cutoff}
    }).to_list(length=1000)
    
    print(f"[Aggregator] Found {len(deployed_events)} successful deployments")
    
    patterns_extracted = 0
    
    for event in deployed_events:
        project_id = event["project_id"]
        user_id = event["user_id"]
        
        # Check if user opted into global learning
        prefs = await get_user_preferences(user_id)
        if not prefs.global_learning_enabled:
            continue
        
        # Get the final spec for this project
        spec_version = await db.spec_versions.find_one(
            {"project_id": project_id},
            sort=[("version", -1)]
        )
        
        if not spec_version:
            continue
        
        spec = spec_version.get("spec_json", {})
        industry = spec.get("industry", "general")
        
        # Check if this project had minimal regenerations (quality indicator)
        regen_count = await db.project_events.count_documents({
            "project_id": project_id,
            "event_type": EventType.SECTION_REGENERATED.value
        })
        
        # Only extract patterns from high-quality projects
        if regen_count > 3:  # Too many regenerations = not a good pattern
            continue
        
        # Extract patterns for each section
        sections = spec.get("sections", [])
        for section in sections:
            section_type = section.get("type", "").lower()
            
            try:
                category = PatternCategory(section_type)
            except ValueError:
                continue
            
            # Check if this section was regenerated
            section_regen = await db.project_events.count_documents({
                "project_id": project_id,
                "event_type": EventType.SECTION_REGENERATED.value,
                "payload.section_type": section_type
            })
            
            if section_regen == 0:  # First attempt was good!
                await extract_and_save_pattern(
                    project_id=project_id,
                    category=category,
                    industry=industry,
                    spec_snippet=section,
                    tags=section.get("tags", [])
                )
                patterns_extracted += 1
    
    print(f"[Aggregator] Extracted {patterns_extracted} new patterns")
    return patterns_extracted


async def calculate_pattern_scores():
    """
    Recalculate success scores for all patterns.
    Run this hourly.
    """
    print("[Aggregator] Recalculating pattern scores...")
    
    cursor = db.pattern_library.find({})
    patterns = await cursor.to_list(length=10000)
    
    updated = 0
    for pattern in patterns:
        total = pattern.get("total_uses", 0)
        if total == 0:
            continue
        
        # Success = (approvals + deploys*2) / (total + regenerates)
        approvals = pattern.get("approval_count", 0)
        deploys = pattern.get("deploy_count", 0)
        regens = pattern.get("regenerate_count", 0)
        
        score = (approvals + deploys * 2) / (total + regens + 1)
        score = min(score, 1.0)
        
        await db.pattern_library.update_one(
            {"id": pattern["id"]},
            {"$set": {"success_score": score, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        updated += 1
    
    print(f"[Aggregator] Updated {updated} pattern scores")
    return updated


# =============================================================================
# STEP C: USER PREFERENCE AGGREGATION
# =============================================================================

async def aggregate_user_preferences(days_back: int = 30):
    """
    Aggregate user behavior into preferences.
    Run this daily.
    """
    print(f"[Aggregator] Aggregating user preferences for last {days_back} days...")
    
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
    
    # Get all users with recent activity
    user_ids = await db.project_events.distinct("user_id", {
        "created_at": {"$gte": cutoff}
    })
    
    print(f"[Aggregator] Processing {len(user_ids)} active users")
    
    for user_id in user_ids:
        prefs = await get_user_preferences(user_id)
        
        if not prefs.personalization_enabled:
            continue
        
        updates = {}
        
        # Aggregate section preferences
        section_counts = defaultdict(int)
        cursor = db.project_events.find({
            "user_id": user_id,
            "event_type": EventType.SECTION_ADDED.value,
            "created_at": {"$gte": cutoff}
        })
        
        async for event in cursor:
            section = event.get("payload", {}).get("section_type")
            if section:
                section_counts[section] += 1
        
        if section_counts:
            # Convert counts to weights
            max_count = max(section_counts.values())
            section_weights = {k: v / max_count for k, v in section_counts.items()}
            updates["section_weights"] = section_weights
            updates["preferred_sections"] = sorted(
                section_counts.keys(),
                key=lambda x: section_counts[x],
                reverse=True
            )[:10]
        
        # Aggregate industry affinity
        industry_counts = defaultdict(int)
        cursor = db.project_events.find({
            "user_id": user_id,
            "event_type": {"$in": [
                EventType.BUILD_SUCCEEDED.value,
                EventType.DEPLOY_SUCCEEDED.value
            ]},
            "created_at": {"$gte": cutoff}
        })
        
        async for event in cursor:
            industry = event.get("payload", {}).get("industry")
            if industry:
                industry_counts[industry] += 1
        
        if industry_counts:
            max_ind = max(industry_counts.values())
            industry_affinity = {k: v / max_ind for k, v in industry_counts.items()}
            updates["industry_affinity"] = industry_affinity
        
        # Aggregate tone preference (from successful projects)
        tone_counts = defaultdict(int)
        cursor = db.project_events.find({
            "user_id": user_id,
            "event_type": EventType.PLAN_APPROVED.value,
            "created_at": {"$gte": cutoff}
        })
        
        async for event in cursor:
            tone = event.get("payload", {}).get("tone")
            if tone:
                tone_counts[tone] += 1
        
        if tone_counts:
            preferred_tone = max(tone_counts.keys(), key=lambda x: tone_counts[x])
            updates["preferred_tone"] = preferred_tone
        
        if updates:
            await update_user_preferences(user_id, updates)
    
    print(f"[Aggregator] Updated preferences for {len(user_ids)} users")
    return len(user_ids)


# =============================================================================
# STEP D: AUTO-FIX LIBRARY BUILDING
# =============================================================================

async def build_autofix_library(days_back: int = 30, min_occurrences: int = 3):
    """
    Analyze build failures and extract common fixes.
    Run this daily.
    """
    print(f"[Aggregator] Building auto-fix library for last {days_back} days...")
    
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
    
    # Get all build failures
    failures = await db.project_events.find({
        "event_type": EventType.BUILD_FAILED.value,
        "created_at": {"$gte": cutoff}
    }).to_list(length=10000)
    
    print(f"[Aggregator] Found {len(failures)} build failures")
    
    # Group failures by error signature
    error_groups = defaultdict(list)
    
    for failure in failures:
        error_text = failure.get("payload", {}).get("error_message", "")
        if not error_text:
            continue
        
        # Record error
        error_sig = await record_error(
            error_text=error_text,
            error_category="build",
            context=failure.get("payload", {})
        )
        
        error_groups[error_sig.signature_hash].append(failure)
    
    # Find errors that were later fixed
    fixed_count = 0
    
    for sig_hash, failures in error_groups.items():
        if len(failures) < min_occurrences:
            continue
        
        # Check if any of these projects succeeded after the failure
        for failure in failures:
            project_id = failure["project_id"]
            failure_time = failure["created_at"]
            
            # Look for success after failure
            success = await db.project_events.find_one({
                "project_id": project_id,
                "event_type": EventType.BUILD_SUCCEEDED.value,
                "created_at": {"$gt": failure_time}
            })
            
            if success:
                # Try to find what changed between failure and success
                spec_before = await db.spec_versions.find_one({
                    "project_id": project_id,
                    "created_at": {"$lte": failure_time}
                }, sort=[("version", -1)])
                
                spec_after = await db.spec_versions.find_one({
                    "project_id": project_id,
                    "created_at": {"$gt": failure_time}
                }, sort=[("version", 1)])
                
                if spec_before and spec_after:
                    # Record this as a successful fix pattern
                    diff_summary = spec_after.get("diff_summary", "Unknown fix")
                    
                    await db.error_signatures.update_one(
                        {"signature_hash": sig_hash},
                        {
                            "$set": {
                                "fix_instructions": diff_summary,
                                "fix_type": "learned",
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            },
                            "$inc": {"fix_success_count": 1}
                        }
                    )
                    fixed_count += 1
                    break  # One fix example is enough
    
    # Recalculate success rates
    cursor = db.error_signatures.find({})
    async for error_sig in cursor:
        occurrences = error_sig.get("occurrence_count", 1)
        successes = error_sig.get("fix_success_count", 0)
        rate = successes / occurrences if occurrences > 0 else 0
        
        await db.error_signatures.update_one(
            {"id": error_sig["id"]},
            {"$set": {"success_rate": rate}}
        )
    
    print(f"[Aggregator] Found {fixed_count} fix patterns")
    return fixed_count


# =============================================================================
# CLEANUP JOBS
# =============================================================================

async def cleanup_old_events(days_to_keep: int = 90):
    """Remove old events to save storage"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_to_keep)).isoformat()
    
    result = await db.project_events.delete_many({
        "created_at": {"$lt": cutoff}
    })
    
    print(f"[Cleanup] Deleted {result.deleted_count} old events")
    return result.deleted_count


async def cleanup_old_patterns(days_to_keep: int = 90, min_score: float = 0.3):
    """Remove low-performing old patterns"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_to_keep)).isoformat()
    
    result = await db.pattern_library.delete_many({
        "updated_at": {"$lt": cutoff},
        "success_score": {"$lt": min_score}
    })
    
    print(f"[Cleanup] Deleted {result.deleted_count} low-performing patterns")
    return result.deleted_count


# =============================================================================
# MAIN AGGREGATOR RUNNER
# =============================================================================

async def run_hourly_jobs():
    """Run all hourly aggregation jobs"""
    print(f"\n{'='*50}")
    print(f"[Aggregator] Starting HOURLY jobs at {datetime.now(timezone.utc)}")
    print(f"{'='*50}\n")
    
    await calculate_pattern_scores()
    
    print("\n[Aggregator] Hourly jobs completed!\n")


async def run_nightly_jobs():
    """Run all nightly aggregation jobs"""
    print(f"\n{'='*50}")
    print(f"[Aggregator] Starting NIGHTLY jobs at {datetime.now(timezone.utc)}")
    print(f"{'='*50}\n")
    
    await extract_winning_patterns()
    await aggregate_user_preferences()
    await build_autofix_library()
    await cleanup_old_events()
    await cleanup_old_patterns()
    
    print("\n[Aggregator] Nightly jobs completed!\n")


# =============================================================================
# SCHEDULER (using asyncio for simplicity)
# =============================================================================

# Global task reference
_scheduler_task = None

async def start_aggregator_scheduler():
    """
    Start the background scheduler.
    In production, use APScheduler or Celery Beat.
    """
    global _scheduler_task
    
    print("[Scheduler] Starting learning aggregator scheduler...")
    
    async def scheduler_loop():
        last_hourly = datetime.now(timezone.utc)
        last_nightly = datetime.now(timezone.utc)
        
        while True:
            try:
                now = datetime.now(timezone.utc)
                
                # Run hourly jobs
                if (now - last_hourly).seconds >= 3600:
                    try:
                        await run_hourly_jobs()
                    except Exception as e:
                        print(f"[Scheduler] Hourly job failed: {e}")
                    last_hourly = now
                
                # Run nightly jobs at 2 AM UTC
                if now.hour == 2 and (now - last_nightly).days >= 1:
                    try:
                        await run_nightly_jobs()
                    except Exception as e:
                        print(f"[Scheduler] Nightly job failed: {e}")
                    last_nightly = now
                
                # Sleep for 5 minutes
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                print("[Scheduler] Scheduler stopped")
                break
            except Exception as e:
                print(f"[Scheduler] Error in scheduler loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    _scheduler_task = asyncio.create_task(scheduler_loop())
    print("[Scheduler] Aggregator scheduler started successfully!")


async def stop_aggregator_scheduler():
    """Stop the background scheduler"""
    global _scheduler_task
    
    if _scheduler_task:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None
        print("[Scheduler] Aggregator scheduler stopped")


# Alias for backward compatibility
start_scheduler = start_aggregator_scheduler


# Manual trigger functions for testing
async def trigger_hourly():
    """Manually trigger hourly jobs"""
    await run_hourly_jobs()


async def trigger_nightly():
    """Manually trigger nightly jobs"""
    await run_nightly_jobs()
