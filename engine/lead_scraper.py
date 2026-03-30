#!/usr/bin/env python3
"""
RAGSPRO Lead Scraper — Scrapes Reddit for REAL [HIRING] leads
Focuses on people LOOKING TO HIRE, not people offering services
Extracts contact info (email, LinkedIn, phone) when available
"""

import json
import re
import requests
import time
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, LEAD_KEYWORDS

LEADS_FILE = DATA_DIR / "leads.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# Subreddits with HIRING-focused searches (strictly [HIRING] only)
SUBREDDITS = [
    # r/forhire — ONLY flair:Hiring posts
    {"name": "r/forhire [HIRING]", "url": "https://www.reddit.com/r/forhire/search.json?q=flair%3AHiring&sort=new&limit=50&t=week"},
    # r/slavelabour — Task offers only (not [TASK] which is people offering work)
    {"name": "r/slavelabour [OFFER]", "url": "https://www.reddit.com/r/slavelabour/search.json?q=flair%3AOffer&sort=new&limit=30&t=week"},
    # Startup subs with hiring intent
    {"name": "r/startups hiring", "url": "https://www.reddit.com/r/startups/search.json?q=%5BHiring%5D+OR+%22we+are+hiring%22+OR+%22looking+to+hire%22&sort=new&limit=25&t=week"},
    # Small business needing help
    {"name": "r/smallbusiness", "url": "https://www.reddit.com/r/smallbusiness/search.json?q=%5BHiring%5D+OR+%22need+a+website%22+OR+%22need+an+app%22+OR+%22looking+for+developer%22&sort=new&limit=25&t=week"},
    # Entrepreneurs building
    {"name": "r/entrepreneur", "url": "https://www.reddit.com/r/Entrepreneur/search.json?q=%5BHiring%5D+OR+%22need+developer%22+OR+%22need+help+building%22&sort=new&limit=25&t=week"},
    # Indie hackers
    {"name": "r/indiehackers", "url": "https://www.reddit.com/r/indiehackers/search.json?q=%5BHiring%5D+OR+%22looking+for+developer%22+OR+%22need+developer%22&sort=new&limit=25&t=week"},
    # Indian startups
    {"name": "r/indianstartups", "url": "https://www.reddit.com/r/indianstartups/search.json?q=%5BHiring%5D+OR+%22we+are+hiring%22&sort=new&limit=25&t=week"},
]


def extract_emails(text):
    """Extract emails from text"""
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    # Filter false positives
    return list(set(e for e in emails if not any(x in e.lower() for x in ['example.com', 'test.com', 'domain.com', 'email.com'])))


def extract_linkedin(text):
    """Extract LinkedIn URLs"""
    patterns = [
        r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+',
        r'(?:https?://)?(?:www\.)?linkedin\.com/company/[\w-]+',
    ]
    results = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            url = m if m.startswith("http") else f"https://{m}"
            results.append(url)
    return list(set(results))


def extract_phones(text):
    """Extract phone numbers"""
    patterns = [
        r'\+91[\s-]?\d{5}[\s-]?\d{5}',
        r'\+1[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}',
        r'\(\d{3}\)[\s-]?\d{3}[\s-]?\d{4}',
    ]
    phones = []
    for pattern in patterns:
        phones.extend(re.findall(pattern, text))
    return list(set(phones))


def is_hiring_post(title, text):
    """Determine if this is someone HIRING (not offering services)"""
    title_lower = title.lower()
    text_lower = (text or "").lower()
    combined = title_lower + " " + text_lower[:500]

    # IMMEDIATE REJECTION: Strong for-hire signals in title
    instant_reject_title = [
        "[for hire]", "[forhire]", "[for-hire]",
        "hire me", "i am a developer", "i'm a developer",
        "i am a freelancer", "i'm a freelancer",
        "i am available", "i'm available", "available for work",
        "open to work", "seeking work", "looking for work",
        "looking for clients", "offering my services",
        "my portfolio", "my services", "i built",
    ]
    for signal in instant_reject_title:
        if signal in title_lower:
            return False

    # REJECT: For-hire signals anywhere in post
    for_hire_signals = [
        "available for freelance", "available for remote",
        "looking for remote work", "seeking remote work",
        "offering website development", "offering web development",
        "offering ai development", "offering chatbot",
        "dm me if interested", "message me if interested",
        "check out my portfolio", "view my work",
        "what i built", "what i've built", "what i have built",
        "i can build", "i will build", "i create",
        "my expertise", "my skills include", "tech stack",
        "years of experience", "years experience",
    ]
    for signal in for_hire_signals:
        if signal in combined:
            return False

    # STRONG HIRING signals (must be present to qualify)
    strong_hiring = [
        "[hiring]", "looking to hire", "need to hire",
        "want to hire", "hiring a", "hiring for",
        "seeking a developer", "seeking developer",
        "need a developer", "need developer", "need an app",
        "need a website", "need someone to build",
        "need help building", "job posting", "position available",
        "we are hiring", "we're hiring", "i am hiring",
        "i'm hiring", "our company", "our team",
        "pay someone to", "will pay", "budget is",
    ]
    has_hiring_signal = any(s in combined for s in strong_hiring)

    # Budget mention helps but not enough alone
    has_budget = bool(re.search(r'\$[\d,]+', title)) or 'budget' in title_lower

    # Must have strong hiring signal OR clear budget + need language
    return has_hiring_signal or (has_budget and any(x in combined for x in ["need", "looking for", "want"]))


