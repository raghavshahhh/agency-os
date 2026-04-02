#!/usr/bin/env python3
"""
RAGSPRO Lead Generation Agent
Self-monitoring agent that scrapes leads continuously
Integrates with existing lead_scraper.py and apify_scraper.py
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from . import BaseAgent
import subprocess
import json


class LeadGenerationAgent(BaseAgent):
    """
    Self-monitoring agent for continuous lead generation
    - Scrapes Reddit every 4 hours
    - Scrapes Google Maps daily
    - Monitors for errors and retries
    - Sends alerts on new leads
    """

    def __init__(self):
        super().__init__(
            name="LeadGenerationAgent",
            description="Continuously scrapes Reddit, Google Maps, LinkedIn for new leads"
        )

        # Add tasks
        self.add_task("reddit_scrape", "Scrape Reddit [HIRING] posts", self._scrape_reddit, 240)  # 4 hours
        self.add_task("gmaps_scrape", "Scrape Google Maps", self._scrape_gmaps, 1440)  # 24 hours
        self.add_task("health_check", "Verify lead database health", self._health_check, 60)  # 1 hour

    def _scrape_reddit(self) -> Dict:
        """Scrape Reddit for [HIRING] posts using existing lead_scraper.py"""
        try:
            # Use existing scraper
            result = subprocess.run(
                ["python3", str(Path(__file__).parent.parent / "lead_scraper.py")],
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse output for new leads count
            new_leads = 0
            for line in result.stdout.split("\n"):
                if "New [HIRING] leads:" in line:
                    try:
                        new_leads = int(line.split(":")[1].strip())
                    except:
                        pass

            # Send alert if new leads found
            if new_leads > 0:
                self.send_alert(f"🎉 Found {new_leads} new [HIRING] leads from Reddit!", priority="normal")

            return {"success": True, "new_leads": new_leads, "output": result.stdout[:500]}

        except Exception as e:
            raise Exception(f"Reddit scraping failed: {e}")

    def _scrape_gmaps(self) -> Dict:
        """Scrape Google Maps using existing apify_scraper.py"""
        try:
            from apify_scraper import run_daily_scrape

            new_leads = run_daily_scrape()

            if new_leads > 0:
                self.send_alert(f"🎉 Found {new_leads} new business leads from Google Maps!", priority="normal")

            return {"success": True, "new_leads": new_leads}

        except Exception as e:
            raise Exception(f"Google Maps scraping failed: {e}")

    def _health_check(self) -> Dict:
        """Verify lead database is healthy"""
        try:
            from config import DATA_DIR

            leads_file = DATA_DIR / "leads.json"
            if not leads_file.exists():
                return {"success": True, "message": "No leads file yet"}

            with open(leads_file) as f:
                leads = json.load(f)

            total = len(leads)
            new_count = len([l for l in leads if l.get("status") == "NEW"])
            contacted = len([l for l in leads if l.get("status") == "CONTACTED"])
            hot = len([l for l in leads if l.get("status") == "HOT_LEAD"])

            # Alert if too many uncontacted leads
            if new_count > 50:
                self.send_alert(
                    f"⚠️ {new_count} uncontacted leads piling up! Time for outreach.",
                    priority="high"
                )

            return {
                "success": True,
                "total": total,
                "new": new_count,
                "contacted": contacted,
                "hot": hot
            }

        except Exception as e:
            raise Exception(f"Health check failed: {e}")


if __name__ == "__main__":
    agent = LeadGenerationAgent()
    agent.start()

    # Keep main thread alive
    import time
    while True:
        time.sleep(1)
