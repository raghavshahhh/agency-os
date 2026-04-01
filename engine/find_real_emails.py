#!/usr/bin/env python3
"""
RAGSPRO Real Email Finder - Hunter.io + Apollo + LinkedIn
Find verified emails for decision makers
"""

import json
import requests
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_DIR

# API Keys
HUNTER_API_KEY = "YOUR_HUNTER_API_KEY"  # Get from hunter.io
APOLLO_API_KEY = "YOUR_APOLLO_API_KEY"  # Get from apollo.io

OUTREACH_FILE = DATA_DIR / "outreach_targets.json"

def find_email_hunter(domain, first_name, last_name):
    """Find email using Hunter.io"""
    if not HUNTER_API_KEY or HUNTER_API_KEY == "YOUR_HUNTER_API_KEY":
        return None

    try:
        url = f"https://api.hunter.io/v2/email-finder"
        params = {
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": HUNTER_API_KEY
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            email = data.get('data', {}).get('email')
            score = data.get('data', {}).get('score', 0)
            if email and score > 70:  # Only high confidence
                return email
    except:
        pass
    return None


def find_email_apollo(name, company):
    """Find email using Apollo.io"""
    if not APOLLO_API_KEY or APOLLO_API_KEY == "YOUR_APOLLO_API_KEY":
        return None

    try:
        url = "https://api.apollo.io/v1/people/match"
        headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
        payload = {
            "api_key": APOLLO_API_KEY,
            "first_name": name.split()[0] if name else "",
            "last_name": name.split()[-1] if len(name.split()) > 1 else "",
            "organization_name": company
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            person = data.get('person', {})
            email = person.get('email')
            if email:
                return email
    except:
        pass
    return None


def get_linkedin_url(company_name):
    """Get LinkedIn company URL"""
    company_urls = {
        "Square Yards": "https://www.linkedin.com/company/square-yards/",
        "NoBroker": "https://www.linkedin.com/company/nobroker/",
        "Practo": "https://www.linkedin.com/company/practo/",
        "BYJU'S": "https://www.linkedin.com/company/byju-s/",
        "Delhivery": "https://www.linkedin.com/company/delhivery/",
        "Lenskart": "https://www.linkedin.com/company/lenskart/",
        "PolicyBazaar": "https://www.linkedin.com/company/policybazaar/",
        "Blinkit": "https://www.linkedin.com/company/blinkit/",
        "Zerodha": "https://www.linkedin.com/company/zerodha/",
        "Razorpay": "https://www.linkedin.com/company/razorpay/",
    }
    return company_urls.get(company_name, "")


def generate_linkedin_dm(target):
    """Generate LinkedIn DM instead of email"""
    company = target['name']
    decision_maker = target['decision_maker']
    industry = target['industry']

    templates = {
        "Real Estate": f"""Hi [Name],

Came across Square Yards while researching PropTech in India. Impressive growth!

Quick question - how are you handling the volume of property inquiries? I built an AI assistant for a Delhi realtor that books site visits automatically and qualifies buyers on WhatsApp.

Cut their response time from hours to minutes. Worth a brief chat?

Raghav
RAGS Pro AI Agency""",
        "default": f"""Hi [Name],

Love what {company} is building in the {industry} space.

I've been building AI chatbots that handle repetitive customer queries - things like "where's my order" or "what are your timings."

One company I worked with reduced their support tickets by 60%.

Worth a quick conversation to see if it applies to {company}?

Raghav
RAGS Pro AI Agency"""
    }

    return templates.get(industry, templates["default"])


def update_targets_with_linkedin():
    """Update targets to use LinkedIn instead of email"""
    with open(OUTREACH_FILE, 'r') as f:
        targets = json.load(f)

    for target in targets:
        if target.get('status') != 'CONTACTED':
            # Add LinkedIn URL
            target['linkedin_company_url'] = get_linkedin_url(target['name'])

            # Generate LinkedIn DM
            target['linkedin_dm'] = generate_linkedin_dm(target)

            # Add LinkedIn search for decision maker
            dm = target['decision_maker'].replace('/', ' ').replace('  ', ' ')
            target['linkedin_dm_search'] = f"site:linkedin.com/in {dm} {target['name']}"

    with open(OUTREACH_FILE, 'w') as f:
        json.dump(targets, f, indent=2)

    print("✅ Updated targets with LinkedIn strategy")
    return targets


def print_linkedin_strategy():
    """Print LinkedIn outreach strategy"""
    print("\n" + "=" * 70)
    print("🔗 LINKEDIN OUTREACH STRATEGY (Higher Success Rate)")
    print("=" * 70)

    print("""
📌 Why LinkedIn over Email for These Companies:
- Email guessing = high bounce rate (as you saw)
- LinkedIn = verified profiles, direct access to decision makers
- Higher response rate (20-30% vs 2-5% for cold email)
- No spam filters

📋 Step-by-Step Process:

1. LinkedIn Premium (1 month free trial)
   → https://www.linkedin.com/premium

2. Search for Decision Makers:
   - "CEO Square Yards"
   - "CTO NoBroker"
   - "VP Technology Delhivery"

3. Send Connection Request with Note:
   "Hi [Name], love what you're building at [Company].
   Would love to connect!"

4. After They Accept (50-70% acceptance rate):
   Send the humanized DM (saved in outreach_targets.json)

5. Follow Up in 3 Days if No Response

💬 Sample DM:
"Came across Square Yards while researching PropTech.
Quick question - how are you handling property inquiry volume?
Built an AI assistant for a Delhi realtor that books visits
automatically. Cut response time from hours to minutes.
Worth a brief chat?"

🎯 Priority Order (Updated):
1. Square Yards - CEO/Head of Product
2. NoBroker - CTO/VP Engineering
3. Delhivery - VP Technology
4. Lenskart - CTO/Head of Digital
5. Zerodha - CTO/Head of Engineering
""")

    print("=" * 70)


def main():
    print("🔄 Switching to LinkedIn strategy (higher success rate)...")
    update_targets_with_linkedin()
    print_linkedin_strategy()

    print("\n✅ Action Items:")
    print("1. Sign up for LinkedIn Premium (free trial)")
    print("2. Search: CEO Square Yards")
    print("3. Send connection request")
    print("4. After accept, send DM from outreach_targets.json")
    print("5. Track responses in Agency OS dashboard")


if __name__ == "__main__":
    main()