def score_lead(title, text):
    """Score a lead based on relevance to RAGSPRO services"""
    score = 0
    combined = (title + " " + (text or "")).lower()

    # [HIRING] tag = highest signal
    if "[hiring]" in combined:
        score += 30

    # Budget/payment mentions
    if re.search(r'\$[\d,]+', combined):
        score += 25
    if 'budget' in combined:
        score += 15

    # RAGSPRO-specific services (highest value leads)
    high_value = ["chatbot", "ai chatbot", "automation", "ai agent", "saas",
                  "web app", "webapp", "dashboard", "platform", "mvp"]
    for kw in high_value:
        if kw in combined:
            score += 20

    # General dev keywords
    dev_keywords = ["website", "landing page", "react", "next.js", "nextjs",
                    "python", "node", "fullstack", "full stack", "backend",
                    "api", "scraping", "bot", "mobile app"]
    for kw in dev_keywords:
        if kw in combined:
            score += 10

    # Urgency
    urgency = ["urgent", "asap", "immediately", "right away", "this week", "today"]
    for kw in urgency:
        if kw in combined:
            score += 15

    # Has contact info = higher intent
    if extract_emails(combined):
        score += 10
    if extract_linkedin(combined):
        score += 5

    return min(score, 100)


def process_post(post_data, source_name):
    """Process a Reddit post into a qualified lead"""
    post = post_data.get("data", {})

    title = post.get("title", "")
    text = post.get("selftext", "")
    author = post.get("author", "unknown")
    permalink = post.get("permalink", "")
    created_utc = post.get("created_utc", 0)

    if not title:
        return None

    # CRITICAL: Only accept hiring posts
    if not is_hiring_post(title, text):
        return None

    # Score the lead
    score = score_lead(title, text)

    # Skip very low quality
    if score < 15:
        return None

    # Extract contact info
    full_text = title + " " + text
    emails = extract_emails(full_text)
    linkedins = extract_linkedin(full_text)
    phones = extract_phones(full_text)

    return {
        "id": f"reddit_{post.get('id', '')}",
        "name": author,
        "title": title[:150],
        "requirement": text[:600],
        "url": f"https://reddit.com{permalink}",
        "platform": source_name,
        "score": score,
        "status": "NEW",
        "extracted_at": datetime.now().isoformat(),
        "posted_at": datetime.fromtimestamp(created_utc).isoformat() if created_utc else "",
        "contact": {
            "email": emails[0] if emails else "",
            "emails": emails,
            "linkedin": linkedins[0] if linkedins else "",
            "phone": phones[0] if phones else "",
            "phones": phones,
            "reddit_user": f"u/{author}"
        },
        "pain_points": [],
        "tags": []
    }


def scrape():
    """Scrape all sources for HIRING leads only"""
    print(f"🎯 {DATA_DIR.parent.name} Lead Scraper")
    print("🔍 Filtering for [HIRING] posts only...")
    print("=" * 50)

    # Load existing
    existing = []
    if LEADS_FILE.exists():
        try:
            with open(LEADS_FILE, 'r') as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            existing = []

    existing_ids = {l.get("id") for l in existing}
    new_leads = []

    for source in SUBREDDITS:
        print(f"\n📡 {source['name']}...")
        try:
            response = requests.get(source["url"], headers=HEADERS, timeout=30)
            if response.status_code == 429:
                print(f"  ⏳ Rate limited, waiting...")
                time.sleep(5)
                response = requests.get(source["url"], headers=HEADERS, timeout=30)

            if response.status_code != 200:
                print(f"  ✗ Error {response.status_code}")
                continue

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            count = 0
            for post_data in posts:
                lead = process_post(post_data, source["name"])
                if lead and lead["id"] not in existing_ids:
                    new_leads.append(lead)
                    existing_ids.add(lead["id"])
                    count += 1

                    has_email = "📧" if lead["contact"]["email"] else ""
                    has_linkedin = "🔗" if lead["contact"]["linkedin"] else ""
                    print(f"  ✓ [Score: {lead['score']}] {has_email}{has_linkedin} {lead['title'][:50]}...")

            print(f"  → {count} new qualified leads")
            time.sleep(2)  # Respect rate limits

        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Merge and sort by score
    all_leads = existing + new_leads
    all_leads.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Save
    LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEADS_FILE, 'w') as f:
        json.dump(all_leads, f, indent=2, default=str)

    print(f"\n{'=' * 50}")
    print(f"✅ New [HIRING] leads: {len(new_leads)}")
    print(f"📊 Total leads in DB: {len(all_leads)}")

    if new_leads:
        with_contact = len([l for l in new_leads if l["contact"]["email"] or l["contact"]["linkedin"]])
        print(f"📇 With contact info: {with_contact}/{len(new_leads)}")

        print("\n🏆 Top New Leads:")
        for i, lead in enumerate(sorted(new_leads, key=lambda x: x["score"], reverse=True)[:5], 1):
            email = lead["contact"]["email"] or "no email"
            print(f"  {i}. [{lead['score']}] {lead['title'][:55]}")
            print(f"     📧 {email} | 👤 {lead['name']}")

    return new_leads


if __name__ == "__main__":
    scrape()
