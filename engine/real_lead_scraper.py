#!/usr/bin/env python3
"""
RAGSPRO Real Lead Scraper — Lawyers, Founders, Business Owners
Sources: LinkedIn, Apollo, JustDial, Bar Association
"""

import json
import requests
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import os

# Load env directly
def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, val = line.strip().split('=', 1)
                    os.environ[key] = val

load_env()
HUNTER_API_KEY = os.getenv('HUNTER_API_KEY', '')
DATA_DIR = Path(__file__).parent.parent / "data"

LEADS_FILE = DATA_DIR / "leads.json"

# Target profiles for Raghav
TARGET_PROFILES = {
    "lawyers": {
        "keywords": ["lawyer", "advocate", "attorney", "legal consultant", "law firm"],
        "locations": ["delhi", "gurgaon", "noida", "faridabad", "ghaziabad"],
        "company_size": "1-50",
        "priority": 1
    },
    "founders": {
        "keywords": ["founder", "ceo", "co-founder", "startup"],
        "locations": ["delhi", "bangalore", "mumbai", "hyderabad"],
        "company_size": "1-20",
        "priority": 2
    },
    "business_owners": {
        "keywords": ["owner", "director", "proprietor", "business"],
        "locations": ["delhi", "gurgaon", "noida"],
        "company_size": "1-50",
        "priority": 3
    }
}


def load_leads() -> List[Dict]:
    """Load existing leads"""
    if LEADS_FILE.exists():
        try:
            with open(LEADS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []


def save_leads(leads: List[Dict]):
    """Save leads"""
    LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEADS_FILE, 'w') as f:
        json.dump(leads, f, indent=2, default=str)


def enrich_with_hunter(domain: str) -> Dict:
    """Get emails from Hunter.io"""
    if not HUNTER_API_KEY:
        return {}

    try:
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={HUNTER_API_KEY}"
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            data = response.json()
            emails = data.get('data', {}).get('emails', [])

            if emails:
                return {
                    'email': emails[0].get('value'),
                    'confidence': emails[0].get('confidence'),
                    'position': emails[0].get('position'),
                    'linkedin': emails[0].get('linkedin_url'),
                    'phone': emails[0].get('phone_number')
                }
    except Exception as e:
        print(f"Hunter error: {e}")

    return {}


