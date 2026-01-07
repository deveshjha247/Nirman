"""
Nirman.tech Planner Agent
Converts user prompts into structured JSON specifications for full-stack app generation.
Includes self-learning integration for personalization and pattern matching.
"""

import json
import re
from typing import Optional, Dict, Any, List

# =============================================================================
# PLANNER SYSTEM PROMPT (BASE)
# =============================================================================

PLANNER_SYSTEM_PROMPT = """You are Nirman.tech Planner Agent.

Goal: Convert the user's request into a STRICT JSON specification for generating a full-stack product (React frontend + FastAPI backend). 
Do NOT write code. Do NOT include explanations. Output JSON ONLY.

Hard rules:
- Output must be valid JSON (no trailing commas, no markdown).
- Use only the allowed keys in the schema below.
- If user requirements are missing, make reasonable assumptions and reflect them in "assumptions".
- Keep scope MVP-friendly: prefer template-based pages/modules.
- Include both "website" and "webapp" if user asks for both; otherwise only what they need.
- Always include authentication if the app has private dashboards.
- Always include CRUD modules if the app requires data management.
- Security: include CORS origins as placeholders and never include secrets.

JSON schema (allowed top-level keys):
{
  "project": { "name": string, "type": "website"|"webapp"|"both", "industry": string },
  "assumptions": string[],
  "theme": { "primary": string, "secondary": string, "font": string, "tone": "modern"|"minimal"|"bold" },
  "website": {
    "pages": [
      { "route": string, "title": string, "sections": string[] }
    ]
  },
  "webapp": {
    "auth": { "enabled": boolean, "method": "email_password"|"magic_link", "roles": string[] },
    "data_models": [
      { "name": string, "fields": [ { "name": string, "type": "string"|"number"|"boolean"|"date"|"datetime"|"text"|"enum", "required": boolean, "enum_values": string[] } ] }
    ],
    "modules": [
      { "name": string, "model": string, "crud": boolean, "pages": string[] }
    ],
    "routes": string[]
  },
  "api": {
    "base_path": "/api",
    "resources": [
      { "name": string, "model": string, "endpoints": string[] }
    ]
  },
  "deployment": { "subdomain": string, "env_vars": string[] }
}

Now, generate the JSON spec for the user's request."""


# =============================================================================
# LEARNING-ENHANCED SYSTEM PROMPT ADDON
# =============================================================================

LEARNING_ADDON_PROMPT = """
PERSONALIZATION CONTEXT:
You may receive additional context to improve output quality:

1. user_preferences: User's preferred theme, tone, sections, and layouts based on their history
2. pattern_snippets: Proven spec fragments from successful similar projects

Rules for using learning context:
- Always output strict JSON spec only.
- Prefer applying user_preferences unless it conflicts with user's current prompt.
- Use pattern_snippets only as guidance for structure; adapt content to user's specific needs.
- If user_preferences.theme is provided, use those colors/fonts unless user explicitly requests different ones.
- If user_preferences.sections is provided, include their frequently-used sections when appropriate.
- If pattern_snippets contains a relevant section, use its structure as a template.

Example of how to apply preferences:
- If user prefers "minimal" tone, reduce visual complexity
- If user frequently uses "testimonials" section, include it by default
- If pattern_snippet shows a successful hero section structure, use similar fields
"""


# =============================================================================
# RENDERER/BUILDER SYSTEM PROMPT
# =============================================================================

