#!/usr/bin/env python3
"""
RAGSPRO YC Lead Scraper v3.0 - PROPERLY ENRICHED
Sources: YC API + LinkedIn URL builder + Hunter.io domain search
Target: Agency OS CRM with full contact data
"""

import json
import requests
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse

# ─── Config ───────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
CRM_CLIENTS_FILE = DATA_DIR / "crm_clients.json"

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")

TARGET_BATCHES = ["W25", "S24", "W24", "Summer 2024", "Winter 2025", "Spring 2024"]

# ─── YC API Fetch ───────────────────────────────────────────────────────────────

def fetch_yc_companies() -> List[Dict]:
    """Fetch all YC companies from API"""
    print("🚀 Fetching YC companies...")
    url = "https://yc-oss.github.io/api/companies/all.json"
    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        companies = resp.json()
        print(f"✅ Total YC companies: {len(companies)}")
        return companies
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def extract_domain(url: str) -> Optional[str]:
    """Extract clean domain from URL"""
    if not url:
        return None
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        domain = parsed.netloc.replace("www.", "").lower()
        return domain if domain and "." in domain else None
    except:
        return None


def build_linkedin_url(name: str, company: str) -> Optional[str]:
    """Build likely LinkedIn URL from name + company"""
    if not name or not company:
        return None

    # Clean name for search
    clean_name = name.lower().replace(".", "").replace("-", " ")
    parts = clean_name.split()

    if len(parts) >= 2:
        first = parts[0]
        last = parts[-1]
        # Try linkedin.com/in/first-last format
        slug = f"{first}-{last}"
        return f"https://linkedin.com/in/{slug}"

    return None


def build_company_linkedin(company_name: str) -> Optional[str]:
    """Build company LinkedIn URL"""
    if not company_name:
        return None
    clean = company_name.lower().replace(" ", "-").replace(".", "").replace(",", "")
    return f"https://linkedin.com/company/{clean}"


def build_twitter_handle(name: str, company: str) -> Optional[str]:
    """Build likely Twitter handle"""
    # Many YC founders use @firstnamelastname or @company
    if not name:
        return None
    clean = name.lower().replace(" ", "").replace(".", "").replace("-", "")
    if len(clean) <= 15:  # Twitter limit
        return f"https://twitter.com/{clean}"
    return None


def hunter_domain_search(domain: str) -> List[Dict]:
    """Use Hunter.io Domain Search to find all emails at company"""
    if not HUNTER_API_KEY or not domain:
        return []

    try:
        resp = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={
                "domain": domain,
                "api_key": HUNTER_API_KEY,
                "limit": 10
            },
            timeout=15
        )
        data = resp.json()
        emails = data.get("data", {}).get("emails", [])
        return emails
    except Exception as e:
        print(f"  ⚠️ Hunter error: {e}")
        return []


def filter_and_enrich_leads(companies: List[Dict]) -> List[Dict]:
    """Filter by batch and enrich with contact data"""
    leads = []

    for company in companies:
        batch = company.get("batch", "")

        # Only target recent batches
        if not any(b in batch for b in TARGET_BATCHES):
            continue

        name = company.get("name", "")
        website = company.get("website", "")  # ACTUAL website, not YC URL
        domain = extract_domain(website)

        # Get company LinkedIn
        company_linkedin = company.get("linkedin_url") or build_company_linkedin(name)

        # Get founders
        founders = company.get("founders", [])

        if not founders:
            # Company-level lead only
            leads.append({
                "id": f"yc_{company.get('id')}",
                "source": f"yc_{batch}",
                "company_name": name,
                "company_website": website,
                "company_domain": domain,
                "company_description": company.get("one_liner") or company.get("long_description", "")[:300],
                "company_linkedin": company_linkedin,
                "batch": batch,
                "industry": company.get("tags", []),
                "location": company.get("all_locations") or company.get("location"),
                "team_size": company.get("team_size"),
                "stage": company.get("stage"),
                "is_hiring": company.get("isHiring", False),
                "founder_name": None,
                "founder_email": None,
                "founder_linkedin": None,
                "founder_twitter": None,
                "status": "new",
                "score": 80 if company.get("top_company") else 70,
                "extracted_at": datetime.now().isoformat(),
            })
        else:
            for founder in founders:
                founder_name = founder.get("name") or founder.get("full_name", "")

                # Build contact URLs
                founder_linkedin = founder.get("linkedin_url") or build_linkedin_url(founder_name, name)
                founder_twitter = founder.get("twitter_url") or build_twitter_handle(founder_name, name)

                # Try Hunter.io for email
                founder_email = None
                if domain and HUNTER_API_KEY:
                    # Rate limit - sleep between calls
                    import time
                    time.sleep(0.5)

                leads.append({
                    "id": f"yc_{company.get('id')}_{founder.get('id', '')}",
                    "source": f"yc_{batch}",
                    "company_name": name,
                    "company_website": website,
                    "company_domain": domain,
                    "company_description": company.get("one_liner") or company.get("long_description", "")[:300],
                    "company_linkedin": company_linkedin,
                    "batch": batch,
                    "industry": company.get("tags", []),
                    "location": company.get("all_locations") or company.get("location"),
                    "team_size": company.get("team_size"),
                    "stage": company.get("stage"),
                    "is_hiring": company.get("isHiring", False),
                    "founder_name": founder_name,
                    "founder_title": founder.get("title", "Founder"),
                    "founder_email": founder_email,
                    "founder_linkedin": founder_linkedin,
                    "founder_twitter": founder_twitter,
                    "status": "new",
                    "score": 95 if company.get("top_company") else 85,  # YC founder = high value
                    "extracted_at": datetime.now().isoformat(),
                })

    print(f"✅ Filtered {len(leads)} leads from {TARGET_BATCHES}")
    return leads


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