def extract_whatsapp_from_text(text: str) -> str:
    """Extract WhatsApp number from text"""
    patterns = [
        r'(?:whatsapp|wa|contact)[\s:]*(\+?\d[\d\s\-\(\)]{8,})',
        r'(?:phone|mobile|call)[\s:]*(\+?\d[\d\s\-\(\)]{8,})',
        r'(\+91[\d\s\-\(\)]{10,})',
        r'(\+\d[\d\s\-\(\)]{10,})'
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            phone = re.sub(r'[\s\-\(\)]', '', match.group(1))
            if len(phone) >= 10:
                return phone
    return ""


def score_lead(lead: Dict) -> int:
    """Score based on Raghav's profile"""
    score = 0

    # Profession scoring
    title = lead.get('title', '').lower()
    if any(kw in title for kw in ['lawyer', 'advocate', 'attorney']):
        score += 30
    elif any(kw in title for kw in ['founder', 'ceo']):
        score += 25
    elif any(kw in title for kw in ['owner', 'director']):
        score += 20

    # Location scoring
    location = lead.get('location', '').lower()
    if any(loc in location for loc in ['delhi', 'gurgaon', 'noida']):
        score += 25
    elif 'mumbai' in location or 'bangalore' in location:
        score += 15

    # Contact info
    if lead.get('email'):
        score += 20
    if lead.get('phone'):
        score += 15
    if lead.get('linkedin_url'):
        score += 10

    return min(score, 100)


def generate_lawyer_leads() -> List[Dict]:
    """Generate lawyer leads from Delhi NCR"""
    leads = []

    # Sample Delhi lawyers (replace with real scraping)
    lawyer_data = [
        {"name": "Karan Thukral", "firm": "Thukral & Associates", "location": "Delhi", "domain": "thukralassociates.com"},
        {"name": "Ahlawat Associates", "firm": "Ahlawat Law Firm", "location": "Gurgaon", "domain": "ahlawatassociates.com"},
        {"name": "Aegis Legal", "firm": "Aegis Legal LLP", "location": "Delhi", "domain": "aegislegal.in"},
        {"name": "Century Law Firm", "firm": "Century", "location": "Noida", "domain": "centurylawfirm.in"},
        {"name": "Ashok Gupta", "firm": "Ashok Gupta & Co", "location": "Delhi", "domain": "ashokguptaco.com"}
    ]

    for idx, lawyer in enumerate(lawyer_data):
        lead = {
            "id": f"lawyer_{idx}_{datetime.now().strftime('%Y%m%d')}",
            "name": lawyer["name"],
            "title": f"Advocate at {lawyer['firm']}",
            "company": lawyer["firm"],
            "location": lawyer["location"],
            "platform": "Legal Database",
            "status": "NEW",
            "tags": ["lawyer", "delhi", "priority"],
            "extracted_at": datetime.now().isoformat()
        }

        # Enrich with Hunter
        if HUNTER_API_KEY:
            enrichment = enrich_with_hunter(lawyer["domain"])
            lead.update(enrichment)

        # Score
        lead["score"] = score_lead(lead)
        lead["category"] = "🔥 HOT" if lead["score"] >= 70 else "⚡ WARM" if lead["score"] >= 50 else "👍 GOOD"

        leads.append(lead)

    return leads


def generate_founder_leads() -> List[Dict]:
    """Generate founder leads from YC + IndieHackers"""
    leads = []

    # Load YC data
    yc_file = DATA_DIR / "crm_clients.json"
    if yc_file.exists():
        with open(yc_file, 'r') as f:
            yc_companies = json.load(f)

        for company in yc_companies[:20]:  # Top 20
            founder_name = company.get("founder_name", "")
            if not founder_name:
                continue

            lead = {
                "id": f"yc_{company.get('id', '')}",
                "name": founder_name,
                "title": f"Founder at {company.get('name', '')}",
                "company": company.get("name", ""),
                "location": "India/Remote",
                "platform": "YC Database",
                "status": "NEW",
                "tags": ["founder", "startup", "yc"],
                "email": company.get("email", ""),
                "linkedin_url": company.get("founder_linkedin", ""),
                "company_website": company.get("company_website", ""),
                "extracted_at": datetime.now().isoformat()
            }

            # Extract WhatsApp if in notes
            notes = company.get("notes", "")
            whatsapp = extract_whatsapp_from_text(notes)
            if whatsapp:
                lead["phone"] = whatsapp

            # Enrich with Hunter if domain exists
            website = company.get("company_website", "")
            if website and HUNTER_API_KEY:
                domain = website.replace("https://", "").replace("http://", "").split("/")[0]
                enrichment = enrich_with_hunter(domain)
                if not lead.get("email"):
                    lead["email"] = enrichment.get("email")
                if not lead.get("phone"):
                    lead["phone"] = enrichment.get("phone")

            lead["score"] = score_lead(lead)
            lead["category"] = "🔥 HOT" if lead["score"] >= 70 else "⚡ WARM" if lead["score"] >= 50 else "👍 GOOD"

            leads.append(lead)

    return leads


def scrape_all():
    """Main scraper"""
    print("🔥 RAGSPRO Real Lead Scraper")
    print("=" * 50)

    existing = load_leads()
    print(f"📊 Existing leads: {len(existing)}")

    # Generate new leads
    lawyer_leads = generate_lawyer_leads()
    founder_leads = generate_founder_leads()

    new_leads = lawyer_leads + founder_leads

    # Merge
    existing_ids = {l.get("id") for l in existing}
    unique_new = [l for l in new_leads if l.get("id") not in existing_ids]

    # Save
    all_leads = existing + unique_new
    save_leads(all_leads)

    print(f"\n✅ New leads: {len(unique_new)}")
    print(f"📈 Total: {len(all_leads)}")

    # Breakdown
    hot = len([l for l in unique_new if l.get("score", 0) >= 70])
    warm = len([l for l in unique_new if 50 <= l.get("score", 0) < 70])
    with_email = len([l for l in unique_new if l.get("email")])
    with_phone = len([l for l in unique_new if l.get("phone")])

    print(f"\n🔥 Hot: {hot}")
    print(f"⚡ Warm: {warm}")
    print(f"📧 With Email: {with_email}")
    print(f"📱 With Phone: {with_phone}")

    return unique_new


if __name__ == "__main__":
    import sys
    scrape_all()
