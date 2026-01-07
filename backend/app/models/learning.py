"""
Learning Models - Self-Learning System for Nirman.tech
Enables personalization + global pattern learning
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# =============================================================================
# EVENT TYPES
# =============================================================================

class EventType(str, Enum):
    """All trackable events in the system"""
    # Project lifecycle
    PROJECT_CREATED = "project_created"
    PROMPT_SUBMITTED = "prompt_submitted"
    
    # Planning
    PLAN_GENERATED = "plan_generated"
    PLAN_APPROVED = "plan_approved"
    PLAN_REJECTED = "plan_rejected"
    PLAN_MODIFIED = "plan_modified"
    
    # Building
    BUILD_STARTED = "build_started"
    BUILD_SUCCEEDED = "build_succeeded"
    BUILD_FAILED = "build_failed"
    
    # Sections
    SECTION_ADDED = "section_added"
    SECTION_REMOVED = "section_removed"
    SECTION_REGENERATED = "section_regenerated"
    SECTION_REORDERED = "section_reordered"
    
    # Theme/Style
    THEME_CHANGED = "theme_changed"
    LAYOUT_CHANGED = "layout_changed"
    
    # Deployment
    DEPLOY_STARTED = "deploy_started"
    DEPLOY_SUCCEEDED = "deploy_succeeded"
    DEPLOY_FAILED = "deploy_failed"
    
    # User feedback
    FEEDBACK_POSITIVE = "feedback_positive"
    FEEDBACK_NEGATIVE = "feedback_negative"


# =============================================================================
# (i) PROJECT EVENTS - Most Important Table
# =============================================================================

class ProjectEvent(BaseModel):
    """
    Logs every user action for learning.
    Collection: project_events
    """
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    user_id: str
    project_id: str
    event_type: EventType
    payload: Dict[str, Any] = {}  # Structured data (PII-safe)
    metadata: Dict[str, Any] = {}  # Extra context
    created_at: str


class ProjectEventCreate(BaseModel):
    """Request to create a project event"""
    project_id: str
    event_type: EventType
    payload: Dict[str, Any] = {}


# =============================================================================
# (ii) SPEC VERSIONS - Track spec evolution
# =============================================================================

class SpecVersion(BaseModel):
    """
    Version history of project specs.
    Collection: spec_versions
    """
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    project_id: str
    user_id: str
    version: int  # 1, 2, 3...
    spec_json: Dict[str, Any]  # The full spec
    diff_summary: Optional[str] = None  # What changed
    source: str = "planner"  # planner, user_edit, regenerate
    created_at: str


# =============================================================================
# (iii) AI RUNS - Already exists, extend if needed
# =============================================================================

class AIRunStep(str, Enum):
    """Steps in AI pipeline"""
    PLANNER = "planner"
    BUILDER = "builder"
    FIXER = "fixer"
    REGENERATE = "regenerate"


# =============================================================================
# (iv) USER PREFERENCES - Personalization
# =============================================================================

class ThemePreference(BaseModel):
    """User's preferred theme settings"""
    primary_color: Optional[str] = None  # "#4F46E5"
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_style: Optional[str] = None  # "light", "dark", "gradient"
    font_family: Optional[str] = None  # "Inter", "Poppins"
    border_radius: Optional[str] = None  # "rounded", "sharp", "pill"


class UserPreferences(BaseModel):
    """
    Per-user personalization settings.
    Collection: user_preferences
    """
    model_config = ConfigDict(populate_by_name=True)
    
    user_id: str
    
    # Theme preferences
    preferred_theme: ThemePreference = ThemePreference()
    
    # Style preferences
    preferred_tone: str = "modern"  # modern, minimal, bold, playful, corporate
    preferred_density: str = "comfortable"  # compact, comfortable, spacious
    
    # Section preferences (most used sections)
    preferred_sections: List[str] = []  # ["hero", "features", "pricing", "testimonials"]
    section_weights: Dict[str, float] = {}  # {"hero": 0.95, "features": 0.8}
    
    # Layout preferences
    preferred_layouts: List[str] = []  # ["single-page", "multi-section", "dashboard"]
    
    # Industry/category affinity
    industry_affinity: Dict[str, float] = {}  # {"saas": 0.7, "ecommerce": 0.3}
    
    # Privacy settings
    personalization_enabled: bool = True
    global_learning_enabled: bool = False  # Opt-in for global improvements
    
    # Timestamps
    created_at: str
    last_updated: str


