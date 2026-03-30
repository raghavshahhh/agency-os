#!/usr/bin/env python3
"""
RAGSPRO Outreach Engine — AI scripts + Resend email + communication tracking
"""

import json
import re
import requests
import socket
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    NVIDIA_API_KEY, NVIDIA_API_URL, NVIDIA_MODEL,
    RESEND_API_KEY, DATA_DIR,
    AGENCY_NAME, AGENCY_TAGLINE, SERVICES, CALENDLY_URL
)

OUTREACH_LOG_FILE = DATA_DIR / "outreach_log.json"


# ─── Email Validation ────────────────────────────────────────────────────────

def validate_email_format(email):
    """Check if email has valid format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_email_domain(email):
    """Check if email domain has MX records (basic verification)"""
    if not validate_email_format(email):
        return {"valid": False, "reason": "Invalid format"}

    domain = email.split("@")[1]

    # Known bad domains
    bad_domains = ["example.com", "test.com", "domain.com", "temp-mail.org",
                   "guerrillamail.com", "mailinator.com", "throwaway.email"]
    if domain.lower() in bad_domains:
        return {"valid": False, "reason": "Disposable/fake domain"}

    # Check MX records
    try:
        import subprocess
        result = subprocess.run(
            ["nslookup", "-type=mx", domain],
            capture_output=True, text=True, timeout=5
        )
        has_mx = "mail exchanger" in result.stdout.lower() or "MX" in result.stdout
        if has_mx:
            return {"valid": True, "reason": "MX records found"}
        else:
            return {"valid": False, "reason": "No MX records"}
    except Exception:
        # Can't verify, assume valid format = okay
        return {"valid": True, "reason": "Format valid (MX check skipped)"}


def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return {"valid": False, "formatted": ""}

    # Clean the phone number
    cleaned = re.sub(r'[^\d+]', '', phone)

    # Check various formats
    if re.match(r'^\+91\d{10}$', cleaned):
        return {"valid": True, "formatted": f"+91 {cleaned[3:8]} {cleaned[8:]}", "country": "IN"}
    elif re.match(r'^\+1\d{10}$', cleaned):
        return {"valid": True, "formatted": f"+1 ({cleaned[2:5]}) {cleaned[5:8]}-{cleaned[8:]}", "country": "US"}
    elif re.match(r'^\d{10}$', cleaned):
        return {"valid": True, "formatted": f"{cleaned[:5]} {cleaned[5:]}", "country": "Unknown"}
    elif len(cleaned) >= 10:
        return {"valid": True, "formatted": phone, "country": "Unknown"}

    return {"valid": False, "formatted": phone}


# ─── AI Script Generation ────────────────────────────────────────────────────

def _call_ai(prompt, max_tokens=500):
    """Call NVIDIA NIM API"""
    if not NVIDIA_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": NVIDIA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are a professional outreach specialist for {AGENCY_NAME}. "
                    f"Services: {', '.join(SERVICES)}. "
                    f"Tagline: {AGENCY_TAGLINE}. "
                    "Write concise, personalized, conversion-focused outreach content. "
                    "Never be generic. Always reference the lead's specific need."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"


def generate_cold_email(lead):
    """Generate personalized cold email using AIDA framework"""
    name = lead.get("name", "there")
    title = lead.get("title", "")
    requirement = lead.get("requirement", "")[:400]
    platform = lead.get("platform", "")

    # Detect industry/pain points from title
    industry_hints = []
    title_lower = title.lower()
    if any(word in title_lower for word in ["saas", "platform", "app", "web app"]):
        industry_hints.append("SaaS/MVP development")
    if any(word in title_lower for word in ["chatbot", "ai", "automation", "bot"]):
        industry_hints.append("AI chatbots and automation")
    if any(word in title_lower for word in ["website", "web", "landing page", "site"]):
        industry_hints.append("Web development")
    if any(word in title_lower for word in ["startup", "mvp", "build", "create"]):
        industry_hints.append("Startup/MVP builds")

    industry_context = ", ".join(industry_hints) if industry_hints else "custom software development"

    prompt = f"""Write a professional cold email using the AIDA framework (Attention, Interest, Desire, Action).

