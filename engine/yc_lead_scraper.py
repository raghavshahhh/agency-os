#!/usr/bin/env python3
"""
RAGSPRO YC + Product Hunt Lead Scraper v2.0
Sources: YC API (5690+ companies) + Product Hunt + Hunter.io enrichment
Target: Agency OS CRM (crm_clients.json + crm_deals.json)
"""

import json
import requests
import re
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse

# ─── Config ───────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
LEADS_FILE = DATA_DIR / "leads.json"
CRM_CLIENTS_FILE = DATA_DIR / "crm_clients.json"
CRM_DEALS_FILE = DATA_DIR / "crm_deals.json"

# API Keys from env (will be loaded from .env)
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")

# Target YC batches (newest founders first)
TARGET_BATCHES = ["W25", "S24", "W24", "Summer 2024", "Winter 2025", "Spring 2024"]

# ICP tags for RAGSPRO (AI, SaaS, Dev tools, Legal tech)
ICP_TAGS = [
    "saas", "b2b", "developer-tools", "artificial-intelligence",
    "legal", "fintech", "automation", "no-code", "api", "developer"
]

# ─── YC API Integration ───────────────────────────────────────────────────────

def fetch_yc_companies() -> List[Dict]:
    """
    Fetch from YC unofficial API (free, daily updated, 5690+ companies)
    Source: https://yc-oss.github.io/api/companies/all.json
    """
    print("🚀 Fetching YC companies...")
    url = "https://yc-oss.github.io/api/companies/all.json"

    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        companies = resp.json()
        print(f"✅ Total YC companies fetched: {len(companies)}")
        return companies
    except Exception as e:
        print(f"❌ YC API error: {e}")
        return []


def filter_yc_leads(companies: List[Dict]) -> List[Dict]:
    """Filter YC companies by batch and ICP tags"""
    leads = []

    for company in companies:
        batch = company.get("batch", "")

        # Filter by target batches
        if not any(b in batch for b in TARGET_BATCHES):
            continue

        # Check ICP match (optional - can remove to get all)
        company_tags = [t.lower() for t in company.get("tags", [])]
        tag_match = any(tag in " ".join(company_tags) for tag in ICP_TAGS)

        # Get founders
        founders = company.get("founders", [])

        if not founders:
            # Company-level lead
            leads.append({
                "id": f"yc_{company.get('id', company.get('name', ''))}",
                "source": "yc",
                "company_name": company.get("name"),
                "company_url": company.get("url"),
                "company_description": company.get("one_liner") or company.get("long_description", "")[:300],
                "batch": batch,
                "industry": company.get("tags", []),
                "location": company.get("location"),
                "team_size": str(company.get("team_size", "")),
                "founder_name": None,
                "founder_linkedin": None,
                "founder_twitter": None,
                "founder_email": None,
                "company_email": None,
                "status": "new",
                "score": 85,  # High quality - YC vetted
                "extracted_at": datetime.now().isoformat(),
            })
        else:
            for founder in founders:
                leads.append({
                    "id": f"yc_{company.get('id', '')}_{founder.get('id', '')}",
                    "source": "yc",
                    "company_name": company.get("name"),
                    "company_url": company.get("url"),
                    "company_description": company.get("one_liner") or company.get("long_description", "")[:300],
                    "batch": batch,
                    "industry": company.get("tags", []),
                    "location": company.get("location"),
                    "team_size": str(company.get("team_size", "")),
                    "founder_name": founder.get("name") or founder.get("full_name"),
                    "founder_linkedin": founder.get("linkedin_url") or founder.get("linkedin"),
                    "founder_twitter": founder.get("twitter_url") or founder.get("twitter"),
                    "founder_email": None,
                    "company_email": None,
                    "status": "new",
                    "score": 90,  # YC founder = highest quality
                    "extracted_at": datetime.now().isoformat(),
                })

    print(f"✅ YC leads filtered: {len(leads)} (batches: {TARGET_BATCHES})")
    return leads


# ─── Hunter.io Email Enrichment ───────────────────────────────────────────────

