#!/usr/bin/env python3
"""
RAGSPRO Scheduler — Automated lead scraping and notifications
"""

import schedule
import time
import subprocess
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "engine"))

try:
    from telegram_brief import send_brief
except:
    send_brief = None

ENGINE_DIR = Path(__file__).parent / "engine"


def scrape_leads():
    """Run lead scraper"""
    print(f"[{datetime.now()}] Scraping leads...")
    try:
        result = subprocess.run(
            ["python3", str(ENGINE_DIR / "lead_scraper.py")],
            capture_output=True,
            text=True,
            timeout=120
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

        if send_brief and new_leads > 0:
            send_brief(f"🎯 Scraped {new_leads} new [HIRING] leads!")

        return new_leads
    except Exception as e:
        print(f"Error scraping: {e}")
        return 0


def daily_report():
    """Send daily summary"""
    print(f"[{datetime.now()}] Sending daily report...")

    from config import DATA_DIR
    import json

    # Load stats
    leads_file = DATA_DIR / "leads.json"
    revenue_file = DATA_DIR / "revenue.json"

    total_leads = 0
    if leads_file.exists():
        try:
            with open(leads_file) as f:
                leads = json.load(f)
                total_leads = len(leads)
        except:
            pass

    monthly_revenue = 0
    if revenue_file.exists():
        try:
            with open(revenue_file) as f:
                data = json.load(f)
                current_month = datetime.now().strftime("%Y-%m")
                for entry in data.get("entries", []):
                    if entry.get("date", "").startswith(current_month):
                        if entry.get("type") == "income":
                            monthly_revenue += entry.get("amount", 0)
        except:
            pass

    message = f"""📊 <b>Daily Report - {datetime.now().strftime('%B %d')}</b>

🎯 Total Leads: {total_leads}
💰 Monthly Revenue: ₹{monthly_revenue:,}

Keep grinding! 🚀"""

    if send_brief:
        send_brief(message)


def run_scheduler():
    """Run the scheduler"""
    print("=" * 50)
    print("⏰ RAGSPRO Scheduler Started")
    print("=" * 50)
    print("\nScheduled tasks:")
    print("  • Scrape leads: Every 6 hours")
    print("  • Daily report: Every day at 9 AM")
    print("\nPress Ctrl+C to stop\n")

    # Schedule tasks
    schedule.every(6).hours.do(scrape_leads)
    schedule.every().day.at("09:00").do(daily_report)

    # Run immediately once
    scrape_leads()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    run_scheduler()