LEAD CONTEXT:
- Name: {name}
- Posted: {title}
- Need: {requirement}
- Found on: {platform}
- Likely Industry: {industry_context}

EMAIL STRUCTURE (AIDA Framework):
1. ATTENTION - Subject line: Curiosity-driven, not clickbait. Reference their specific situation.
2. INTEREST - Opening line: Show you understand their exact need from their post. Be specific.
3. DESIRE - Body: Briefly mention how RAGSPRO solves this exact problem. Include ONE specific relevant case study or result. Make them want to learn more.
4. ACTION - CTA: Single, low-friction next step (book a 15-min call or reply with one question).

TONE GUIDELINES:
- Professional but conversational (like a LinkedIn message)
- No generic fluff like "I hope this email finds you well"
- No aggressive sales language
- Sound like a peer offering help, not a vendor pitching
- Keep under 120 words total

AGENCY INFO:
- Name: {AGENCY_NAME}
- Specialty: AI Chatbots, SaaS Development, Automation
- Calendly: {CALENDLY_URL}

OUTPUT FORMAT:
Subject: [subject line]

[email body - max 4 short paragraphs]

Best regards,
Raghav | {AGENCY_NAME}
📅 Book a call: {CALENDLY_URL}

Write ONLY the email. No explanations or notes."""

    return _call_ai(prompt, max_tokens=500)


def generate_cold_email_followup(lead, previous_emails):
    """Generate strategic follow-up email using value-add approach"""
    name = lead.get("name", "there")
    title = lead.get("title", "")

    prev_summary = "\n".join([f"- Sent on {e.get('sent_at', '')[:10]}: {e.get('subject', 'No subject')}..." for e in previous_emails[:2]])

    prompt = f"""Write a strategic follow-up email for a lead who hasn't responded.

CONTEXT:
- Lead Name: {name}
- Their Original Post: {title}
- Previous Outreach:
{prev_summary}

FOLLOW-UP FRAMEWORK:
1. Subject Line: Use pattern like "Quick thought on [their project]" or "Re: [previous subject]"
2. Opening: Brief reference to previous email (1 sentence max)
3. Value Add: Share ONE of these:
   - A relevant case study/result from similar client
   - A quick insight about their specific need
   - A free resource (audit, checklist, framework)
   - A time-sensitive opportunity
4. Soft CTA: Make it easy to respond (yes/no question or one-click booking)

