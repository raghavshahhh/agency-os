#!/usr/bin/env python3
"""
RAGSPRO Telegram Brief - Sends daily morning brief via Telegram
"""

import json
import requests
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    DATA_DIR, CONTENT_DIR, AGENCY_NAME
)


def send_telegram(message):
    """Send message via Telegram Bot"""
    if not TELEGRAM_BOT_TOKEN:
        print("✗ TELEGRAM_BOT_TOKEN not set!")
        return False

    if not TELEGRAM_CHAT_ID:
        print("✗ TELEGRAM_CHAT_ID not set! Send /start to your bot first.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"✗ Telegram Error: {e}")
        return False


def get_stats():
    """Gather all stats for the brief"""
    stats = {
        "total_leads": 0,
        "new_leads": 0,
        "hot_leads": 0,
        "contacted": 0,
        "pipeline_value": 0,
        "pipeline_deals": 0,
        "closed_deals": 0,
        "content_generated": False,
        "content_days": 0,
    }

    # Leads
    leads_file = DATA_DIR / "leads.json"
    if leads_file.exists():
        try:
            with open(leads_file, 'r') as f:
                leads = json.load(f)
            stats["total_leads"] = len(leads)
            stats["new_leads"] = len([l for l in leads if l.get("status") == "NEW"])
            stats["hot_leads"] = len([l for l in leads if l.get("status") == "HOT_LEAD"])
            stats["contacted"] = len([l for l in leads if l.get("status") == "CONTACTED"])
        except Exception:
            pass

    # Pipeline
    pipeline_file = DATA_DIR / "pipeline.json"
    if pipeline_file.exists():
        try:
            with open(pipeline_file, 'r') as f:
                pipeline = json.load(f)
            stats["pipeline_deals"] = len(pipeline)
            stats["pipeline_value"] = sum(d.get("value", 0) for d in pipeline)
            stats["closed_deals"] = len([d for d in pipeline if d.get("stage") == "CLOSED"])
        except Exception:
            pass

    # Content
    today = datetime.now().strftime("%Y-%m-%d")
    today_content = CONTENT_DIR / today
    stats["content_generated"] = today_content.exists() and len(list(today_content.glob("*.txt"))) > 0

    if CONTENT_DIR.exists():
        stats["content_days"] = len([d for d in CONTENT_DIR.iterdir() if d.is_dir()])

    return stats


def format_inr(amount):
    """Format amount in INR"""
    if amount >= 100000:
        return f"₹{amount/100000:.1f}L"
    elif amount >= 1000:
        return f"₹{amount/1000:.0f}K"
    return f"₹{amount}"


def build_brief():
    """Build the daily brief message"""
    now = datetime.now()
    stats = get_stats()

    brief = f"""🌅 *{AGENCY_NAME} Daily Brief*
📅 {now.strftime('%A, %B %d, %Y')} | {now.strftime('%I:%M %p')}

━━━━━━━━━━━━━━━━

📊 *Dashboard Snapshot*
• Total Leads: {stats['total_leads']}
• New Leads: {stats['new_leads']}
• Hot Leads: 🔥 {stats['hot_leads']}
• Contacted: {stats['contacted']}

💰 *Pipeline*
• Active Deals: {stats['pipeline_deals']}
• Pipeline Value: {format_inr(stats['pipeline_value'])}
• Closed: {stats['closed_deals']}

📝 *Content*
• Today's content: {'✅ Generated' if stats['content_generated'] else '❌ Not yet'}
• Total content days: {stats['content_days']}

━━━━━━━━━━━━━━━━

📋 *Today's Checklist:*
□ Post on LinkedIn
□ Post on Twitter
□ Send 5 Fiverr proposals
□ Send 5 Upwork proposals
□ Follow up with hot leads

💡 _Open dashboard: localhost:8501_"""

    return brief


def main():
    """Send daily brief via Telegram"""
    print(f"📱 {AGENCY_NAME} Telegram Brief")
    print("=" * 40)

    brief = build_brief()
    print("\n" + brief)

    print("\n\nSending to Telegram...", end="")
    success = send_telegram(brief)

    if success:
        print(" ✓ Sent!")
    else:
        print(" ✗ Failed (check token/chat_id)")


if __name__ == "__main__":
    main()
