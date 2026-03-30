#!/usr/bin/env python3
"""
RAGSPRO LinkedIn Scraper — Find hiring posts from LinkedIn
Uses RSS feeds and search to find people hiring for developers/AI/chatbots
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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# LinkedIn job search RSS feeds (public, no login required)
LINKEDIN_SEARCHES = [
    # Job searches for relevant roles
    {"name": "LinkedIn: Developer Hiring", "url": "https://www.linkedin.com/jobs/search?keywords=developer&location=remote&f_TPR=r86400&sortBy=DD"},
    {"name": "LinkedIn: AI Chatbot Hiring", "url": "https://www.linkedin.com/jobs/search?keywords=ai%20chatbot&location=remote&f_TPR=r86400&sortBy=DD"},
    {"name": "LinkedIn: SaaS Developer", "url": "https://www.linkedin.com/jobs/search?keywords=saas%20developer&location=remote&f_TPR=r86400&sortBy=DD"},
    {"name": "LinkedIn: Next.js Developer", "url": "https://www.linkedin.com/jobs/search?keywords=next.js&location=remote&f_TPR=r86400&sortBy=DD"},
    {"name": "LinkedIn: Python Developer", "url": "https://www.linkedin.com/jobs/search?keywords=python%20developer&location=remote&f_TPR=r86400&sortBy=DD"},
]

# Alternative: LinkedIn posts via RSS (limited)
LINKEDIN_RSS_FEEDS = [
    # Note: LinkedIn RSS feeds are limited, these are placeholder for actual scraping
    {"name": "LinkedIn Posts: #hiring", "url": "https://www.linkedin.com/feed/hashtag/hiring"},
]


def extract_emails(text):
    """Extract emails from text"""
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return list(set(e for e in emails if not any(x in e.lower() for x in ['example.com', 'test.com', 'linkedin.com'])))


def extract_linkedin_urls(text):
    """Extract LinkedIn URLs"""
    pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/(?:company|in)/[\w-]+'
    matches = re.findall(pattern, text)
    return list(set(matches))


def score_linkedin_job(title, description, company):
    """Score a LinkedIn job posting"""
    score = 0
    combined = (title + " " + description + " " + company).lower()

    # Base score for being a real job posting
    score += 20

    # High-value keywords
    high_value = ["chatbot", "ai chatbot", "automation", "ai agent", "saas",
                  "web app", "webapp", "dashboard", "platform", "mvp", "nextjs", "next.js"]
    for kw in high_value:
        if kw in combined:
            score += 15

    # General dev keywords
    dev_keywords = ["website", "landing page", "react", "python", "node",
                    "fullstack", "full stack", "backend", "api", "scraping", "bot"]
    for kw in dev_keywords:
        if kw in combined:
            score += 8

    # Remote-friendly
    if "remote" in combined:
        score += 10

    # Contract/freelance preferred
    if any(x in combined for x in ["contract", "freelance", "project", "part-time", "part time"]):
        score += 10

    # Urgency
    urgency = ["urgent", "asap", "immediately", "right away", "this week", "today", "quickly"]
    for kw in urgency:
        if kw in combined:
            score += 10

    # Company size indicators (startups/small = better for us)
    if any(x in combined for x in ["startup", "early stage", "seed", "series a"]):
        score += 10

    return min(score, 100)


def scrape_linkedin_jobs():
    """Scrape LinkedIn job postings (simplified version)"""
    print("🎯 RAGSPRO LinkedIn Job Scraper")
    print("Note: Full LinkedIn scraping requires LinkedIn API or Selenium")
    print("This is a foundation module - integrate with LinkedIn API for full functionality")
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

    # For now, create a template/example lead structure
    # Real implementation needs LinkedIn API or browser automation
    print("\n📡 LinkedIn Jobs API integration ready")
    print("To enable full scraping:")
    print("  1. Apply for LinkedIn Marketing Developer Program")
    print("  2. Get API credentials")
    print("  3. Or use browser automation with Selenium/Playwright")
    print("\n✅ Module ready for integration")

    return new_leads


def create_linkedin_lead(job_data):
    """Convert LinkedIn job data to lead format"""
    return {
        "id": f"linkedin_{job_data.get('job_id', '')}",
        "name": job_data.get("company", "Unknown"),
        "title": job_data.get("title", "")[:150],
        "requirement": job_data.get("description", "")[:600],
        "url": job_data.get("url", ""),
        "platform": "LinkedIn Jobs",
        "score": score_linkedin_job(
            job_data.get("title", ""),
            job_data.get("description", ""),
            job_data.get("company", "")
        ),
        "status": "NEW",
        "extracted_at": datetime.now().isoformat(),
        "posted_at": job_data.get("posted_at", ""),
        "contact": {
            "email": "",
            "emails": [],
            "linkedin": job_data.get("company_linkedin", ""),
            "phone": "",
            "phones": [],
            "company": job_data.get("company", ""),
            "recruiter": job_data.get("recruiter_name", ""),
        },
        "pain_points": [],
        "tags": ["linkedin", "job-posting"]
    }


if __name__ == "__main__":
    scrape_linkedin_jobs()
