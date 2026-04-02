#!/usr/bin/env python3
"""
RAGSPRO Email Automation System — Automated email sequences
Day 0: Initial, Day 3: Follow-up, Day 7: Break-up
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, RESEND_API_KEY, AGENCY_NAME, GMAIL_USER, GMAIL_APP_PASSWORD

LEADS_FILE = DATA_DIR / "leads.json"
EMAIL_LOG_FILE = DATA_DIR / "email_automation_log.json"
SEQUENCE_FILE = DATA_DIR / "email_sequences.json"

# Email templates
EMAIL_TEMPLATES = {
    "day_0": {
        "subject": "quick question",
        "body": """Hi {first_name},

Saw {company} - congrats on the recent growth.

Quick question: Are you still handling {pain_point} manually?

We just helped a similar {industry} company automate their lead generation and they saw 40% more qualified leads in 30 days.

Worth a quick look?

Raghav
{agency_name}
{agency_url}"""
    },
    "day_3": {
        "subject": "Re: quick question",
        "body": """Hey {first_name},

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
    },
    "day_7": {
        "subject": "should I close the loop?",
        "body": """{first_name},

No worries if timing's off - should I close this out for now?

Or if {pain_point} is still a thing, here's a 5-min Loom showing exactly how we'd approach it:

https://loom.com/share/example

Either way, no hard feelings!

Raghav"""
    },
    "proposal_followup": {
        "subject": "Quick follow-up on proposal",
        "body": """Hi {first_name},

Just floating this to the top of your inbox in case you had a chance to review the proposal I sent.

Happy to answer any questions or jump on a quick call to discuss.

Best,
Raghav"""
    },
    "deal_won": {
        "subject": "Welcome to {agency_name} - Let's Get Started!",
        "body": """Hi {first_name},

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
    }
}

def load_leads():
    """Load all leads"""
    if LEADS_FILE.exists():
        with open(LEADS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_leads(leads):
    """Save leads"""
    with open(LEADS_FILE, 'w') as f:
        json.dump(leads, f, indent=2)

def load_email_log():
    """Load email automation log"""
    if EMAIL_LOG_FILE.exists():
        with open(EMAIL_LOG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_email_log(log):
    """Save email automation log"""
    with open(EMAIL_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

def was_email_sent(lead_id, template_name):
    """Check if email was already sent"""
    log = load_email_log()
    lead_log = log.get(lead_id, [])
    return any(entry.get("template") == template_name for entry in lead_log)

def log_email_sent(lead_id, template_name, email, status):
    """Log sent email"""
    log = load_email_log()
    if lead_id not in log:
        log[lead_id] = []

    log[lead_id].append({
        "template": template_name,
        "sent_at": datetime.now().isoformat(),
        "email": email,
        "status": status
    })
    save_email_log(log)

def send_email_resend(to_email, subject, body):
    """Send email using Resend API"""
    if not RESEND_API_KEY:
        print(f"⚠️ RESEND_API_KEY not set, skipping email to {to_email}")
        return False

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": f"Raghav at RAGSPRO <{GMAIL_USER or 'raghav@ragspro.com'}>",
                "to": [to_email],
                "subject": subject,
                "text": body
            },
            timeout=30
        )

        if response.status_code in [200, 201, 202]:
            return True
        else:
            print(f"❌ Email failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def personalize_template(template_name, lead):
    """Fill template with lead data"""
    template = EMAIL_TEMPLATES.get(template_name, {})
    subject = template.get("subject", "")
    body = template.get("body", "")

    # Extract first name
    name = lead.get("name", "")
    first_name = name.split()[0] if name else "there"

    # Determine pain point based on industry/title
    industry = lead.get("industry", "business")
    title = lead.get("title", "").lower()

    if "developer" in title or "software" in title or "tech" in title:
        pain_point = "lead generation"
    elif "marketing" in title or "sales" in title:
        pain_point = "outreach and follow-ups"
    elif "operations" in title or "automation" in title:
        pain_point = "manual workflows"
    else:
        pain_point = "manual processes"

    # Fill template
    subject = subject.format(
        agency_name=AGENCY_NAME
    )

    body = body.format(
        first_name=first_name,
        company=lead.get("company", "your company"),
        industry=industry,
        pain_point=pain_point,
        agency_name=AGENCY_NAME,
        agency_url="https://ragspro.com",
        timeline="2-3 weeks"
    )

    return subject, body

def send_sequence_email(lead, template_name):
    """Send a specific sequence email to a lead"""
    email = lead.get("contact", {}).get("emails", [])
    if not email:
        email = [lead.get("email", "")]

    if not email or not email[0]:
        print(f"⚠️ No email for lead {lead.get('id')}")
        return False

    # Check if already sent
    if was_email_sent(lead.get("id"), template_name):
        return True  # Already sent, skip

    # Personalize and send
    subject, body = personalize_template(template_name, lead)
    success = send_email_resend(email[0], subject, body)

    # Log the attempt
    log_email_sent(lead.get("id"), template_name, email[0], "sent" if success else "failed")

    return success

def update_lead_status(lead, new_status):
    """Update lead status"""
    leads = load_leads()
    for l in leads:
        if l.get("id") == lead.get("id"):
            l["status"] = new_status
            l["last_updated"] = datetime.now().isoformat()
            break
    save_leads(leads)

def run_email_sequences():
    """Run daily email sequence automation"""
    print("=" * 60)
    print("📧 RAGSPRO Email Sequence Automation")
    print("=" * 60)

    leads = load_leads()
    now = datetime.now()
    stats = {"day_0": 0, "day_3": 0, "day_7": 0, "proposals": 0}

    for lead in leads:
        # Get when lead was first contacted
        email_log = load_email_log().get(lead.get("id"), [])

        if not email_log:
            # New lead - send Day 0 email
            if lead.get("status") == "NEW" and lead.get("contact", {}).get("emails"):
                success = send_sequence_email(lead, "day_0")
                if success:
                    update_lead_status(lead, "CONTACTED")
                    stats["day_0"] += 1

        else:
            # Check last email sent
            last_email = max(email_log, key=lambda x: x.get("sent_at", ""))
            last_sent = datetime.fromisoformat(last_email.get("sent_at", now.isoformat()))
            days_since = (now - last_sent).days

            templates_sent = {e.get("template") for e in email_log}

            # Day 3 follow-up
            if days_since >= 3 and "day_0" in templates_sent and "day_3" not in templates_sent:
                if lead.get("status") not in ["REPLIED", "HOT_LEAD", "PROPOSAL_SENT", "CLOSED"]:
                    success = send_sequence_email(lead, "day_3")
                    if success:
                        stats["day_3"] += 1

            # Day 7 break-up
            elif days_since >= 4 and "day_3" in templates_sent and "day_7" not in templates_sent:
                if lead.get("status") not in ["REPLIED", "HOT_LEAD", "PROPOSAL_SENT", "CLOSED"]:
                    success = send_sequence_email(lead, "day_7")
                    if success:
                        stats["day_7"] += 1

    # Proposal follow-ups
    for lead in leads:
        if lead.get("status") == "PROPOSAL_SENT":
            # Check if proposal was sent 24h ago
            activities = lead.get("activities", [])
            for activity in activities:
                if activity.get("type") == "proposal_sent":
                    sent_time = datetime.fromisoformat(activity.get("at", now.isoformat()))
                    if (now - sent_time).days >= 1:
                        if not was_email_sent(lead.get("id"), "proposal_followup"):
                            success = send_sequence_email(lead, "proposal_followup")
                            if success:
                                stats["proposals"] += 1

    print(f"\n📊 Emails Sent:")
    print(f"   Day 0 (Initial): {stats['day_0']}")
    print(f"   Day 3 (Follow-up): {stats['day_3']}")
    print(f"   Day 7 (Break-up): {stats['day_7']}")
    print(f"   Proposal Follow-ups: {stats['proposals']}")

    return stats

def send_deal_won_email(lead):
    """Send onboarding email when deal is won"""
    success = send_sequence_email(lead, "deal_won")
    if success:
        print(f"✅ Onboarding email sent to {lead.get('company', 'client')}")
    return success

if __name__ == "__main__":
    run_email_sequences()