RENDERER_SYSTEM_PROMPT = """You are Nirman.tech Builder Agent.

Goal: Generate production-ready code based on the JSON specification provided.

You will receive a JSON spec and must generate a complete, working application.

Hard rules:
1. Generate ONLY valid HTML/CSS/JS code (no explanations, no markdown code blocks).
2. Use Tailwind CSS for styling (include CDN script tag).
3. Make the design modern, responsive, and professional.
4. Include all sections and pages specified in the JSON.
5. Use semantic HTML5 elements.
6. Include smooth animations and transitions.
7. Ensure mobile-first responsive design.
8. Include proper meta tags and SEO basics.
9. Use Inter or the specified font from Google Fonts.
10. Include placeholder images from https://placehold.co/ or Unsplash.

For websites:
- Generate a single-page HTML with all sections
- Include navigation that scrolls to sections
- Add contact forms with basic validation
- Include footer with links

For webapps:
- Generate the main dashboard HTML
- Include sidebar navigation
- Add placeholder for data tables/cards
- Include modals for CRUD operations

Color scheme from theme:
- Use primary color for CTAs and highlights
- Use secondary for accents
- Maintain good contrast ratios

Output format: Pure HTML code starting with <!DOCTYPE html>"""


# =============================================================================
# RENDERER LEARNING ADDON
# =============================================================================

RENDERER_LEARNING_ADDON = """
PERSONALIZATION CONTEXT:
Apply the following user preferences and patterns to improve output:

1. user_preferences: Contains theme colors, font, tone, density, and layout preferences
2. pattern_snippets: Proven code patterns from successful projects

Rules:
- Apply user_preferences.theme colors to the design
- Match user_preferences.tone (modern/minimal/bold) in the visual style
- If user_preferences.density is "compact", reduce spacing; if "spacious", increase whitespace
- Use pattern_snippets as structural templates but adapt content to the spec
- Maintain consistency with user's previous successful projects
"""


# =============================================================================
# PLANNER FUNCTIONS
# =============================================================================

def extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from AI response, handling various formats."""
    # Try direct JSON parse first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
        r'\{[\s\S]*\}'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response)
        for match in matches:
            try:
                # Clean the match
                cleaned = match.strip()
                if not cleaned.startswith('{'):
                    continue
                return json.loads(cleaned)
            except json.JSONDecodeError:
                continue
    
    return None


def validate_spec(spec: Dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate the generated spec against required schema."""
    errors = []
    
    # Required top-level keys
    if "project" not in spec:
        errors.append("Missing 'project' key")
    else:
        if "name" not in spec["project"]:
            errors.append("Missing 'project.name'")
        if "type" not in spec["project"]:
            errors.append("Missing 'project.type'")
        elif spec["project"]["type"] not in ["website", "webapp", "both"]:
            errors.append("Invalid 'project.type' - must be website, webapp, or both")
    
    if "theme" not in spec:
        errors.append("Missing 'theme' key")
    
    # Validate website if present
    if spec.get("project", {}).get("type") in ["website", "both"]:
        if "website" not in spec:
            errors.append("Missing 'website' key for website/both type")
        elif "pages" not in spec.get("website", {}):
            errors.append("Missing 'website.pages'")
    
    # Validate webapp if present
    if spec.get("project", {}).get("type") in ["webapp", "both"]:
        if "webapp" not in spec:
            errors.append("Missing 'webapp' key for webapp/both type")
    
    return len(errors) == 0, errors


def create_default_spec(prompt: str) -> Dict[str, Any]:
    """Create a default spec when AI fails."""
    # Extract potential name from prompt
    words = prompt.split()[:3]
    name = " ".join(words).title() if words else "My Project"
    
    # Determine type based on keywords
    prompt_lower = prompt.lower()
    if any(word in prompt_lower for word in ["dashboard", "admin", "app", "crud", "login"]):
        project_type = "webapp"
    elif any(word in prompt_lower for word in ["landing", "website", "portfolio", "blog"]):
        project_type = "website"
    else:
        project_type = "website"
    
    spec = {
        "project": {
            "name": name,
            "type": project_type,
            "industry": "general"
        },
        "assumptions": [
            "Modern, responsive design required",
            "Single page application",
            "Contact form included"
        ],
        "theme": {
            "primary": "#6366f1",
            "secondary": "#8b5cf6",
            "font": "Inter",
            "tone": "modern"
        }
    }
    
    if project_type in ["website", "both"]:
        spec["website"] = {
            "pages": [
                {
                    "route": "/",
                    "title": "Home",
                    "sections": ["hero", "features", "testimonials", "cta", "footer"]
                }
            ]
        }
    
    if project_type in ["webapp", "both"]:
        spec["webapp"] = {
            "auth": {
                "enabled": True,
                "method": "email_password",
                "roles": ["user", "admin"]
            },
            "data_models": [],
            "modules": [],
            "routes": ["/dashboard", "/settings"]
        }
    
    spec["deployment"] = {
        "subdomain": name.lower().replace(" ", "-"),
        "env_vars": ["DATABASE_URL", "JWT_SECRET"]
    }
    
    return spec


