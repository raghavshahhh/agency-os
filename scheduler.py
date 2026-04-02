#!/usr/bin/env python3
"""
RAGSPRO Scheduler — Automated lead scraping, content generation, and notifications
Schedule: Lead scraping every 4 hours, Content at 7 AM, Telegram brief at 8 AM
"""

import schedule
import time
import subprocess
from datetime import datetime
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent / "engine"))

try:
    from telegram_brief import send_brief
except:
    send_brief = None

ENGINE_DIR = Path(__file__).parent / "engine"
DATA_DIR = Path(__file__).parent / "data"


def scrape_leads():
    """Run lead scraper every 4 hours"""
    print(f"[{datetime.now()}] 🔍 Scraping leads...")
    try:
        result = subprocess.run(
            [sys.executable, str(ENGINE_DIR / "lead_scraper.py")],
            capture_output=True,
            text=True,
            timeout=180
        )
        print(result.stdout)

        # Parse output for new leads count
        new_leads = 0
        for line in result.stdout.split("\n"):
            if "New [HIRING] leads:" in line:
                try:
                    new_leads = int(line.split(":")[1].strip())
                except:
                    pass

        # Auto-score new leads if any found
        if new_leads > 0:
            try:
                score_new_leads()
            except Exception as e:
                print(f"Error scoring leads: {e}")

            if send_brief:
                send_brief(f"🎯 Scraped {new_leads} new [HIRING] leads!")

        return new_leads
    except Exception as e:
        print(f"❌ Error scraping: {e}")
        return 0


def score_new_leads():
    """Auto-score newly scraped leads"""
    leads_file = DATA_DIR / "leads.json"
    if not leads_file.exists():
        return

    try:
        with open(leads_file, 'r') as f:
            leads = json.load(f)

        # Re-score leads that don't have a calculated score
        for lead in leads:
            if lead.get("status") == "NEW" and not lead.get("auto_scored"):
                score = calculate_lead_score(lead)
                lead["score"] = score
                lead["auto_scored"] = True

        with open(leads_file, 'w') as f:
            json.dump(leads, f, indent=2, default=str)

        print(f"✅ Auto-scored {len([l for l in leads if l.get('auto_scored')])} leads")
    except Exception as e:
        print(f"❌ Error in auto-scoring: {e}")


def calculate_lead_score(lead):
    """Calculate lead score based on multiple factors"""
    score = lead.get("score", 0)

    # Boost for having email
    if lead.get("contact", {}).get("email"):
        score += 10

    # Boost for having LinkedIn
    if lead.get("contact", {}).get("linkedin"):
        score += 5

    # Boost for keywords in title
    high_value = ["chatbot", "ai chatbot", "automation", "ai agent", "saas",
                  "web app", "webapp", "dashboard", "platform", "mvp"]
    title = lead.get("title", "").lower()
    for kw in high_value:
        if kw in title:
            score += 15

    return min(score, 100)


def generate_daily_content():
    """Generate content for all platforms at 7 AM"""
    print(f"[{datetime.now()}] 📝 Generating daily content...")
    try:
        result = subprocess.run(
            [sys.executable, str(ENGINE_DIR / "content_engine.py")],
            capture_output=True,
            text=True,
            timeout=180
        )
        print(result.stdout)

        if send_brief:
            send_brief("📝 Daily content generated for LinkedIn, Twitter, Instagram & Reels!")

        return True
    except Exception as e:
        print(f"❌ Error generating content: {e}")
        return False


def daily_telegram_brief():
    """Send Telegram brief at 8 AM"""
    print(f"[{datetime.now()}] 📱 Sending Telegram brief...")

    # Gather stats
    leads_file = DATA_DIR / "leads.json"
    revenue_file = DATA_DIR / "revenue.json"
    pipeline_file = DATA_DIR / "pipeline.json"

    stats = {
        "total_leads": 0,
        "new_leads": 0,
        "hot_leads": 0,
        "monthly_revenue": 0,
        "pipeline_value": 0
    }

    # Lead stats
    if leads_file.exists():
        try:
            with open(leads_file) as f:
                leads = json.load(f)
                stats["total_leads"] = len(leads)
                stats["new_leads"] = len([l for l in leads if l.get("status") == "NEW"])
                stats["hot_leads"] = len([l for l in leads if l.get("status") == "HOT_LEAD"])
        except:
            pass

    # Revenue stats
    if revenue_file.exists():
        try:
            with open(revenue_file) as f:
                data = json.load(f)
                current_month = datetime.now().strftime("%Y-%m")
                for entry in data.get("entries", []):
                    if entry.get("date", "").startswith(current_month):
                        if entry.get("type") == "income":
                            stats["monthly_revenue"] += entry.get("amount", 0)
        except:
            pass

    # Pipeline stats
    if pipeline_file.exists():
        try:
            with open(pipeline_file) as f:
                pipeline = json.load(f)
                stats["pipeline_value"] = sum(d.get("value", 0) for d in pipeline)
        except:
            pass

    message = f"""📊 <b>RAGSPRO Daily Brief - {datetime.now().strftime('%B %d, %I:%M %p')}</b>

🎯 <b>Leads:</b> {stats['total_leads']} total | {stats['new_leads']} new | {stats['hot_leads']} hot 🔥
💰 <b>Revenue:</b> ₹{stats['monthly_revenue']:,} this month
📈 <b>Pipeline:</b> ₹{stats['pipeline_value']:,}

Have a productive day! 🚀"""

    if send_brief:
        send_brief(message)


def run_scheduler():
    """Run the scheduler with all automated tasks"""
    print("=" * 60)
    print("⏰ RAGSPRO Scheduler Started")
    print("=" * 60)
    print("\n📅 Scheduled Tasks:")
    print(" • Lead scraping: Every 4 hours (6 AM, 10 AM, 2 PM, 6 PM, 10 PM)")
    print(" • Content generation: Daily at 7:00 AM")
    print(" • Telegram brief: Daily at 8:00 AM")
    print("\nPress Ctrl+C to stop\n")

    # Schedule lead scraping every 4 hours
    schedule.every(4).hours.do(scrape_leads)

    # Schedule content generation at 7 AM
    schedule.every().day.at("07:00").do(generate_daily_content)

    # Schedule Telegram brief at 8 AM
    schedule.every().day.at("08:00").do(daily_telegram_brief)

    # Run lead scrape immediately on startup
    scrape_leads()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    run_scheduler()
