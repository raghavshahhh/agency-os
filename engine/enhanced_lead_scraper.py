#!/usr/bin/env python3
"""
RAGSPRO Smart Lead Scraper - Only leads with contact info
Extracts emails/LinkedIn from Reddit + LinkedIn lookup
"""

import json
import re
import requests
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from config import DATA_DIR, LEAD_KEYWORDS

LEADS_FILE = DATA_DIR / "leads.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

REDDIT_SOURCES = [
    {"name": "r/forhire", "url": "https://www.reddit.com/r/forhire/new.json?limit=50"},
    {"name": "r/startups", "url": "https://www.reddit.com/r/startups/new.json?limit=30"},
    {"name": "r/webdev", "url": "https://www.reddit.com/r/webdev/search.json?q=hire+me&sort=new&limit=25"},
]


def extract_emails(text):
    """Extract all emails from text"""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    # Filter out common false positives
    valid = [e for e in emails if not any(x in e.lower() for x in ['example.com', 'test.com', 'domain.com'])]
    return list(set(valid))


def extract_linkedin(text):
    """Extract LinkedIn URLs"""
    patterns = [
        r'linkedin\.com/in/[\w-]+',
        r'linkedin\.com/company/[\w-]+',
    ]
    linkedins = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        linkedins.extend(['https://' + m for m in matches])
    return list(set(linkedins))


def extract_phone(text):
    """Extract phone numbers (US/India/Intl)"""
    patterns = [
        r'\+91[\s-]?\d{10}',  # India +91
        r'\+1[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}',  # US +1
        r'\(\d{3}\)[\s-]?\d{3}[\s-]?\d{4}',  # (123) 456-7890
        r'\d{3}[\s-]\d{3}[\s-]\d{4}',  # 123-456-7890
    ]
    phones = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        phones.extend(matches)
    return list(set(phones))


def has_contact_info(text):
    """Check if text has any contact info"""
    return (
        len(extract_emails(text)) > 0 or
        len(extract_linkedin(text)) > 0 or
        len(extract_phone(text)) > 0
    )


