#!/usr/bin/env python3
"""
RAGSPRO Outreach Automation Agent
Self-monitoring agent that handles email sequences
Integrates with existing outreach_engine.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from . import BaseAgent


class OutreachAutomationAgent(BaseAgent):
    """
    Self-monitoring agent for automated outreach
    - Sends Day 0 emails to new leads
    - Day 3 and Day 7 follow-ups
    - Monitors reply rates
    - Alerts on high bounce rates
    """

    def __init__(self):
        super().__init__(
            name="OutreachAutomationAgent",
            description="Automates email sequences: Day 0, Day 3, Day 7 follow-ups"
        )

        # Add tasks
        self.add_task("day0_emails", "Send Day 0 emails to new leads", self._send_day0, 60)  # Every hour
        self.add_task("followups", "Send Day 3/7 follow-ups", self._send_followups, 360)  # Every 6 hours
        self.add_task("stats_report", "Daily outreach stats report", self._daily_stats, 1440)  # Daily

    def _send_day0(self) -> Dict:
        """Send initial emails to new leads"""
        try:
            from outreach_engine import generate_cold_email, send_email_resend, log_outreach
            from config import DATA_DIR

            leads_file = DATA_DIR / "leads.json"
            if not leads_file.exists():
                return {"success": True, "message": "No leads file"}

            with open(leads_file) as f:
                leads = json.load(f)

            # Find NEW leads with email
            new_leads = [
                l for l in leads
                if l.get("status") == "NEW" and l.get("contact", {}).get("email")
            ]

            sent_count = 0
            failed_count = 0

            for lead in new_leads[:5]:  # Max 5 per run
                try:
                    email = lead.get("contact", {}).get("email")
                    if not email:
                        continue

                    # Generate personalized email
                    email_content = generate_cold_email(lead)
                    if not email_content or email_content.startswith("Error"):
                        failed_count += 1
                        continue

                    # Parse subject and body
                    lines = email_content.split("\n")
                    subject = lines[0].replace("Subject:", "").strip()
                    body = "\n".join(lines[1:]).strip()

                    # Send via Resend
                    result = send_email_resend(email, subject, body)

                    if result.get("success"):
                        log_outreach(lead.get("id"), "email", email_content, sent_via="resend")
                        lead["status"] = "CONTACTED"
                        lead["contacted_at"] = datetime.now().isoformat()
                        sent_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    self.log(f"Failed to send to {lead.get('id')}: {e}", "error")
                    failed_count += 1

            # Save updated leads
            with open(leads_file, 'w') as f:
                json.dump(leads, f, indent=2)

            if sent_count > 0:
                self.send_alert(
                    f"📧 Sent {sent_count} Day 0 emails! Failed: {failed_count}",
                    priority="normal"
                )

            return {"success": True, "sent": sent_count, "failed": failed_count}

        except Exception as e:
            raise Exception(f"Day 0 email sending failed: {e}")

    def _send_followups(self) -> Dict:
        """Send Day 3 and Day 7 follow-up emails"""
        try:
            from outreach_engine import generate_cold_email_followup, send_email_resend, log_outreach, get_lead_outreach_history
            from config import DATA_DIR

            leads_file = DATA_DIR / "leads.json"
            if not leads_file.exists():
                return {"success": True, "message": "No leads file"}

            with open(leads_file) as f:
                leads = json.load(f)

            now = datetime.now()
            day3_sent = 0
            day7_sent = 0

            for lead in leads:
                if lead.get("status") != "CONTACTED":
                    continue

                # Get outreach history
                history = get_lead_outreach_history(lead.get("id"))
                email_history = [h for h in history if h.get("type") == "email"]

                if not email_history:
                    continue

                # Check last email date
                last_email = max(email_history, key=lambda x: x.get("sent_at", ""))
                last_sent = datetime.fromisoformat(last_email.get("sent_at", now.isoformat()))
                days_since = (now - last_sent).days

                email = lead.get("contact", {}).get("email")
                if not email:
                    continue

                # Day 3 follow-up
                if days_since >= 3 and days_since < 7 and len(email_history) == 1:
                    try:
                        followup = generate_cold_email_followup(lead, email_history)
                        if followup and not followup.startswith("Error"):
                            result = send_email_resend(email, "Re: quick question", followup)
                            if result.get("success"):
                                log_outreach(lead.get("id"), "email_followup", followup, sent_via="resend")
                                day3_sent += 1
                    except Exception as e:
                        self.log(f"Day 3 follow-up failed for {lead.get('id')}: {e}", "error")

                # Day 7 break-up
                elif days_since >= 7 and len(email_history) == 2:
                    try:
                        breakup = generate_cold_email_followup(lead, email_history, is_final=True)
                        if breakup and not breakup.startswith("Error"):
                            result = send_email_resend(email, "should I close the loop?", breakup)
                            if result.get("success"):
                                log_outreach(lead.get("id"), "email_breakup", breakup, sent_via="resend")
                                lead["status"] = "CONTACTED"  # Keep as contacted but stop follow-ups
                                day7_sent += 1
                    except Exception as e:
                        self.log(f"Day 7 break-up failed for {lead.get('id')}: {e}", "error")

            # Save updated leads
            with open(leads_file, 'w') as f:
                json.dump(leads, f, indent=2)

            total_sent = day3_sent + day7_sent
            if total_sent > 0:
                self.send_alert(
                    f"🔄 Sent {day3_sent} Day 3 + {day7_sent} Day 7 follow-ups!",
                    priority="normal"
                )

            return {"success": True, "day3": day3_sent, "day7": day7_sent}

        except Exception as e:
            raise Exception(f"Follow-up sending failed: {e}")

    def _daily_stats(self) -> Dict:
        """Generate and send daily outreach statistics"""
        try:
            from outreach_engine import get_outreach_stats
            from config import DATA_DIR

            stats = get_outreach_stats()

            leads_file = DATA_DIR / "leads.json"
            total_leads = 0
            new_leads = 0
            hot_leads = 0

            if leads_file.exists():
                with open(leads_file) as f:
                    leads = json.load(f)
                    total_leads = len(leads)
                    new_leads = len([l for l in leads if l.get("status") == "NEW"])
                    hot_leads = len([l for l in leads if l.get("status") == "HOT_LEAD"])

            message = f"""📊 Daily Outreach Report

📧 Emails Sent: {stats.get('emails_sent', 0)}
💬 LinkedIn DMs: {stats.get('linkedin_sent', 0)}
📞 Calls Made: {stats.get('calls_made', 0)}
✅ Replies: {stats.get('replied', 0)}

📈 Lead Pipeline:
• Total: {total_leads}
• New: {new_leads}
• Hot: {hot_leads}

Keep crushing it! 💪"""

            self.send_alert(message, priority="normal")

            return {"success": True, **stats}

        except Exception as e:
            raise Exception(f"Stats report failed: {e}")


if __name__ == "__main__":
    agent = OutreachAutomationAgent()
    agent.start()

    import time
    while True:
        time.sleep(1)