def generate_build_prompt(spec: Dict[str, Any]) -> str:
    """Generate the prompt for the renderer/builder agent."""
    spec_json = json.dumps(spec, indent=2)
    
    prompt = f"""Based on the following JSON specification, generate a complete, production-ready HTML page:

```json
{spec_json}
```

Requirements:
1. Create a modern, responsive {spec['project']['type']} for {spec['project'].get('industry', 'general')} industry
2. Use the theme colors: primary={spec['theme']['primary']}, secondary={spec['theme']['secondary']}
3. Font: {spec['theme']['font']}, Tone: {spec['theme']['tone']}
"""

    if "website" in spec:
        pages = spec["website"].get("pages", [])
        if pages:
            sections = pages[0].get("sections", [])
            prompt += f"\n4. Include these sections: {', '.join(sections)}"
    
    if "webapp" in spec:
        prompt += "\n5. Include a dashboard layout with sidebar navigation"
        if spec["webapp"].get("auth", {}).get("enabled"):
            prompt += "\n6. Include login/auth UI components"
    
    prompt += "\n\nGenerate the complete HTML code now:"
    
    return prompt


# =============================================================================
# INDUSTRY-SPECIFIC TEMPLATES
# =============================================================================

INDUSTRY_TEMPLATES = {
    "food_delivery": {
        "sections": ["hero_search", "categories", "popular_restaurants", "how_it_works", "app_download", "footer"],
        "features": ["restaurant_listing", "menu_display", "cart", "order_tracking"],
        "colors": {"primary": "#ef4444", "secondary": "#f97316"}
    },
    "ecommerce": {
        "sections": ["hero_banner", "categories", "featured_products", "deals", "testimonials", "footer"],
        "features": ["product_catalog", "cart", "wishlist", "checkout"],
        "colors": {"primary": "#3b82f6", "secondary": "#8b5cf6"}
    },
    "saas": {
        "sections": ["hero", "features", "pricing", "testimonials", "faq", "cta", "footer"],
        "features": ["dashboard", "analytics", "settings", "billing"],
        "colors": {"primary": "#6366f1", "secondary": "#8b5cf6"}
    },
    "portfolio": {
        "sections": ["hero", "about", "skills", "projects", "contact", "footer"],
        "features": ["project_gallery", "contact_form"],
        "colors": {"primary": "#1f2937", "secondary": "#6b7280"}
    },
    "healthcare": {
        "sections": ["hero", "services", "doctors", "appointments", "testimonials", "footer"],
        "features": ["appointment_booking", "doctor_profiles", "patient_portal"],
        "colors": {"primary": "#0ea5e9", "secondary": "#06b6d4"}
    },
    "education": {
        "sections": ["hero", "courses", "instructors", "testimonials", "pricing", "footer"],
        "features": ["course_catalog", "enrollment", "progress_tracking"],
        "colors": {"primary": "#8b5cf6", "secondary": "#a855f7"}
    },
    "real_estate": {
        "sections": ["hero_search", "featured_properties", "services", "agents", "testimonials", "footer"],
        "features": ["property_listing", "search_filters", "agent_contact"],
        "colors": {"primary": "#059669", "secondary": "#10b981"}
    }
}


