#!/usr/bin/env python3
"""
RAGSPRO Unified Outreach Module
Combines: Email automation, LinkedIn outreach, follow-up sequences
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import sys

try:
    import requests
except ImportError:
    print("⚠️ requests not installed. Run: pip install requests")
    requests = None

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR, RESEND_API_KEY, AGENCY_NAME, GMAIL_USER

LEADS_FILE = DATA_DIR / "leads.json"
EMAIL_LOG_FILE = DATA_DIR / "email_automation_log.json"
OUTREACH_LOG_FILE = DATA_DIR / "outreach_log.json"


@dataclass
class EmailTemplate:
    name: str
    subject: str
    body: str
    delay_days: int
    condition: str


class TemplateLibrary:
    """All email templates in one place"""

    DAY_0 = EmailTemplate(
        name="day_0",
        subject="quick question",
        delay_days=0,
        condition="NEW",
        body="""Hi {first_name},

Saw {company} - congrats on the recent growth.

Quick question: Are you still handling {pain_point} manually?

We just helped a similar {industry} company automate their lead generation and they saw 40% more qualified leads in 30 days.

Worth a quick look?

Raghav
{agency_name}
{agency_url}"""
    )

    DAY_3 = EmailTemplate(
        name="day_3",
        subject="Re: quick question",
        delay_days=3,
        condition="CONTACTED",
        body="""Hey {first_name},

In case this got buried - wanted to share exactly how we helped a similar company:

They were spending 10+ hours/week on manual {pain_point}. We built them an automated workflow that:

✅ Scrapes 100 leads/day from Google Maps
✅ Auto-sends personalized emails
✅ Updates their CRM automatically
✅ Books meetings on autopilot

Result: 40% more qualified leads, zero manual work.

If that sounds relevant, happy to share the playbook.

Raghav
{agency_name}"""
    )

    DAY_7 = EmailTemplate(
        name="day_7",
        subject="should I close the loop?",
        delay_days=7,
        condition="CONTACTED",
        body="""{first_name},

No worries if timing's off - should I close this out for now?

Or if {pain_point} is still a thing, here's a 5-min Loom showing exactly how we'd approach it:

https://loom.com/share/example

Either way, no hard feelings!

Raghav"""
    )

    PROPOSAL_FOLLOWUP = EmailTemplate(
        name="proposal_followup",
        subject="Quick follow-up on proposal",
        delay_days=1,
        condition="PROPOSAL_SENT",
        body="""Hi {first_name},

Just floating this to the top of your inbox in case you had a chance to review the proposal I sent.

Happy to answer any questions or jump on a quick call to discuss.

Best,
Raghav"""
    )

    DEAL_WON = EmailTemplate(
        name="deal_won",
        subject="Welcome to {agency_name} - Let's Get Started!",
        delay_days=0,
        condition="CLOSED_WON",
        body="""Hi {first_name},

Welcome aboard! 🎉

I'm excited to work with {company}. Here's what happens next:

