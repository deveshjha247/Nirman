import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

# App Version
APP_VERSION = "1.0.0"
APP_NAME = "Nirman"

# MongoDB
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# JWT
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# AI Keys - Direct Provider Keys
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')
GROK_API_KEY = os.environ.get('GROK_API_KEY', '')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY', '')
COHERE_API_KEY = os.environ.get('COHERE_API_KEY', '')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
TOGETHER_API_KEY = os.environ.get('TOGETHER_API_KEY', '')
PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY', '')
FIREWORKS_API_KEY = os.environ.get('FIREWORKS_API_KEY', '')
AI21_API_KEY = os.environ.get('AI21_API_KEY', '')
QWEN_API_KEY = os.environ.get('QWEN_API_KEY', '')
MOONSHOT_API_KEY = os.environ.get('MOONSHOT_API_KEY', '')
YI_API_KEY = os.environ.get('YI_API_KEY', '')
ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '')
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', '')
DEFAULT_AI_PROVIDER = os.environ.get('DEFAULT_AI_PROVIDER', 'openai')

# Cashfree
CASHFREE_APP_ID = os.environ.get('CASHFREE_APP_ID', '')
CASHFREE_SECRET_KEY = os.environ.get('CASHFREE_SECRET_KEY', '')
CASHFREE_ENV = os.environ.get('CASHFREE_ENV', 'sandbox')

# GitHub Integration
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', '')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', '')

# Vercel Integration
VERCEL_CLIENT_ID = os.environ.get('VERCEL_CLIENT_ID', '')
VERCEL_CLIENT_SECRET = os.environ.get('VERCEL_CLIENT_SECRET', '')

# Canva Integration
CANVA_CLIENT_ID = os.environ.get('CANVA_CLIENT_ID', '')
CANVA_CLIENT_SECRET = os.environ.get('CANVA_CLIENT_SECRET', '')

# Razorpay Integration (App-level for platform payments)
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

# MongoDB Atlas (for app-level connection monitoring)
MONGODB_ATLAS_PUBLIC_KEY = os.environ.get('MONGODB_ATLAS_PUBLIC_KEY', '')
MONGODB_ATLAS_PRIVATE_KEY = os.environ.get('MONGODB_ATLAS_PRIVATE_KEY', '')

# Plans Configuration
PLANS = {
    "free": {
        "id": "free",
        "name": "Free",
        "price_monthly": 0,
        "price_yearly": 0,
        "features": [
            "5 Projects",
            "100 AI Generations/month",
            "Basic Templates",
            "Community Support"
        ],
        "limits": {
            "projects": 5,
            "generations_per_month": 100
        }
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price_monthly": 999,
        "price_yearly": 9999,
        "features": [
            "Unlimited Projects",
            "1000 AI Generations/month",
            "All Templates",
            "Priority Support",
            "Export to GitHub",
            "Custom Domains"
        ],
        "limits": {
            "projects": -1,
            "generations_per_month": 1000
        }
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "price_monthly": 4999,
        "price_yearly": 49999,
        "features": [
            "Unlimited Everything",
            "Unlimited AI Generations",
            "White Label",
            "Dedicated Support",
            "API Access",
            "Team Collaboration",
            "Custom Integrations"
        ],
        "limits": {
            "projects": -1,
            "generations_per_month": -1
        }
    }
}