def detect_industry(prompt: str) -> str:
    """Detect industry from user prompt."""
    prompt_lower = prompt.lower()
    
    industry_keywords = {
        "food_delivery": ["food", "delivery", "restaurant", "order food", "meal", "cuisine", "zomato", "swiggy"],
        "ecommerce": ["shop", "store", "ecommerce", "products", "sell", "buy", "amazon", "shopping"],
        "saas": ["saas", "software", "platform", "subscription", "dashboard", "analytics", "b2b"],
        "portfolio": ["portfolio", "personal", "resume", "cv", "freelancer", "designer", "developer"],
        "healthcare": ["health", "medical", "doctor", "hospital", "clinic", "patient", "appointment"],
        "education": ["course", "learn", "education", "school", "university", "training", "tutorial"],
        "real_estate": ["property", "real estate", "house", "apartment", "rent", "buy home", "listing"]
    }
    
    for industry, keywords in industry_keywords.items():
        if any(keyword in prompt_lower for keyword in keywords):
            return industry
    
    return "general"


def enhance_spec_with_industry(spec: Dict[str, Any], industry: str) -> Dict[str, Any]:
    """Enhance spec with industry-specific templates."""
    if industry in INDUSTRY_TEMPLATES:
        template = INDUSTRY_TEMPLATES[industry]
        
        # Update theme colors if not specified
        if spec.get("theme", {}).get("primary") == "#6366f1":  # Default color
            spec["theme"]["primary"] = template["colors"]["primary"]
            spec["theme"]["secondary"] = template["colors"]["secondary"]
        
        # Enhance website sections
        if "website" in spec and spec["website"].get("pages"):
            spec["website"]["pages"][0]["sections"] = template["sections"]
        
        # Add industry to project
        spec["project"]["industry"] = industry
    
    return spec


# =============================================================================
# LEARNING-ENHANCED PROMPT BUILDERS
# =============================================================================

def build_planner_prompt_with_learning(
    user_prompt: str,
    learning_context: Dict[str, Any] = None
) -> str:
    """
    Build the complete planner prompt with learning context injected.
    This is where personalization happens.
    """
    base_prompt = PLANNER_SYSTEM_PROMPT
    
    if learning_context:
        # Add learning addon
        base_prompt += "\n\n" + LEARNING_ADDON_PROMPT
        
        # Add user preferences if available
        if learning_context.get("user_preferences"):
            prefs = learning_context["user_preferences"]
            base_prompt += f"\n\nUSER PREFERENCES:\n```json\n{json.dumps(prefs, indent=2)}\n```"
        
        # Add pattern snippets if available
        if learning_context.get("pattern_snippets"):
            patterns = learning_context["pattern_snippets"]
            base_prompt += f"\n\nPATTERN SNIPPETS (proven successful patterns):\n```json\n{json.dumps(patterns, indent=2)}\n```"
    
    # Add the user's actual request
    base_prompt += f"\n\nUSER REQUEST:\n{user_prompt}\n\nGenerate the JSON spec now:"
    
    return base_prompt


