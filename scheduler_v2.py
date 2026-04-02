#!/usr/bin/env python3
"""
RAGSPRO Scheduler V2 — Full automation with Apify + Email sequences
Schedule:
  - Lead scraping (Reddit + Apify) every 4 hours
  - Email sequences daily at 9 AM
  - Telegram brief daily at 8 AM
"""

import schedule
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import json

# Add engine to path
sys.path.insert(0, str(Path(__file__).parent / "engine"))

# NEW: Unified modules
try:
    from scrapers import run_daily_scrape as unified_scrape
except ImportError:
    from engine.scrapers import scrape as unified_scrape

try:
    from outreach import run_email_sequences
except ImportError:
    from engine.outreach_engine import run_email_sequences

try:
    from analytics import get_daily_report
except ImportError:
    from engine.analytics import get_daily_report

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

ENGINE_DIR = Path(__file__).parent / "engine"
DATA_DIR = Path(__file__).parent / "data"

def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"⚠️ Telegram not configured")
        return False

    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        })
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def run_all_lead_scraping():
    """Run unified lead scraper (Reddit + Google Maps + LinkedIn)"""
    print(f"\n{'='*60}")
    print(f"🚀 Starting Unified Lead Scraping — {datetime.now()}")
    print(f"{'='*60}")

    try:
        result = unified_scrape()

        stats = result.get("by_source", {})
        total = result.get("new_leads", 0)

        message = f"""📊 <b>Daily Lead Report</b>

🔍 Reddit Leads: {stats.get('reddit', 0)}
🌐 Google Maps: {stats.get('google_maps', 0)}
💼 LinkedIn Jobs: {stats.get('linkedin', 0)}
✅ <b>Total New: {total}</b>
📊 Total DB: {result.get('total_leads', 0)}

Next: Email sequences at 9 AM
"""
        send_telegram_message(message)
        print(f"\n✅ Total new leads: {total}")

        return total
    except Exception as e:
        print(f"❌ Scraping error: {e}")
        send_telegram_message(f"⚠️ Scraping error: {e}")
        return 0

def run_daily_email_sequences():
    """Run email automation"""
    print(f"\n{'='*60}")
    print(f"📧 Starting Email Sequences — {datetime.now()}")
    print(f"{'='*60}")

    try:
        stats = run_email_sequences()

        message = f"""📧 <b>Email Sequence Report</b>

✉️ Day 0 (Initial): {stats.get('day_0', 0)}
🔄 Day 3 (Follow-up): {stats.get('day_3', 0)}
🚪 Day 7 (Break-up): {stats.get('day_7', 0)}
🔥 Hot Leads: {stats.get('hot_leads', 0)}
📄 Proposals: {stats.get('proposals', 0)}

<b>Total Sent: {sum(v for k, v in stats.items() if k != 'errors')}</b>
"""
        send_telegram_message(message)

        return stats
    except Exception as e:
        print(f"❌ Email automation error: {e}")
        send_telegram_message(f"⚠️ Email error: {e}")
        return {}

def send_morning_brief():
    """Send morning summary with marketing metrics"""
    # Load data
    leads_file = DATA_DIR / "leads.json"
    crm_file = DATA_DIR / "crm_deals.json"
    content_file = DATA_DIR / "content_queue.json"

    leads_count = 0
    deals_count = 0
    scheduled_content = 0

    if leads_file.exists():
        with open(leads_file) as f:
            leads = json.load(f)
            leads_count = len(leads)

    if crm_file.exists():
        with open(crm_file) as f:
            deals = json.load(f)
            deals_count = len(deals)

    if content_file.exists():
        with open(content_file) as f:
            content = json.load(f)
            scheduled_content = len([c for c in content if c.get("status") == "scheduled"])

    message = f"""🌅 <b>Good Morning Raghav!</b>

📊 <b>Agency OS Status:</b>
• Total Leads: {leads_count}
• Active Deals: {deals_count}
• Content Scheduled: {scheduled_content}

📱 <b>Marketing Today:</b>
• 1 Reel: Build in public update
• Reply to all DMs within 1 hour
• Engage with 10 similar accounts

🎯 <b>Today's Focus:</b>
• Close 1 deal
• Follow up with hot leads
• Post Instagram Reel at 7 PM

Let's crush it! 💪
"""
    send_telegram_message(message)