TONE:
- Assume they missed it (not that they're ignoring you)
- Helpful, not desperate
- Professional confidence
- Under 80 words

AVOID:
- "Just following up"
- "Did you see my email?"
- Multiple CTAs
- Apologizing for emailing

AGENCY INFO:
- Name: {AGENCY_NAME}
- Booking: {CALENDLY_URL}

OUTPUT FORMAT:
Subject: [subject line]

[2-3 short paragraphs max]

Best,
Raghav | {AGENCY_NAME}
📅 {CALENDLY_URL}

Write ONLY the email."""

    return _call_ai(prompt, max_tokens=350)


def generate_call_script(lead):
    """Generate professional call script"""
    name = lead.get("name", "the lead")
    title = lead.get("title", "")
    requirement = lead.get("requirement", "")[:300]
    pain_points = lead.get("pain_points", [])

    prompt = f"""Write a professional cold call script for this lead.

Lead Name: {name}
Their Post: {title}
Requirement: {requirement}
Pain Points: {', '.join(pain_points) if pain_points else 'not identified'}

FORMAT:
[INTRO] - Who you are, why calling (10 sec)
[HOOK] - Reference their specific need (10 sec)
[VALUE] - How {AGENCY_NAME} helps (20 sec)
[QUESTION] - Open-ended question to engage them (10 sec)
[CLOSE] - Suggest next step / book call (10 sec)

[OBJECTION HANDLERS]
- "I'm not interested" → ...
- "Send me details" → ...
- "What's the price?" → ...

RULES:
- Total max 60 seconds speaking time
- Conversational, not robotic
- Reference their exact problem from the post

Write ONLY the script."""

    return _call_ai(prompt, max_tokens=500)


def generate_linkedin_dm(lead):
    """Generate LinkedIn connection message"""
    name = lead.get("name", "")
    title = lead.get("title", "")
    requirement = lead.get("requirement", "")[:200]

    prompt = f"""Write a LinkedIn connection request message.

Lead: {name}
Their Post: {title}
Need: {requirement}

RULES:
- Max 280 characters (LinkedIn limit for connection notes)
- Personal, not corporate
- Reference their specific work/post
- NO selling in the first message, just connect
- End with genuine curiosity

Write ONLY the message text."""

    return _call_ai(prompt, max_tokens=100)


# ─── Resend Email Integration ────────────────────────────────────────────────

def send_email_resend(to_email, subject, body, from_name="Raghav | RAGSPRO"):
    """Send email via Resend API"""
    if not RESEND_API_KEY:
        return {"success": False, "error": "RESEND_API_KEY not set"}

    if not validate_email_format(to_email):
        return {"success": False, "error": f"Invalid email: {to_email}"}

    # Determine from address based on Resend domain
    from_email = f"{from_name} <onboarding@resend.dev>"

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": body
    }

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code in [200, 201]:
            result = response.json()
            return {
                "success": True,
                "resend_id": result.get("id", ""),
                "message": f"Email sent to {to_email}"
            }
        else:
            error_msg = response.json().get("message", response.text)
            return {"success": False, "error": f"Resend API error: {error_msg}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Outreach Log ────────────────────────────────────────────────────────────

def load_outreach_log():
    """Load outreach history"""
    if OUTREACH_LOG_FILE.exists():
        try:
            with open(OUTREACH_LOG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_outreach_log(log):
    """Save outreach history"""
    OUTREACH_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTREACH_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2, default=str)


def log_outreach(lead_id, outreach_type, content, sent_via="manual", to_email="", resend_id=""):
    """Log an outreach action"""
    log = load_outreach_log()

    entry = {
        "id": f"outreach_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "lead_id": lead_id,
        "type": outreach_type,  # email, linkedin_dm, call
        "content": content,
        "sent_via": sent_via,  # resend, manual
        "to_email": to_email,
        "resend_id": resend_id,
        "sent_at": datetime.now().isoformat(),
        "status": "sent"  # sent, opened, replied, bounced
    }

    log.append(entry)
    save_outreach_log(log)
    return entry


def get_lead_outreach_history(lead_id):
    """Get outreach history for a specific lead"""
    log = load_outreach_log()
    return [e for e in log if e.get("lead_id") == lead_id]


def get_outreach_stats():
    """Get overall outreach statistics"""
    log = load_outreach_log()
    return {
        "total_sent": len(log),
        "emails_sent": len([e for e in log if e.get("type") == "email"]),
        "linkedin_dms": len([e for e in log if e.get("type") == "linkedin_dm"]),
        "calls_logged": len([e for e in log if e.get("type") == "call"]),
        "via_resend": len([e for e in log if e.get("sent_via") == "resend"]),
        "replied": len([e for e in log if e.get("status") == "replied"]),
    }


# ─── Parse Email Components ──────────────────────────────────────────────────

def parse_email_content(ai_output):
    """Parse AI-generated email into subject + body"""
    if not ai_output:
        return {"subject": "", "body": ""}

    lines = ai_output.strip().split("\n")
    subject = ""
    body_lines = []

    for i, line in enumerate(lines):
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
        else:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    if not subject and body:
        # First line as subject if no explicit subject
        subject = body.split("\n")[0][:80]

    return {"subject": subject, "body": body}


if __name__ == "__main__":
    print(f"🚀 {AGENCY_NAME} Outreach Engine")
    print("=" * 40)
    print(f"Resend API Key: {'✅ Set' if RESEND_API_KEY else '❌ Missing'}")
    print(f"NVIDIA API Key: {'✅ Set' if NVIDIA_API_KEY else '❌ Missing'}")

    stats = get_outreach_stats()
    print(f"\nOutreach Stats:")
    print(f"  Total Sent: {stats['total_sent']}")
    print(f"  Emails: {stats['emails_sent']}")
    print(f"  LinkedIn DMs: {stats['linkedin_dms']}")
    print(f"  Via Resend: {stats['via_resend']}")