def build_renderer_prompt_with_learning(
    spec: Dict[str, Any],
    learning_context: Dict[str, Any] = None
) -> str:
    """
    Build the renderer/builder prompt with learning context.
    Applies user preferences to code generation.
    """
    spec_json = json.dumps(spec, indent=2)
    
    base_prompt = RENDERER_SYSTEM_PROMPT
    
    if learning_context:
        # Add learning addon
        base_prompt += "\n\n" + RENDERER_LEARNING_ADDON
        
        # Add user preferences
        if learning_context.get("user_preferences"):
            prefs = learning_context["user_preferences"]
            base_prompt += f"\n\nUSER PREFERENCES:\n```json\n{json.dumps(prefs, indent=2)}\n```"
        
        # Add pattern snippets
        if learning_context.get("pattern_snippets"):
            patterns = learning_context["pattern_snippets"]
            base_prompt += f"\n\nPATTERN SNIPPETS:\n```json\n{json.dumps(patterns, indent=2)}\n```"
    
    # Add the spec
    base_prompt += f"\n\nJSON SPECIFICATION:\n```json\n{spec_json}\n```"
    
    # Add generation instructions
    base_prompt += f"""

REQUIREMENTS:
1. Create a modern, responsive {spec['project']['type']} for {spec['project'].get('industry', 'general')} industry
2. Use theme colors: primary={spec['theme']['primary']}, secondary={spec['theme']['secondary']}
3. Font: {spec['theme']['font']}, Tone: {spec['theme']['tone']}
"""

    if "website" in spec:
        pages = spec["website"].get("pages", [])
        if pages:
            sections = pages[0].get("sections", [])
            base_prompt += f"\n4. Include these sections: {', '.join(sections)}"
    
    if "webapp" in spec:
        base_prompt += "\n5. Include a dashboard layout with sidebar navigation"
        if spec["webapp"].get("auth", {}).get("enabled"):
            base_prompt += "\n6. Include login/auth UI components"
    
    base_prompt += "\n\nGenerate the complete HTML code now:"
    
    return base_prompt


def apply_preferences_to_spec(
    spec: Dict[str, Any],
    user_preferences: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply user preferences to enhance the spec.
    Called after AI generates spec but before rendering.
    """
    if not user_preferences:
        return spec
    
    # Apply theme preferences if user hasn't specified different ones
    theme_prefs = user_preferences.get("theme", {})
    if theme_prefs:
        if not spec.get("theme"):
            spec["theme"] = {}
        
        # Only apply if spec has default values
        if spec["theme"].get("primary") in ["#6366f1", None]:
            if theme_prefs.get("primary_color"):
                spec["theme"]["primary"] = theme_prefs["primary_color"]
        
        if spec["theme"].get("secondary") in ["#8b5cf6", None]:
            if theme_prefs.get("secondary_color"):
                spec["theme"]["secondary"] = theme_prefs["secondary_color"]
        
        if not spec["theme"].get("font") and theme_prefs.get("font_family"):
            spec["theme"]["font"] = theme_prefs["font_family"]
    
    # Apply tone preference
    if user_preferences.get("tone") and not spec.get("theme", {}).get("tone"):
        spec.setdefault("theme", {})["tone"] = user_preferences["tone"]
    
    # Add frequently used sections if not already specified
    if "website" in spec and spec["website"].get("pages"):
        current_sections = spec["website"]["pages"][0].get("sections", [])
        preferred_sections = user_preferences.get("sections", [])
        
        # Add up to 2 preferred sections that aren't already included
        for section in preferred_sections[:3]:
            if section not in current_sections and len(current_sections) < 8:
                # Insert before footer if present
                if "footer" in current_sections:
                    idx = current_sections.index("footer")
                    current_sections.insert(idx, section)
                else:
                    current_sections.append(section)
        
        spec["website"]["pages"][0]["sections"] = current_sections
    
    return spec


def merge_pattern_into_spec(
    spec: Dict[str, Any],
    pattern_snippets: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Merge winning patterns into the spec.
    Uses pattern structure while keeping user's content.
    """
    if not pattern_snippets:
        return spec
    
    # For website specs, enhance sections with patterns
    if "website" in spec and spec["website"].get("pages"):
        for page in spec["website"]["pages"]:
            enhanced_sections = []
            
            for section_name in page.get("sections", []):
                if section_name in pattern_snippets:
                    # Use pattern structure
                    pattern = pattern_snippets[section_name]
                    enhanced_section = {
                        "type": section_name,
                        "template": pattern.get("template", "default"),
                        "config": pattern.get("config", {})
                    }
                    enhanced_sections.append(enhanced_section)
                else:
                    enhanced_sections.append(section_name)
            
            page["sections"] = enhanced_sections
    
    return spec

