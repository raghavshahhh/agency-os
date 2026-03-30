"""
RAGSPRO Command Center - Configuration Module
Reads API keys from external files - NEVER hardcoded
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = BASE_DIR / "data"
CONTENT_DIR = DATA_DIR / "content"
PROPOSALS_DIR = DATA_DIR / "proposals"

# Create directories
for d in [DATA_DIR, CONTENT_DIR, PROPOSALS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Load local .env if exists
local_env = BASE_DIR / ".env"
if local_env.exists():
    load_dotenv(local_env)

# ============ READ API KEYS FROM EXTERNAL FILES ============

# NVIDIA NIM API Key from ~/free-claude-code/.env
NVIDIA_FREE_CLAUDE_ENV = Path.home() / "free-claude-code" / ".env"
def _load_nvidia_key():
    """Read NVIDIA API key from free-claude-code .env file"""
    if NVIDIA_FREE_CLAUDE_ENV.exists():
        with open(NVIDIA_FREE_CLAUDE_ENV, 'r') as f:
            for line in f:
                if line.startswith('NVIDIA_NIM_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"')
    return None

NVIDIA_API_KEY = _load_nvidia_key() or os.getenv("NVIDIA_API_KEY", "")
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "qwen/qwen2.5-7b-instruct"  # Use smaller model for speed

# Telegram Bot Token
def _load_telegram_token():
    """Read Telegram token from environment or config files"""
    # First check environment
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if token:
        return token
    # Check openclaw workspace
    openclaw_env = Path.home() / ".openclaw" / "workspace-ragspro" / ".env"
    if openclaw_env.exists():
        with open(openclaw_env, 'r') as f:
            for line in f:
                if line.startswith('TELEGRAM_BOT_TOKEN='):
                    return line.split('=', 1)[1].strip().strip('"')
    return ""

TELEGRAM_BOT_TOKEN = _load_telegram_token()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Gmail Credentials (from openclaw workspace)
def _load_gmail_creds():
    """Read Gmail credentials from openclaw workspace"""
    openclaw_env = Path.home() / ".openclaw" / "workspace-ragspro" / ".env"
    creds = {"user": "", "password": ""}
    if openclaw_env.exists():
        with open(openclaw_env, 'r') as f:
            for line in f:
                if line.startswith('GMAIL_USER='):
                    creds["user"] = line.split('=', 1)[1].strip().strip('"')
                elif line.startswith('GMAIL_APP_PASSWORD='):
                    creds["password"] = line.split('=', 1)[1].strip().strip('"')
    return creds

_gmail_creds = _load_gmail_creds()
GMAIL_USER = _gmail_creds["user"] or os.getenv("GMAIL_USER", "ragsproai@gmail.com")
GMAIL_APP_PASSWORD = _gmail_creds["password"] or os.getenv("GMAIL_APP_PASSWORD", "")

# Search APIs
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# n8n
N8N_API_KEY = os.getenv("N8N_API_KEY", "")
N8N_URL = os.getenv("N8N_URL", "http://localhost:5678")

# Resend
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

# ============ AGENCY INFO ============

AGENCY_NAME = "RAGSPRO"
AGENCY_URL = "https://ragspro.com"
AGENCY_TAGLINE = "AI Chatbots, SaaS & Automation Solutions"
CALENDLY_URL = "https://calendly.com/ragspro/discovery"
SERVICES = ["AI Chatbots", "SaaS Development", "Automation", "Next.js", "Python"]
PRICE_RANGE = "₹15,000 - ₹1,00,000"

SOCIAL_LINKS = {
    "linkedin": "https://linkedin.com/company/ragspro",
    "twitter": "https://twitter.com/ragspro",
    "instagram": "https://instagram.com/ragspro",
    "github": "https://github.com/ragspro"
}

# ============ LINKEDIN WEEKLY ROTATION ============
LINKEDIN_TOPICS = {
    0: "What I built this week - showcase projects",  # Monday
    1: "AI tip/tool you should know",  # Tuesday
    2: "Behind the scenes at RAGSPRO",  # Wednesday
    3: "Lesson learned from a client project",  # Thursday
    4: "Client result/full-stack build walkthrough",  # Friday
    5: "Free tip/weekend learning",  # Saturday
    6: "Weekly recap & what's coming"  # Sunday
}

# ============ KEYWORDS FOR LEAD FILTERING ============
LEAD_KEYWORDS = [
    "need developer", "hire developer", "looking for developer",
    "chatbot", "automation", "AI", "artificial intelligence",
    "saas", "SaaS", "website", "web app", "webapp",
    "nextjs", "next.js", "python", "bot", "landing page",
    "mvp", "build", "developer needed"
]

# ============ UTILITIES ============

def get_today_folder():
    """Get today's date folder for content: data/content/YYYY-MM-DD/"""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    folder = CONTENT_DIR / today
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def get_today_proposals_folder():
    """Get today's date folder for proposals: data/proposals/YYYY-MM-DD/"""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    folder = PROPOSALS_DIR / today
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def format_inr(amount):
    """Format amount in Indian Rupees"""
    if amount >= 100000:
        return f"₹{amount/100000:.1f}L"
    elif amount >= 1000:
        return f"₹{amount/1000:.0f}K"
    return f"₹{amount}"

if __name__ == "__main__":
    print("=== RAGSPRO Config Test ===")
    print(f"NVIDIA_API_KEY: {'✓ Set' if NVIDIA_API_KEY else '✗ Missing'}")
    print(f"TELEGRAM_BOT_TOKEN: {'✓ Set' if TELEGRAM_BOT_TOKEN else '✗ Missing'}")
    print(f"GMAIL_USER: {GMAIL_USER}")
    print(f"GMAIL_APP_PASSWORD: {'✓ Set' if GMAIL_APP_PASSWORD else '✗ Missing'}")
    print(f"Today's folder: {get_today_folder()}")
