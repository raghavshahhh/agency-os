#!/usr/bin/env python3
"""
RAGSPRO Auto Outreach - Send emails to verified leads
Automated follow-ups + Response tracking
"""

import json
import time
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_DIR, GMAIL_USER, GMAIL_APP_PASSWORD

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = GMAIL_USER
SENDER_PASSWORD = GMAIL_APP_PASSWORD

OUTREACH_FILE = DATA_DIR / "outreach_targets.json"
SENT_LOG_FILE = DATA_DIR / "sent_emails.json"
FOLLOWUP_FILE = DATA_DIR / "followups.json"


def load_targets():
    """Load outreach targets"""
    if not OUTREACH_FILE.exists():
        print("❌ No targets found. Run linkedin_outreach.py first")
        return []

    with open(OUTREACH_FILE, 'r') as f:
        return json.load(f)


def load_sent_log():
    """Load sent email log"""
    if SENT_LOG_FILE.exists():
        with open(SENT_LOG_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_sent_log(log):
    """Save sent email log"""
    with open(SENT_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)


def send_email_smtp(to_email, subject, body, is_html=False):
    """Send email using Gmail SMTP"""
    try:
        # Clean password (remove spaces if present)
        password = SENDER_PASSWORD.replace(" ", "") if SENDER_PASSWORD else ""
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, password)

            msg = MIMEMultipart('alternative')
            # Show as "Raghav | RAGS Pro AI Agency" but send from Gmail
            msg['From'] = f"Raghav | RAGS Pro <{SENDER_EMAIL}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)