def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL"""
    if not url:
        return None
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        domain = parsed.netloc.replace("www.", "")
        return domain if domain else None
    except:
        return None


def enrich_email_hunter(domain: str, first_name: str, last_name: str) -> Optional[str]:
    """
    Use Hunter.io to find email from domain + name
    Free tier: 25 searches/month | Paid: $49/mo = 500 searches
    """
    if not HUNTER_API_KEY or not domain or not first_name:
        return None

    # Skip YC domain
    if "ycombinator.com" in domain:
        return None

    try:
        resp = requests.get(
            "https://api.hunter.io/v2/email-finder",
            params={
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name or "",
                "api_key": HUNTER_API_KEY
            },
            timeout=10
        )
        data = resp.json()
        email = data.get("data", {}).get("email")
        confidence = data.get("data", {}).get("score", 0)

        if email and confidence >= 60:
            print(f"  📧 Found email: {email} ({confidence}% confidence)")
            return email
    except Exception as e:
        print(f"  ⚠️ Hunter error: {e}")

    return None


def enrich_leads(leads: List[Dict]) -> List[Dict]:
    """Enrich leads with Hunter.io emails"""
    print(f"\n🔍 Enriching {len(leads)} leads with Hunter.io...")

    enriched = []
    for i, lead in enumerate(leads):
        if lead.get("founder_email"):
            enriched.append(lead)
            continue

        # Try to find email
        domain = extract_domain(lead.get("company_url"))
        founder_name = lead.get("founder_name", "")

        if domain and founder_name and HUNTER_API_KEY:
            names = founder_name.split()
            first = names[0] if names else ""
            last = names[-1] if len(names) > 1 else ""

            email = enrich_email_hunter(domain, first, last)
            if email:
                lead["founder_email"] = email
                lead["email_source"] = "hunter.io"

            # Rate limit: 1 req/sec for free tier
            import time
            time.sleep(1.1)

        enriched.append(lead)

        # Progress
        if (i + 1) % 10 == 0:
            print(f"  📊 Progress: {i+1}/{len(leads)}")

    print(f"✅ Enrichment complete")
    return enriched


# ─── CRM Integration ────────────────────────────────────────────────────────────

def load_crm_clients() -> List[Dict]:
    """Load existing CRM clients"""
    if CRM_CLIENTS_FILE.exists():
        try:
            with open(CRM_CLIENTS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []


def save_crm_clients(clients: List[Dict]):
    """Save CRM clients"""
    CRM_CLIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CRM_CLIENTS_FILE, 'w') as f:
        json.dump(clients, f, indent=2, default=str)


def convert_lead_to_crm_client(lead: Dict) -> Dict:
    """Convert scraped lead to CRM client format"""
    return {
        "id": lead.get("id", f"CLI_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
        "name": lead.get("founder_name") or lead.get("company_name", "Unknown"),
        "email": lead.get("founder_email") or lead.get("company_email", ""),
        "phone": "",
        "company": lead.get("company_name", ""),
        "source": f"{lead.get('source', 'unknown')}_{lead.get('batch', '')}",
        "tags": lead.get("industry", []),
        "status": "lead",  # lead, prospect, client, churned
        "created_at": lead.get("extracted_at", datetime.now().isoformat()),
        "last_contact": None,
        "notes": f"YC Batch: {lead.get('batch', 'N/A')}\nLocation: {lead.get('location', 'N/A')}\nTeam: {lead.get('team_size', 'N/A')}\n{lead.get('company_description', '')[:200]}"
    }


def push_to_crm(leads: List[Dict]) -> Dict:
    """Push leads to Agency OS CRM"""
    print(f"\n💾 Pushing {len(leads)} leads to CRM...")

    existing_clients = load_crm_clients()
    existing_emails = {c.get("email", "").lower() for c in existing_clients if c.get("email")}

    added = 0
    skipped = 0
    new_clients = []

    for lead in leads:
        email = lead.get("founder_email") or lead.get("company_email", "")

        # Skip duplicates
        if email and email.lower() in existing_emails:
            skipped += 1
            continue

        # Convert to CRM format
        client = convert_lead_to_crm_client(lead)
        new_clients.append(client)
        existing_emails.add(email.lower() if email else "")
        added += 1

        print(f"  ✅ {client['name']} ({client['company']})")

    # Save combined
    all_clients = existing_clients + new_clients
    save_crm_clients(all_clients)

    # Also save to legacy leads.json for backward compatibility
    save_to_legacy_leads(leads)

    return {"added": added, "skipped": skipped, "total": len(all_clients)}


def save_to_legacy_leads(leads: List[Dict]):
    """Also save to legacy leads.json format"""
    existing = []
    if LEADS_FILE.exists():
        try:
            with open(LEADS_FILE, 'r') as f:
                existing = json.load(f)
        except:
            pass

    existing_ids = {l.get("id") for l in existing}
    new_leads = [l for l in leads if l.get("id") not in existing_ids]

    all_leads = existing + new_leads
    all_leads.sort(key=lambda x: x.get("score", 0), reverse=True)

    LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEADS_FILE, 'w') as f:
        json.dump(all_leads, f, indent=2, default=str)

    print(f"  📁 Legacy leads.json: {len(new_leads)} new, {len(all_leads)} total")


# ─── Main Execution ───────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("🚀 RAGSPRO YC Lead Scraper v2.0")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Check Hunter API key
    if not HUNTER_API_KEY:
        print("\n⚠️  HUNTER_API_KEY not set! Email enrichment disabled.")
        print("   Add to .env: HUNTER_API_KEY=your_key_here")

    # 1. Fetch YC data
    companies = fetch_yc_companies()
    if not companies:
        print("❌ No companies fetched. Exiting.")
        return

    # 2. Filter leads
    leads = filter_yc_leads(companies)
    if not leads:
        print("❌ No leads matched criteria. Exiting.")
        return

    # 3. Enrich with emails (optional)
    if HUNTER_API_KEY:
        leads = enrich_leads(leads[:25])  # Limit to 25 for free tier
    else:
        print("\n⏭️  Skipping enrichment (no Hunter API key)")

    # 4. Push to CRM
    stats = push_to_crm(leads)

    # 5. Summary
    print("\n" + "=" * 60)
    print("🎉 COMPLETE!")
    print("=" * 60)
    print(f"📊 New leads added: {stats['added']}")
    print(f"📊 Duplicates skipped: {stats['skipped']}")
    print(f"📊 Total CRM clients: {stats['total']}")
    print(f"\n💡 Next steps:")
    print(f"   1. Open Agency OS → Clients page")
    print(f"   2. Filter by 'lead' status")
    print(f"   3. Add deals for high-value prospects")


if __name__ == "__main__":
    main()
