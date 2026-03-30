#!/usr/bin/env python3
"""
RAGSPRO Scheduler - Sets up cron jobs for all engines
"""

import sys
from pathlib import Path
from crontab import CronTab

# Get project paths
PROJECT_DIR = Path(__file__).parent.parent.absolute()
ENGINE_DIR = PROJECT_DIR / "engine"
PYTHON = "/usr/bin/python3"

def setup_cron_jobs():
    """Setup all cron jobs"""
    print("⏰ RAGSPRO Scheduler")
    print("=" * 40)

    cron = CronTab(user=True)

    # Remove existing RAGSPRO jobs
    existing = list(cron.find_comment("RAGSPRO"))
    for job in existing:
        cron.remove(job)
    print(f"✓ Removed {len(existing)} existing jobs")

    # Jobs configuration
    jobs = [
        {
            "name": "content_engine",
            "time": "0 7 * * *",  # 7:00 AM daily
            "script": "content_engine.py",
            "desc": "Generate daily content"
        },
        {
            "name": "lead_scraper",
            "time": "30 7 * * *",  # 7:30 AM daily
            "script": "lead_scraper.py",
            "desc": "Scrape leads from Reddit"
        },
        {
            "name": "telegram_brief",
            "time": "0 8 * * *",  # 8:00 AM daily
            "script": "telegram_brief.py",
            "desc": "Send daily Telegram brief"
        },
        {
            "name": "proposal_engine",
            "time": "0 9 * * *",  # 9:00 AM daily
            "script": "proposal_engine.py",
            "desc": "Generate proposals"
        }
    ]

    # Add lead scraper every 4 hours
    job = cron.new(
        command=f"cd {ENGINE_DIR} && {PYTHON} lead_scraper.py >> {PROJECT_DIR}/logs/lead_scraper.log 2>&1",
        comment="RAGSPRO lead_scraper_4h"
    )
    job.setall("0 */4 * * *")
    print("✓ Added: Lead scraper every 4 hours")

    # Create logs directory
    logs_dir = PROJECT_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Add jobs
    for job_config in jobs:
        cmd = f"cd {ENGINE_DIR} && {PYTHON} {job_config['script']} >> {logs_dir}/{job_config['name']}.log 2>&1"
        job = cron.new(command=cmd, comment=f"RAGSPRO {job_config['name']}")
        job.setall(job_config['time'])
        print(f"✓ Added: {job_config['desc']} at {job_config['time']}")

    # Enable cron service reminder
    print("\n⚠️  IMPORTANT:")
    print("Enable cron service with:")
    print("  sudo launchctl load -w /System/Library/LaunchDaemons/com.vix.cron.plist")

    # Write to temp file first (crontab requires confirmation)
    cron.write()
    print(f"\n✅ Cron jobs written successfully!")

    # Show current jobs
    print("\n📋 Current RAGSPRO cron jobs:")
    print("-" * 40)
    for job in cron.find_comment("RAGSPRO"):
        print(f"  {job}")

def remove_all_jobs():
    """Remove all RAGSPRO cron jobs"""
    cron = CronTab(user=True)
    existing = list(cron.find_comment("RAGSPRO"))
    for job in existing:
        cron.remove(job)
    cron.write()
    print(f"✓ Removed {len(existing)} RAGSPRO jobs")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="RAGSPRO Scheduler")
    parser.add_argument("--remove", action="store_true", help="Remove all jobs")
    args = parser.parse_args()

    if args.remove:
        remove_all_jobs()
    else:
        setup_cron_jobs()

if __name__ == "__main__":
    main()