def send_email_resend(to_email, subject, body):
    """Send email using Resend API (better deliverability)"""
    import os
    import requests

    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key:
        return False, "Resend API key not found"

    try:
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Use verified ragspro.com domain
        payload = {
            "from": "Raghav Shah <raghav@ragspro.com>",
            "to": [to_email],
            "subject": subject,
            "text": body,
            "reply_to": "ragsproai@gmail.com"
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            return True, resp.json().get('id', 'sent')
        else:
            return False, f"Resend error: {resp.text}"
    except Exception as e:
        return False, str(e)


def guess_email_patterns(name, company, domain):
    """Guess email patterns for decision makers"""
    if not name or not domain:
        return []

    # Clean name
    name_parts = name.lower().split()
    if len(name_parts) < 1:
        return []

    first = name_parts[0]
    last = name_parts[-1] if len(name_parts) > 1 else ""
    first_initial = first[0] if first else ""
    last_initial = last[0] if last else ""

    patterns = [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{first}_{last}@{domain}",
        f"{first_initial}{last}@{domain}",
        f"{first}.{last_initial}@{domain}",
        f"{first}{last_initial}@{domain}",
        f"{last}@{domain}",
        "info@" + domain,
        "contact@" + domain,
        "hello@" + domain,
        "support@" + domain,
        "sales@" + domain,
        "business@" + domain,
    ]

    return list(set(patterns))


def verify_email_hunter(email):
    """Verify email using Hunter.io API"""
    import os
    import requests

    api_key = os.getenv("HUNTER_API_KEY", "")
    if not api_key:
        return None

    try:
        url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={api_key}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('data', {}).get('status')  # valid, invalid, accept_all, etc.
    except:
        pass
    return None


def get_email_subject(industry):
    """Get industry-specific subject lines"""
    subjects = {
        "Real Estate": [
            "Quick question about lead response time",
            "AI chatbot for property inquiries - 10 min demo?",
            "Automating property lead qualification"
        ],
        "Healthcare": [
            "Reducing no-shows at your clinic",
            "AI assistant for appointment booking",
            "Quick question about patient queries"
        ],
        "E-commerce": [
            "Automating order tracking queries",
            "AI chatbot for customer support",
            "Reducing support tickets by 70%"
        ],
        "Retail": [
            "WhatsApp automation for customer queries",
            "AI chatbot for product inquiries",
            "Quick question about customer support"
        ],
        "Logistics": [
            "Automating delivery tracking",
            "AI assistant for shipment queries",
            "Reducing support calls by 60%"
        ],
        "Fintech": [
            "AI chatbot for customer onboarding",
            "Automating repetitive queries",
            "Quick question about support volume"
        ],
        "Edtech": [
            "AI for student onboarding",
            "Automating course queries",
            "Chatbot for student support"
        ],
        "default": [
            "Quick question about AI automation",
            "10-min chat about chatbots?",
            "Automating customer queries"
        ]
    }

    import random
    return random.choice(subjects.get(industry, subjects["default"]))


def verify_email_format(email):
    """Basic email format validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def verify_email_exists(email):
    """Verify email exists using Hunter.io (if API key available)"""
    import os
    api_key = os.getenv("HUNTER_API_KEY", "")
    if not api_key or api_key == "YOUR_HUNTER_API_KEY":
        return None  # Skip verification if no API key

    try:
        url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={api_key}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            status = data.get('data', {}).get('status')
            score = data.get('data', {}).get('score', 0)
            # Only return valid if status is valid and score > 70
            return status == "valid" and score > 70
    except:
        pass
    return None


def send_outreach_email(target, dry_run=True):
    """Send personalized outreach email"""
    company = target['name']
    industry = target['industry']
    message = target['outreach_message']
    website = target.get('website', '')

    # Try to find decision maker email
    decision_maker = target.get('decision_maker', '')
    dm_name = decision_maker.split('/')[0] if '/' in decision_maker else decision_maker

    # Guess emails
    emails = []
    if website:
        domain = website.replace('https://', '').replace('http://', '').split('/')[0]
        emails = guess_email_patterns(dm_name, company, domain)

    if not emails:
        print(f"⚠️ No email found for {company}")
        return False

    # Validate emails before using
    valid_emails = []
    for email in emails[:5]:  # Check first 5
        if verify_email_format(email):
            # Try to verify existence (if Hunter API available)
            exists = verify_email_exists(email)
            if exists is None or exists:  # If no API key or valid
                valid_emails.append(email)

    if not valid_emails:
        print(f"❌ No valid emails found for {company}")
        print(f"   Guessed: {emails[:3]}")
        print(f"   Suggestion: Use LinkedIn instead - {target.get('linkedin_search', 'N/A')}")
        return False

    to_email = valid_emails[0]

    # Verify warning
    if "@gmail.com" in to_email or "@yahoo.com" in to_email:
        print(f"⚠️ Warning: {to_email} looks like a personal email, not corporate")

    # Get subject
    subject = get_email_subject(industry)

    # Personalize message (signature already included in outreach_targets.json)
    body = message.replace("[Name]", dm_name.split()[0] if dm_name else "there")

    print(f"\n📧 To: {to_email}")
    print(f"📨 Subject: {subject}")
    print(f"🏢 Company: {company}")
    print("-" * 50)

    if dry_run:
        print("\n[DRY RUN - Email not sent]")
        print(f"Body preview:\n{body[:200]}...")
        return True

    # Send via Resend with professional signature
    success, result = send_email_resend(to_email, subject, body)

    if success:
        print(f"✅ Email sent! ID: {result}")

        # Log the sent email
        sent_log = load_sent_log()
        sent_log[to_email] = {
            "company": company,
            "sent_at": datetime.now().isoformat(),
            "subject": subject,
            "email_id": result,
            "status": "sent"
        }
        save_sent_log(sent_log)

        # Update target status
        target['status'] = 'CONTACTED'
        target['contacted_at'] = datetime.now().isoformat()
        target['email_used'] = to_email

        return True
    else:
        print(f"❌ Failed: {result}")
        return False


def send_follow_up(email, days_after=3):
    """Send follow-up email"""
    sent_log = load_sent_log()

    if email not in sent_log:
        print(f"⚠️ No original email found for {email}")
        return False

    original = sent_log[email]
    sent_date = datetime.fromisoformat(original['sent_at'])

    if datetime.now() - sent_date < timedelta(days=days_after):
        print(f"⏳ Too early for follow-up to {email}")
        return False

    # Follow-up message
    subject = f"Re: {original['subject']}"
    body = f"""Hi,

Quick follow-up on my email below.

Worth a brief chat this week?

Best,
Raghav
RAGS Pro

---
{original.get('original_body', 'Original message')}
"""

    success, result = send_email_resend(email, subject, body)
    if success:
        print(f"✅ Follow-up sent to {email}")
        sent_log[email]['follow_up_sent'] = datetime.now().isoformat()
        save_sent_log(sent_log)
        return True

    return False


def run_outreach_campaign(dry_run=True, max_emails=5):
    """Run full outreach campaign"""
    print("=" * 70)
    print("🚀 RAGSPRO AUTO OUTREACH CAMPAIGN")
    print("=" * 70)
    print(f"Mode: {'DRY RUN (test)' if dry_run else 'LIVE (sending real emails)'}")
    print(f"Max emails: {max_emails}")
    print("=" * 70)

    targets = load_targets()
    if not targets:
        return

    # Filter high priority targets not yet contacted
    high_priority = [t for t in targets
                     if t.get('priority') == 'HIGH'
                     and t.get('status') != 'CONTACTED']

    print(f"\n📊 Found {len(high_priority)} high-priority targets")

    sent_count = 0
    for target in high_priority[:max_emails]:
        if send_outreach_email(target, dry_run=dry_run):
            sent_count += 1

        if not dry_run:
            time.sleep(2)  # Rate limiting

    print("\n" + "=" * 70)
    print(f"✅ Campaign complete: {sent_count} emails {'simulated' if dry_run else 'sent'}")
    print("=" * 70)

    if dry_run:
        print("\n💡 To send real emails, run with: python auto_outreach.py --live")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='RAGSPRO Auto Outreach')
    parser.add_argument('--live', action='store_true', help='Send real emails')
    parser.add_argument('--max', type=int, default=5, help='Max emails to send')
    parser.add_argument('--follow-up', action='store_true', help='Send follow-ups')
    args = parser.parse_args()

    if args.follow_up:
        print("Sending follow-ups...")
        # Logic for follow-ups
    else:
        run_outreach_campaign(dry_run=not args.live, max_emails=args.max)


if __name__ == "__main__":
    main()