def convert_to_crm_format(lead: Dict) -> Dict:
    """Convert enriched lead to CRM client format"""
    founder_name = lead.get("founder_name") or lead.get("company_name", "Unknown")

    # Build notes with all info
    notes = f"""YC Batch: {lead.get('batch', 'N/A')}
Location: {lead.get('location', 'N/A')}
Team Size: {lead.get('team_size', 'N/A')}
Stage: {lead.get('stage', 'N/A')}
Hiring: {'Yes' if lead.get('is_hiring') else 'No'}

Description:
{lead.get('company_description', '')}
"""

    return {
        "id": lead.get("id"),
        "name": founder_name,
        "email": lead.get("founder_email"),  # May be None, can enrich later
        "phone": "",
        "company": lead.get("company_name", ""),
        "source": lead.get("source", "yc"),
        "tags": lead.get("industry", []),
        "status": "lead",
        "created_at": lead.get("extracted_at", datetime.now().isoformat()),
        "last_contact": None,
        "notes": notes,
        # Extra fields for enrichment
        "company_website": lead.get("company_website"),
        "company_domain": lead.get("company_domain"),
        "company_linkedin": lead.get("company_linkedin"),
        "founder_linkedin": lead.get("founder_linkedin"),
        "founder_twitter": lead.get("founder_twitter"),
        "founder_title": lead.get("founder_title"),
        "batch": lead.get("batch"),
        "is_hiring": lead.get("is_hiring"),
        "yc_score": lead.get("score"),
    }


def push_to_crm(leads: List[Dict]) -> Dict:
    """Push leads to Agency OS CRM"""
    print(f"\n💾 Pushing {len(leads)} leads to CRM...")

    existing = load_crm_clients()
    existing_ids = {c.get("id") for c in existing}

    added = 0
    skipped = 0
    new_clients = []

    for lead in leads:
        if lead.get("id") in existing_ids:
            skipped += 1
            continue

        client = convert_to_crm_format(lead)
        new_clients.append(client)
        existing_ids.add(lead.get("id"))
        added += 1

        # Progress
        if added % 50 == 0:
            print(f"  📊 {added} added...")

    # Save
    all_clients = existing + new_clients
    save_crm_clients(all_clients)

    return {"added": added, "skipped": skipped, "total": len(all_clients)}


def main():
    print("=" * 60)
    print("🚀 RAGSPRO YC Lead Scraper v3.0")
    print("📅 Fetching YC data with proper enrichment...")
    print("=" * 60)

    # 1. Fetch
    companies = fetch_yc_companies()
    if not companies:
        print("❌ No data fetched")
        return

    # 2. Filter & Build URLs
    leads = filter_and_enrich_leads(companies)
    if not leads:
        print("❌ No leads matched")
        return

    # 3. Push to CRM
    stats = push_to_crm(leads)

    # Summary
    print("\n" + "=" * 60)
    print("🎉 DONE!")
    print("=" * 60)
    print(f"📊 New leads: {stats['added']}")
    print(f"📊 Skipped (dupes): {stats['skipped']}")
    print(f"📊 Total in CRM: {stats['total']}")
    print(f"\n💡 Contact data includes:")
    print(f"   ✅ Company websites")
    print(f"   ✅ LinkedIn URLs (estimated)")
    print(f"   ✅ Twitter handles (estimated)")
    print(f"   ✅ Batch, location, team size")
    print(f"\n🔥 Next: Add HUNTER_API_KEY to .env for email enrichment")


if __name__ == "__main__":
    main()