class UserPreferencesUpdate(BaseModel):
    """Request to update user preferences"""
    preferred_theme: Optional[ThemePreference] = None
    preferred_tone: Optional[str] = None
    preferred_density: Optional[str] = None
    preferred_sections: Optional[List[str]] = None
    preferred_layouts: Optional[List[str]] = None
    personalization_enabled: Optional[bool] = None
    global_learning_enabled: Optional[bool] = None


# =============================================================================
# (v) PATTERN LIBRARY - Global Best Patterns
# =============================================================================

class PatternCategory(str, Enum):
    """Categories for patterns"""
    HERO = "hero"
    FEATURES = "features"
    PRICING = "pricing"
    TESTIMONIALS = "testimonials"
    CTA = "cta"
    NAVBAR = "navbar"
    FOOTER = "footer"
    CONTACT = "contact"
    GALLERY = "gallery"
    TEAM = "team"
    FAQ = "faq"
    STATS = "stats"


class PatternLibrary(BaseModel):
    """
    Global winning patterns learned from successful projects.
    Collection: pattern_library
    """
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    
    # Categorization
    category: PatternCategory  # hero, features, pricing...
    industry: str  # saas, ecommerce, food_delivery, gym, portfolio
    
    # The pattern itself
    pattern_name: str  # "Modern SaaS Hero with Gradient"
    spec_snippet: Dict[str, Any]  # Winning spec fragment
    
    # Success metrics
    success_score: float = 0.0  # 0-1, computed from approvals/deploys
    approval_count: int = 0
    deploy_count: int = 0
    regenerate_count: int = 0  # Lower is better
    total_uses: int = 0
    
    # Metadata
    tags: List[str] = []  # ["gradient", "animated", "dark-mode"]
    example_project_ids: List[str] = []  # Anonymized references
    
    # Timestamps
    created_at: str
    updated_at: str


class PatternLibraryCreate(BaseModel):
    """Request to add a pattern"""
    category: PatternCategory
    industry: str
    pattern_name: str
    spec_snippet: Dict[str, Any]
    tags: List[str] = []


# =============================================================================
# (vi) ERROR SIGNATURES - Auto-Fix Learning
# =============================================================================

class ErrorSignature(BaseModel):
    """
    Known error patterns and their fixes.
    Collection: error_signatures
    """
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    
    # Error identification
    signature_hash: str  # MD5/SHA of normalized error text
    error_pattern: str  # Short description "Missing closing div"
    error_category: str  # "syntax", "runtime", "build", "deploy"
    
    # Error details
    error_sample: str  # Truncated example error text
    trigger_context: Optional[str] = None  # What usually causes this
    
    # Fix information
    fix_type: str  # "auto", "manual", "prompt_refinement"
    fix_patch: Optional[str] = None  # Diff or code fix
    fix_instructions: Optional[str] = None  # Human-readable fix
    fix_prompt: Optional[str] = None  # Prompt to send to AI fixer
    
    # Success metrics
    occurrence_count: int = 0
    fix_success_count: int = 0
    success_rate: float = 0.0  # fix_success_count / occurrence_count
    
    # Timestamps
    first_seen: str
    last_seen: str
    updated_at: str


class ErrorSignatureCreate(BaseModel):
    """Request to add/update error signature"""
    error_pattern: str
    error_category: str
    error_sample: str
    fix_type: str
    fix_patch: Optional[str] = None
    fix_instructions: Optional[str] = None


# =============================================================================
# AGGREGATED INSIGHTS (for dashboards/analytics)
# =============================================================================

class IndustryInsights(BaseModel):
    """Aggregated insights per industry"""
    industry: str
    total_projects: int = 0
    approval_rate: float = 0.0  # Plans approved without modification
    deploy_rate: float = 0.0  # Projects that got deployed
    avg_regenerations: float = 0.0  # Avg section regenerations
    top_sections: List[str] = []  # Most used sections
    top_patterns: List[str] = []  # Best performing pattern IDs


class UserInsights(BaseModel):
    """Per-user learning insights"""
    user_id: str
    total_projects: int = 0
    preferred_industry: Optional[str] = None
    style_consistency: float = 0.0  # How consistent their choices are
    top_sections: List[str] = []
    avg_satisfaction: float = 0.0  # Based on feedback events


# =============================================================================
# LEARNING CONFIG
# =============================================================================

class LearningConfig(BaseModel):
    """System-wide learning configuration"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = "global_config"
    
    # Feature flags
    personalization_default: bool = True
    global_learning_default: bool = False
    
    # Aggregation settings
    aggregation_interval_hours: int = 24
    min_samples_for_pattern: int = 10
    pattern_success_threshold: float = 0.7
    
    # Privacy settings
    anonymize_patterns: bool = True
    max_pattern_age_days: int = 90
    
    updated_at: str