def find_company_name(text):
    """Try to extract company/business name"""
    # Look for patterns like "at XYZ" or "from XYZ"
    patterns = [
        r'(?:at|from|with)\s+([A-Z][a-zA-Z0-9\s&]+(?:Inc|LLC|Ltd|Ltd\.|Company|Co\.))',
        r'(?:at|from|with)\s+([A-Z][a-zA-Z0-9\s&]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()[:50]
    return ""


def detect_pain_points(text):
    """Detect pain points from requirement text"""
    pain_points = []
    text_lower = text.lower()

    pain_keywords = {
        "slow response": ["slow", "delay", "time", "waiting", "response time"],
        "manual work": ["manual", "repetitive", "boring", "tedious", "spreadsheet"],
        "cost too high": ["expensive", "costly", "too much", "budget", "affordable"],
        "no technical team": ["no developer", "need developer", "hiring", "team"],
        "losing leads": ["leads", "customers", "missing", "losing"],
        "overwhelmed": ["overwhelm", "too many", "can't handle", "too much"],
    }

    for pain, keywords in pain_keywords.items():
        if any(kw in text_lower for kw in keywords):
            pain_points.append(pain)

    return pain_points[:3]  # Top 3 pain points


def detect_industry(text):
    """Detect industry from text"""
    industries = {
        "SaaS": ["saas", "software", "app", "platform"],
        "E-commerce": ["ecommerce", "shopify", "amazon", "store", "sell"],
        "Agency": ["agency", "marketing", "client"],
        "Real Estate": ["real estate", "property", "realtor"],
        "Healthcare": ["health", "medical", "clinic", "hospital"],
        "Education": ["education", "course", "learning", "training"],
        "Finance": ["finance", "accounting", "bookkeeping", "tax"],
    }

    text_lower = text.lower()
    for industry, keywords in industries.items():
        if any(kw in text_lower for kw in keywords):
            return industry
    return "General"


def process_post(post_data, source_name):
    """Process a Reddit post into a lead with contact info"""
    post = post_data.get("data", {})

    title = post.get("title", "")
    text = post.get("selftext", "") + " " + title
    author = post.get("author", "unknown")
    permalink = post.get("permalink", "")
    created_utc = post.get("created_utc", 0)

    if not title:
        return None

    # Check for contact info
    emails = extract_emails(text)
    linkedins = extract_linkedin(text)
    phones = extract_phone(text)

    # Skip if no contact info
    if not emails and not linkedins and not phones:
        return None

    # Score based on content
    score = 0
    text_lower = text.lower()

    # Budget/year mentions = high intent
    if re.search(r'\$[\d,]+', text) or re.search(r'\d{4,}', text) or 'budget' in text_lower:
        score += 30

    # Keywords
    if any(kw in text_lower for kw in ['developer', 'chatbot', 'automation', 'ai', 'saas']):
        score += 25

    # Immediate need indicators
    if any(kw in text_lower for kw in ['urgent', 'asap', 'looking for', 'hire', 'need']):
        score += 20

    # Pain points
    pain_points = detect_pain_points(text)
    score += len(pain_points) * 10

    score = min(score, 100)

    # Skip low-quality leads
    if score < 40:
        return None

    company = find_company_name(text)
    industry = detect_industry(text)

    return {
        "id": f"reddit_{post.get('id')}",
        "name": author,
        "company": company,
        "industry": industry,
        "title": title[:150],
        "requirement": text[:800],
        "url": f"https://reddit.com{permalink}",
        "score": score,
        "status": "NEW",
        "source": source_name,
        "extracted_at": datetime.now().isoformat(),
        "posted_at": datetime.fromtimestamp(created_utc).isoformat(),
        "contact": {
            "emails": emails,
            "linkedin": linkedins[0] if linkedins else "",
            "phones": phones,
            "preferred": "email" if emails else ("linkedin" if linkedins else "phone")
        },
        "pain_points": pain_points,
        "tags": pain_points + [industry.lower()]
    }


def scrape_smart():
    """Smart scrape - only leads with contact info"""
    print("🎯 RAGSPRO Smart Lead Hunter")
    print("Only scraping leads with contact info...")
    print("=" * 50)

    existing = []
    if LEADS_FILE.exists():
        with open(LEADS_FILE, 'r') as f:
            existing = json.load(f)
    existing_ids = {l.get("id") for l in existing}

    new_leads = []

    for source in REDDIT_SOURCES:
        print(f"\n📡 {source['name']}...")
        try:
            response = requests.get(source["url"], headers=HEADERS, timeout=30)
            if response.status_code != 200:
                print(f"  ✗ Error {response.status_code}")
                continue

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            for post_data in posts:
                lead = process_post(post_data, source["name"])
                if lead and lead["id"] not in existing_ids:
                    new_leads.append(lead)
                    emails = len(lead["contact"]["emails"])
                    linkedin = "Yes" if lead["contact"]["linkedin"] else "No"
                    print(f"  ✓ [Score: {lead['score']}] {lead['title'][:50]}...")
                    print(f"    📧 {emails} emails | 🔗 LinkedIn: {linkedin}")
                    print(f"    💢 Pain: {', '.join(lead['pain_points'])}")

            time.sleep(1)

        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Save
    all_leads = existing + new_leads
    all_leads.sort(key=lambda x: x.get("score", 0), reverse=True)

    with open(LEADS_FILE, 'w') as f:
        json.dump(all_leads, f, indent=2, default=str)

    print(f"\n{'=' * 50}")
    print(f"✅ New leads with contact: {len(new_leads)}")
    print(f"📊 Total leads: {len(all_leads)}")

    # Show top 3
    if new_leads:
        print("\n🏆 Top Leads with Contact:")
        for i, l in enumerate(sorted(new_leads, key=lambda x: x["score"], reverse=True)[:3], 1):
            print(f"{i}. [{l['score']}] {l['title'][:60]}...")
            print(f"   Emails: {', '.join(l['contact']['emails'][:2]) or 'None'}")

    return new_leads


if __name__ == "__main__":
    scrape_smart()
