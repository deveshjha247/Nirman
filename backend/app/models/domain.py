from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class Subdomain(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    subdomain: str  # project-name
    project_id: str
    user_id: str
    is_active: bool = True
    created_at: str

class CustomDomain(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    domain: str
    project_id: str
    user_id: str
    verification_status: str = "pending"  # pending, verified, failed
    ssl_status: str = "pending"  # pending, active, expired
    dns_records: List[dict] = []
    created_at: str
    verified_at: Optional[str] = None

# Reserved subdomains that cannot be used
RESERVED_SUBDOMAINS = [
    "www", "app", "admin", "api", "docs", "support", "help",
    "blog", "mail", "email", "ftp", "cdn", "static", "assets",
    "login", "register", "signup", "signin", "dashboard", "panel",
    "nirman", "test", "dev", "staging", "prod", "production"
]

# Blocked words for abuse prevention
BLOCKED_WORDS = [
    "porn", "xxx", "sex", "nude", "hack", "crack", "warez",
    "phishing", "scam", "fraud", "illegal", "drugs"
]