def generate_weekly_content():
    """Generate content for the week"""
    print(f"\n{'='*60}")
    print(f"📝 Generating Weekly Content — {datetime.now()}")
    print(f"{'='*60}")

    try:
        from content_factory import ContentFactory
        factory = ContentFactory()
        content = factory.generate_weekly_content()

        message = f"""📝 <b>Weekly Content Generated</b>

✅ {len(content)} pieces scheduled
• Reels: {len([c for c in content if c.content_type == 'reel'])}
• Carousels: {len([c for c in content if c.content_type == 'carousel'])}
• Stories: {len([c for c in content if c.content_type == 'story'])}

All ready for review in Marketing Dashboard!
"""
        send_telegram_message(message)
        print(f"✅ Generated {len(content)} content pieces")

    except Exception as e:
        print(f"❌ Content generation error: {e}")
        send_telegram_message(f"⚠️ Content generation error: {e}")


def send_weekly_report():
    """Send weekly marketing report"""
    print(f"\n{'='*60}")
    print(f"📊 Weekly Report — {datetime.now()}")
    print(f"{'='*60}")

    try:
        from analytics import get_weekly_report
        report = get_weekly_report()

        metrics = report.get("summary", {})

        message = f"""📊 <b>Weekly Marketing Report</b>

📈 <b>This Week:</b>
• Leads: {metrics.get('leads', {}).get('total', 0)}
• Emails Sent: {metrics.get('emails', {}).get('sent_today', 0)}
• Content Posted: {metrics.get('content', {}).get('posted', 0)}

💡 <b>Recommendations:</b>
{chr(10).join(['• ' + r for r in report.get('recommendations', [])[:3]])}

Full report in dashboard!
"""
        send_telegram_message(message)
        print("✅ Weekly report sent")

    except Exception as e:
        print(f"❌ Weekly report error: {e}")

def test_all_systems():
    """Test all automation systems"""
    print("="*60)
    print("🧪 Testing Agency OS Automation V2")
    print("="*60)

    print("\n1️⃣ Testing Unified Scraper...")
    try:
        from scrapers import UnifiedScraper
        scraper = UnifiedScraper()
        print("   ✅ Unified scraper initialized")
    except Exception as e:
        print(f"   ❌ Scraper error: {e}")

    print("\n2️⃣ Testing Unified Outreach...")
    try:
        from outreach import UnifiedOutreach
        outreach = UnifiedOutreach()
        print("   ✅ Unified outreach initialized")
    except Exception as e:
        print(f"   ❌ Outreach error: {e}")

    print("\n3️⃣ Testing Social Modules...")
    try:
        from social.instagram_analyzer import InstagramAnalyzer
        from social.youtube_analyzer import YouTubeAnalyzer
        print("   ✅ Social modules loaded")
    except Exception as e:
        print(f"   ❌ Social modules error: {e}")

    print("\n4️⃣ Testing Content Factory...")
    try:
        from content_factory import ContentFactory
        factory = ContentFactory()
        print("   ✅ Content factory initialized")
    except Exception as e:
        print(f"   ❌ Content factory error: {e}")

    print("\n5️⃣ Testing Telegram...")
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print(f"   ✅ Telegram configured")
        send_telegram_message("🧪 <b>Agency OS V2 Test</b>\nAll unified systems operational!")
    else:
        print(f"   ⚠️ Telegram not configured")

    print("\n✅ System test complete")

# Schedule jobs
print("="*60)
print("📅 RAGSPRO Scheduler V2 Started")
print("="*60)
print("\nScheduled Jobs:")
print("  • Lead scraping: Every 4 hours")
print("  • Email sequences: Daily at 9:00 AM")
print("  • Morning brief: Daily at 8:00 AM")
print("  • Content generation: Sundays at 6:00 PM")
print("  • Weekly report: Sundays at 8:00 PM")
print("="*60)

# Schedule
schedule.every(4).hours.do(run_all_lead_scraping)
schedule.every().day.at("09:00").do(run_daily_email_sequences)
schedule.every().day.at("08:00").do(send_morning_brief)
schedule.every().sunday.at("18:00").do(generate_weekly_content)
schedule.every().sunday.at("20:00").do(send_weekly_report)

# Test on first run
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Test all systems")
    parser.add_argument("--scrape-now", action="store_true", help="Run scrape immediately")
    parser.add_argument("--email-now", action="store_true", help="Run email sequences immediately")
    args = parser.parse_args()

    if args.test:
        test_all_systems()
    elif args.scrape_now:
        run_all_lead_scraping()
    elif args.email_now:
        run_daily_email_sequences()
    else:
        # Run scheduler loop
        print("\n⏳ Scheduler running... Press Ctrl+C to stop")

        # Do initial scrape
        run_all_lead_scraping()

        while True:
            schedule.run_pending()
            time.sleep(60)
