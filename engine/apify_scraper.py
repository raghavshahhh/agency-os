#!/usr/bin/env python3
"""
RAGSPRO Apify Lead Scraper — Google Maps + LinkedIn scraping
Fetches real business leads with contact info
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path
import sys
import re

sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR

LEADS_FILE = DATA_DIR / "leads.json"

def get_apify_token():
    """Get Apify token from environment or config"""
    import os
    token = os.getenv("APIFY_TOKEN", "")
    if not token:
        # Check in common locations
        env_file = Path.home() / ".apify" / "token"
        if env_file.exists():
            return env_file.read_text().strip()
    return token

APIFY_TOKEN = get_apify_token()

def scrape_google_maps(query="software companies in Delhi", max_results=50):
    """Scrape Google Maps for business leads"""
    if not APIFY_TOKEN:
        print("❌ APIFY_TOKEN not set")
        return []

    print(f"🔍 Scraping Google Maps: '{query}'...")

    # Apify Google Maps Scraper actor
    actor_id = "compass~crawler-google-places"

    # Start the actor run
    run_response = requests.post(
        f"https://api.apify.com/v2/acts/{actor_id}/runs",
        headers={"Authorization": f"Bearer {APIFY_TOKEN}"},
        json={
            "queries": query,
            "maxCrawledPlaces": max_results,
            "language": "en",
            "region": "in"
        }
    )

    if run_response.status_code != 201:
        print(f"❌ Failed to start actor: {run_response.text}")
        return []

    run_data = run_response.json()
    run_id = run_data["data"]["id"]

    print(f"⏳ Waiting for scrape to complete (run: {run_id[:8]}...)...")

    # Wait for completion
    for _ in range(30):  # Max 5 minutes
        time.sleep(10)
        status_response = requests.get(
            f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}",
            headers={"Authorization": f"Bearer {APIFY_TOKEN}"}
        )
        status = status_response.json()["data"]["status"]

        if status == "SUCCEEDED":
            break
        elif status in ["FAILED", "TIMED-OUT", "ABORTED"]:
            print(f"❌ Scrape failed with status: {status}")
            return []

    # Get dataset items
    dataset_id = status_response.json()["data"]["defaultDatasetId"]
    dataset_response = requests.get(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items",
        headers={"Authorization": f"Bearer {APIFY_TOKEN}"},
        params={"format": "json", "clean": "true"}
    )

    results = dataset_response.json()
    print(f"✅ Scraped {len(results)} businesses from Google Maps")

    return results

def transform_google_maps_to_lead(place_data):
    """Transform Apify Google Maps result to Agency OS lead format"""
    lead = {
        "id": f"gmaps_{place_data.get('placeId', 'unknown')}",
        "name": place_data.get("title", ""),
        "company": place_data.get("title", ""),
        "title": f"{place_data.get('title', '')} - {place_data.get('categoryName', 'Business')}",
        "requirement": place_data.get("description", ""),
        "industry": place_data.get("categoryName", ""),
        "url": place_data.get("website", ""),
        "platform": "Google Maps",
        "score": 80 if place_data.get("website") else 60,
        "status": "NEW",
        "extracted_at": datetime.now().isoformat(),
        "posted_at": datetime.now().isoformat(),
        "location": place_data.get("address", ""),
        "phone": place_data.get("phone", ""),
        "contact": {
            "emails": [],
            "phones": [place_data.get("phone", "")] if place_data.get("phone") else [],
            "website": place_data.get("website", "")
        },
        "source": "apify_google_maps",
        "metadata": {
            "rating": place_data.get("totalScore"),
            "reviews": place_data.get("reviewsCount"),
            "latitude": place_data.get("location", {}).get("lat"),
            "longitude": place_data.get("location", {}).get("lng")
        }
    }

    return lead

def scrape_linkedin_jobs(keywords="AI developer", location="India", max_results=25):
    """Scrape LinkedIn job postings for hiring intent"""
    if not APIFY_TOKEN:
        print("❌ APIFY_TOKEN not set")
        return []

    print(f"🔍 Scraping LinkedIn Jobs: '{keywords}' in {location}...")

    actor_id = "apify~linkedin-jobs-scraper"

    run_response = requests.post(
        f"https://api.apify.com/v2/acts/{actor_id}/runs",
        headers={"Authorization": f"Bearer {APIFY_TOKEN}"},
        json={
            "searchTerms": keywords,
            "location": location,
            "maxResults": max_results,
            "jobType": ""
        }
    )

    if run_response.status_code != 201:
        print(f"❌ Failed to start actor: {run_response.text}")
        return []

    run_id = run_response.json()["data"]["id"]

    # Wait for completion
    for _ in range(30):
        time.sleep(10)
        status_response = requests.get(
            f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}",
            headers={"Authorization": f"Bearer {APIFY_TOKEN}"}
        )
        status = status_response.json()["data"]["status"]

        if status == "SUCCEEDED":
            break
        elif status in ["FAILED", "TIMED-OUT", "ABORTED"]:
            print(f"❌ Scrape failed: {status}")
            return []

    dataset_id = status_response.json()["data"]["defaultDatasetId"]
    dataset_response = requests.get(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items",
        headers={"Authorization": f"Bearer {APIFY_TOKEN}"}
    )

    results = dataset_response.json()
    print(f"✅ Scraped {len(results)} LinkedIn job postings")

    return results

def transform_linkedin_job_to_lead(job_data):
    """Transform LinkedIn job to Agency OS lead format"""
    lead = {
        "id": f"linkedin_{job_data.get('id', 'unknown')}",
        "name": job_data.get("companyName", ""),
        "company": job_data.get("companyName", ""),
        "title": f"{job_data.get('title', '')} at {job_data.get('companyName', '')}",
        "requirement": job_data.get("description", ""),
        "industry": job_data.get("industry", ""),
        "url": job_data.get("jobUrl", ""),
        "platform": "LinkedIn",
        "score": 85,
        "status": "NEW",
        "extracted_at": datetime.now().isoformat(),
        "posted_at": job_data.get("postedAt", datetime.now().isoformat()),
        "location": job_data.get("location", ""),
        "contact": {
            "emails": [],
            "website": job_data.get("companyUrl", "")
        },
        "source": "apify_linkedin",
        "metadata": {
            "salary": job_data.get("salary"),
            "seniority": job_data.get("seniorityLevel"),
            "workType": job_data.get("workType"),
            "applicants": job_data.get("applicantsCount")
        }
    }

    return lead

def load_existing_leads():
    """Load existing leads from file"""
    if LEADS_FILE.exists():
        with open(LEADS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_leads(leads):
    """Save leads to file"""
    LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEADS_FILE, 'w') as f:
        json.dump(leads, f, indent=2)

def add_new_leads(new_leads):
    """Add new leads, avoiding duplicates"""
    existing = load_existing_leads()
    existing_ids = {l.get("id") for l in existing}

    added = 0
    for lead in new_leads:
        if lead.get("id") not in existing_ids:
            existing.append(lead)
            existing_ids.add(lead.get("id"))
            added += 1

    save_leads(existing)
    return added

def run_daily_scrape():
    """Run daily lead scraping from multiple sources"""
    print("=" * 60)
    print("🚀 RAGSPRO Daily Lead Scraper")
    print("=" * 60)

    total_added = 0

    # Scrape Google Maps for software companies
    if APIFY_TOKEN:
        try:
            # Delhi NCR
            results = scrape_google_maps("software companies in Delhi", 30)
            leads = [transform_google_maps_to_lead(r) for r in results]
            added = add_new_leads(leads)
            print(f"   Added: {added} new leads")
            total_added += added

            # Mumbai
            results = scrape_google_maps("software companies in Mumbai", 30)
            leads = [transform_google_maps_to_lead(r) for r in results]
            added = add_new_leads(leads)
            print(f"   Added: {added} new leads")
            total_added += added

            # Bangalore
            results = scrape_google_maps("software companies in Bangalore", 30)
            leads = [transform_google_maps_to_lead(r) for r in results]
            added = add_new_leads(leads)
            print(f"   Added: {added} new leads")
            total_added += added

            # LinkedIn Jobs
            results = scrape_linkedin_jobs("AI developer OR chatbot OR automation", "India", 25)
            leads = [transform_linkedin_job_to_lead(r) for r in results]
            added = add_new_leads(leads)
            print(f"   Added: {added} new leads")
            total_added += added

        except Exception as e:
            print(f"❌ Error during scraping: {e}")
    else:
        print("⚠️ APIFY_TOKEN not set, skipping Apify scraper")
        print("   Set it with: export APIFY_TOKEN=your_token")

    print(f"\n✅ Total new leads added: {total_added}")
    print(f"📊 Total leads in database: {len(load_existing_leads())}")

    return total_added

if __name__ == "__main__":
    run_daily_scrape()