1. Project kickoff call (schedule here: https://calendly.com/raghavshah)
2. I'll send the invoice for 50% advance
3. We start building!

Timeline: {timeline}

Questions? Just reply to this email.

Let's build something amazing,
Raghav

P.S. Join our private client Telegram for updates: t.me/ragspro_clients"""
    )

    HOT_LEAD = EmailTemplate(
        name="hot_lead",
        subject="Quick question about {company}",
        delay_days=0,
        condition="HOT_LEAD",
        body="""Hi {first_name},

Thanks for your interest! I looked at {company} and have some ideas on how we can help with {pain_point}.

Got 15 mins this week for a quick call? I'm free Tuesday 2-4pm IST or Thursday morning.

Here's my cal: https://calendly.com/raghavshah

Raghav
{agency_name}"""
    )

    @classmethod
    def get_all(cls) -> List[EmailTemplate]:
        return [cls.DAY_0, cls.DAY_3, cls.DAY_7, cls.PROPOSAL_FOLLOWUP, cls.DEAL_WON, cls.HOT_LEAD]

    @classmethod
    def get_by_name(cls, name: str) -> Optional[EmailTemplate]:
        for template in cls.get_all():
            if template.name == name:
                return template
        return None


class LeadManager:
    """Manage leads from JSON file"""

    def __init__(self):
        self.leads_file = LEADS_FILE
        self._ensure_file()

    def _ensure_file(self):
        if not self.leads_file.exists():
            self.leads_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.leads_file, 'w') as f:
                json.dump([], f)

    def load(self) -> List[Dict]:
        with open(self.leads_file, 'r') as f:
            return json.load(f)

    def save(self, leads: List[Dict]):
        with open(self.leads_file, 'w') as f:
            json.dump(leads, f, indent=2)

    def update_status(self, lead_id: str, new_status: str):
        leads = self.load()
        for lead in leads:
            if lead.get("id") == lead_id:
                lead["status"] = new_status
                lead["last_updated"] = datetime.now().isoformat()
                break
        self.save(leads)

    def get_by_status(self, status: str) -> List[Dict]:
        return [l for l in self.load() if l.get("status") == status]

    def get_by_id(self, lead_id: str) -> Optional[Dict]:
        for lead in self.load():
            if lead.get("id") == lead_id:
                return lead
        return None


class EmailSender:
    """Send emails via Resend API"""

    def __init__(self):
        if requests is None:
            raise ImportError("requests module not available. Run: pip install requests")

        self.api_key = RESEND_API_KEY
        self.from_email = GMAIL_USER or "raghav@ragspro.com"

    def send(self, to_email: str, subject: str, body: str) -> bool:
        if not self.api_key:
            print(f"⚠️ RESEND_API_KEY not set, skipping email to {to_email}")
            return False

        try:
            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": f"Raghav at {AGENCY_NAME} <{self.from_email}>",
                    "to": [to_email],
                    "subject": subject,
                    "text": body
                },
                timeout=30
            )
            return response.status_code in [200, 201, 202]
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False


class OutreachLogger:
    """Log all outreach activity"""

    def __init__(self):
        self.log_file = OUTREACH_LOG_FILE
        self.email_log_file = EMAIL_LOG_FILE

    def _load(self, file_path: Path) -> Dict:
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}

    def _save(self, file_path: Path, data: Dict):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def was_sent(self, lead_id: str, template_name: str) -> bool:
        log = self._load(self.email_log_file)
        lead_log = log.get(lead_id, [])
        return any(entry.get("template") == template_name for entry in lead_log)

    def log_email(self, lead_id: str, template_name: str, email: str, success: bool):
        log = self._load(self.email_log_file)
        if lead_id not in log:
            log[lead_id] = []

        log[lead_id].append({
            "template": template_name,
            "sent_at": datetime.now().isoformat(),
            "email": email,
            "status": "sent" if success else "failed"
        })
        self._save(self.email_log_file, log)

    def log_activity(self, lead_id: str, activity_type: str, details: Dict = None):
        log = self._load(self.log_file)
        if lead_id not in log:
            log[lead_id] = []

        entry = {
            "type": activity_type,
            "at": datetime.now().isoformat()
        }
        if details:
            entry.update(details)

        log[lead_id].append(entry)
        self._save(self.log_file, log)


class Personalizer:
    """Personalize email content based on lead data"""

    @staticmethod
    def get_first_name(name: str) -> str:
        return name.split()[0] if name else "there"

    @staticmethod
    def detect_pain_point(lead: Dict) -> str:
        title = lead.get("title", "").lower()
        industry = lead.get("industry", "").lower()

        if any(x in title for x in ["developer", "software", "tech", "engineer"]):
            return "lead generation"
        elif any(x in title for x in ["marketing", "sales"]):
            return "outreach and follow-ups"
        elif any(x in title for x in ["operations", "automation"]):
            return "manual workflows"
        elif "saas" in industry or "software" in industry:
            return "customer acquisition"
        else:
            return "manual processes"

    @classmethod
    def fill_template(cls, template: EmailTemplate, lead: Dict) -> Tuple[str, str]:
        first_name = cls.get_first_name(lead.get("name", ""))
        pain_point = cls.detect_pain_point(lead)

        subject = template.subject.format(
            agency_name=AGENCY_NAME,
            company=lead.get("company", "your company")
        )

        body = template.body.format(
            first_name=first_name,
            company=lead.get("company", "your company"),
            industry=lead.get("industry", "business"),
            pain_point=pain_point,
            agency_name=AGENCY_NAME,
            agency_url="https://ragspro.com",
            timeline="2-3 weeks"
        )

        return subject, body


class UnifiedOutreach:
    """Main outreach orchestrator"""

    def __init__(self):
        self.leads = LeadManager()
        self.sender = EmailSender()
        self.logger = OutreachLogger()
        self.personalizer = Personalizer()

    def get_email_for_lead(self, lead: Dict) -> Optional[str]:
        """Extract best email from lead data"""
        contact = lead.get("contact", {})

        # Try emails list first
        emails = contact.get("emails", [])
        if emails and emails[0]:
            return emails[0]

        # Try single email field
        email = lead.get("email", "")
        if email:
            return email

        return None

    def send_sequence_email(self, lead: Dict, template_name: str, force: bool = False) -> bool:
        """Send a specific email template to a lead"""
        lead_id = lead.get("id")
        email = self.get_email_for_lead(lead)

        if not email:
            print(f"⚠️ No email for lead {lead_id}")
            return False

        # Check if already sent
        if not force and self.logger.was_sent(lead_id, template_name):
            return True

        # Get and personalize template
        template = TemplateLibrary.get_by_name(template_name)
        if not template:
            print(f"⚠️ Template {template_name} not found")
            return False

        subject, body = self.personalizer.fill_template(template, lead)

        # Send email
        success = self.sender.send(email, subject, body)

        # Log attempt
        self.logger.log_email(lead_id, template_name, email, success)

        if success:
            print(f"✅ Sent {template_name} to {email}")
        else:
            print(f"❌ Failed to send {template_name} to {email}")

        return success

    def process_sequences(self) -> Dict:
        """Process all email sequences (called daily)"""
        print("=" * 60)
        print("📧 Processing Email Sequences")
        print("=" * 60)

        leads = self.leads.load()
        now = datetime.now()
        stats = {
            "day_0": 0, "day_3": 0, "day_7": 0,
            "proposals": 0, "hot_leads": 0, "errors": 0
        }

        for lead in leads:
            lead_id = lead.get("id")
            status = lead.get("status", "NEW")

            try:
                # Check email history
                email_log = self.logger._load(self.logger.email_log_file).get(lead_id, [])

                if status == "NEW":
                    # Send Day 0 email
                    if self.get_email_for_lead(lead):
                        success = self.send_sequence_email(lead, "day_0")
                        if success:
                            self.leads.update_status(lead_id, "CONTACTED")
                            stats["day_0"] += 1

                elif status == "CONTACTED" and email_log:
                    # Check last email
                    last_email = max(email_log, key=lambda x: x.get("sent_at", ""))
                    last_sent = datetime.fromisoformat(last_email.get("sent_at", now.isoformat()))
                    days_since = (now - last_sent).days
                    templates_sent = {e.get("template") for e in email_log}

                    # Day 3 follow-up
                    if days_since >= 3 and "day_0" in templates_sent and "day_3" not in templates_sent:
                        success = self.send_sequence_email(lead, "day_3")
                        if success:
                            stats["day_3"] += 1

                    # Day 7 break-up
                    elif days_since >= 7 and "day_3" in templates_sent and "day_7" not in templates_sent:
                        success = self.send_sequence_email(lead, "day_7")
                        if success:
                            stats["day_7"] += 1

                elif status == "PROPOSAL_SENT":
                    # Check for proposal follow-up
                    activities = lead.get("activities", [])
                    for activity in activities:
                        if activity.get("type") == "proposal_sent":
                            sent_time = datetime.fromisoformat(activity.get("at", now.isoformat()))
                            if (now - sent_time).days >= 1:
                                if not self.logger.was_sent(lead_id, "proposal_followup"):
                                    success = self.send_sequence_email(lead, "proposal_followup")
                                    if success:
                                        stats["proposals"] += 1

                elif status == "HOT_LEAD":
                    # Send hot lead email
                    if not self.logger.was_sent(lead_id, "hot_lead"):
                        success = self.send_sequence_email(lead, "hot_lead")
                        if success:
                            stats["hot_leads"] += 1

            except Exception as e:
                print(f"❌ Error processing lead {lead_id}: {e}")
                stats["errors"] += 1

        print(f"\n📊 Sequence Results:")
        print(f"   Day 0 (Initial): {stats['day_0']}")
        print(f"   Day 3 (Follow-up): {stats['day_3']}")
        print(f"   Day 7 (Break-up): {stats['day_7']}")
        print(f"   Hot Leads: {stats['hot_leads']}")
        print(f"   Proposal Follow-ups: {stats['proposals']}")

        return stats

    def send_deal_won_email(self, lead_id: str) -> bool:
        """Send onboarding email when deal is won"""
        lead = self.leads.get_by_id(lead_id)
        if not lead:
            print(f"⚠️ Lead {lead_id} not found")
            return False

        success = self.send_sequence_email(lead, "deal_won", force=True)
        if success:
            self.leads.update_status(lead_id, "CLOSED_WON")
            print(f"✅ Onboarding email sent to {lead.get('company', 'client')}")

        return success

    def mark_hot_lead(self, lead_id: str):
        """Mark a lead as hot and send immediate email"""
        self.leads.update_status(lead_id, "HOT_LEAD")
        lead = self.leads.get_by_id(lead_id)
        if lead:
            self.send_sequence_email(lead, "hot_lead")


# Convenience functions for scheduler
def run_email_sequences() -> Dict:
    """Run daily email sequences - called by scheduler"""
    outreach = UnifiedOutreach()
    return outreach.process_sequences()


def send_deal_won_email(lead_id: str) -> bool:
    """Send deal won email"""
    outreach = UnifiedOutreach()
    return outreach.send_deal_won_email(lead_id)


def mark_hot_lead(lead_id: str):
    """Mark lead as hot"""
    outreach = UnifiedOutreach()
    outreach.mark_hot_lead(lead_id)


if __name__ == "__main__":
    result = run_email_sequences()
    print(f"\nTotal emails sent: {sum(v for k, v in result.items() if k != 'errors')}")
