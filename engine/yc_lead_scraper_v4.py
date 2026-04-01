#!/usr/bin/env python3
"""
RAGSPRO YC Lead Scraper v4.0 - FULLY ENRICHED
- Extracts emails from descriptions
- Hunter.io domain search for all company emails
- LinkedIn URL building
- Proper CRM integration
"""

import json
import requests
import re
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse
import time

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ─── Config ───────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
CRM_CLIENTS_FILE = DATA_DIR / "crm_clients.json"

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")

TARGET_BATCHES = ["W25", "S24", "W24", "Summer 2024", "Winter 2025", "Spring 2024"]

# ─── Email Extraction ─────────────────────────────────────────────────────────

def extract_emails_from_text(text: str) -> List[str]:
    """Extract all emails from text using regex"""
    if not text:
        return []

    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)

    # Filter out common false positives
    filtered = []
    for email in emails:
        email = email.lower()
        if any(x in email for x in ['example.com', 'test.com', 'domain.com', 'email.com']):
            continue
        if email not in filtered:
            filtered.append(email)

    return filtered


def extract_common_emails(domain: str) -> Dict[str, str]:
    """Generate common email patterns for a domain"""
    if not domain:
        return {}

    return {
        "founders": f"founders@{domain}",
        "hello": f"hello@{domain}",
        "contact": f"contact@{domain}",
        "info": f"info@{domain}",
        "support": f"support@{domain}",
    }


# ─── Hunter.io Integration ────────────────────────────────────────────────────

def hunter_domain_search(domain: str) -> Dict:
    """
    Use Hunter.io Domain Search API to find all emails at a company
    Returns: {emails: [], pattern: str, organization: str}
    """
    if not HUNTER_API_KEY or not domain:
        return {"emails": [], "pattern": None}

    try:
        resp = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={
                "domain": domain,
                "api_key": HUNTER_API_KEY,
                "limit": 20
            },
            timeout=15
        )
        data = resp.json()

        if data.get("data"):
            return {
                "emails": data["data"].get("emails", []),
                "pattern": data["data"].get("pattern"),
                "organization": data["data"].get("organization"),
                "domain": domain
            }
    except Exception as e:
        print(f"  ⚠️ Hunter error for {domain}: {e}")

    return {"emails": [], "pattern": None}


def hunter_email_finder(domain: str, first_name: str, last_name: str) -> Optional[str]:
    """Use Hunter.io Email Finder to guess a specific email"""
    if not HUNTER_API_KEY or not domain or not first_name:
        return None

    try:
        resp = requests.get(
            "https://api.hunter.io/v2/email-finder",
            params={
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name,
                "api_key": HUNTER_API_KEY
            },
            timeout=10
        )
        data = resp.json()

        if data.get("data") and data["data"].get("email"):
            email = data["data"]["email"]
            score = data["data"].get("score", 0)
            if score >= 50:  # Confidence threshold
                return email
    except Exception as e:
        pass

    return None


# ─── URL Builders ───────────────────────────────────────────────────────────────

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


def build_company_linkedin(name: str) -> str:
    """Build company LinkedIn URL from name"""
    if not name:
        return ""
    clean = re.sub(r'[^\w\s-]', '', name.lower())
    clean = clean.replace(" ", "-").replace("--", "-")
    return f"https://linkedin.com/company/{clean}"


def build_founder_linkedin(name: str, company: str) -> str:
    """Build likely founder LinkedIn URL"""
    if not name:
        return ""
    clean = name.lower().replace(".", "").replace("-", " ")
    parts = clean.split()

    if len(parts) >= 2:
        slug = f"{parts[0]}-{parts[-1]}"
        return f"https://linkedin.com/in/{slug}"
    return ""


# ─── YC API Fetch ───────────────────────────────────────────────────────────────

def fetch_yc_companies() -> List[Dict]:
    """Fetch all YC companies"""
    print("🚀 Fetching YC companies...")
    url = "https://yc-oss.github.io/api/companies/all.json"
    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def fetch_company_details(company_slug: str, batch: str) -> Dict:
    """Fetch full company details including founders"""
    batch_slug = batch.lower().replace(" ", "-")
    url = f"https://yc-oss.github.io/api/batches/{batch_slug}/{company_slug}.json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return {}


# ─── Lead Processing ────────────────────────────────────────────────────────────

def process_company(company: Dict) -> Optional[Dict]:
    """Process a single company and return enriched lead"""
    batch = company.get("batch", "")

    # Filter by batch
    if not any(b in batch for b in TARGET_BATCHES):
        return None

    name = company.get("name", "")
    website = company.get("website", "")
    domain = extract_domain(website)
    description = company.get("long_description", "") or company.get("one_liner", "")

    # Extract emails from description
    found_emails = extract_emails_from_text(description)
    company_email = found_emails[0] if found_emails else None

    # Build LinkedIn URLs
    company_linkedin = build_company_linkedin(name)

    # Hunter.io enrichment (if API key available)
    hunter_data = {"emails": [], "pattern": None}
    if HUNTER_API_KEY and domain:
        hunter_data = hunter_domain_search(domain)
        time.sleep(0.5)  # Rate limiting

    # Combine all emails
    all_emails = {
        "from_description": found_emails,
        "from_hunter": [e.get("value") for e in hunter_data.get("emails", [])],
        "common": extract_common_emails(domain),
        "pattern": hunter_data.get("pattern")
    }

    return {
        "id": f"yc_{company.get('id')}",
        "source": f"yc_{batch}",
        "company_name": name,
        "company_website": website,
        "company_domain": domain,
        "company_description": description[:500],
        "company_linkedin": company_linkedin,
        "company_email": company_email,
        "batch": batch,
        "industry": company.get("tags", []),
        "location": company.get("all_locations") or company.get("location"),
        "team_size": company.get("team_size"),
        "stage": company.get("stage"),
        "is_hiring": company.get("isHiring", False),
        "top_company": company.get("top_company", False),
        "all_emails": all_emails,
        "status": "new",
        "score": 90 if company.get("top_company") else 80,
        "extracted_at": datetime.now().isoformat(),
    }


# ─── CRM Integration ────────────────────────────────────────────────────────────

def load_crm() -> List[Dict]:
    if CRM_CLIENTS_FILE.exists():
        try:
            with open(CRM_CLIENTS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []


def save_crm(clients: List[Dict]):
    CRM_CLIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CRM_CLIENTS_FILE, 'w') as f:
        json.dump(clients, f, indent=2, default=str)


def convert_to_crm(lead: Dict) -> Dict:
    """Convert lead to CRM format with full contact info"""
    emails = lead.get("all_emails", {})

    # Build contact info section
    contact_info = f"""🚀 YC {lead.get('batch', 'N/A')}
📍 Location: {lead.get('location', 'N/A')}
👥 Team: {lead.get('team_size', 'N/A')} | Stage: {lead.get('stage', 'N/A')}
💼 Hiring: {'Yes' if lead.get('is_hiring') else 'No'}

🔗 Links:
   Website: {lead.get('company_website', 'N/A')}
   LinkedIn: {lead.get('company_linkedin', 'N/A')}

📧 Emails Found:
   From Description: {', '.join(emails.get('from_description', [])) or 'None'}
   From Hunter.io: {', '.join(emails.get('from_hunter', [])[:3]) or 'None'}
   Pattern: {emails.get('pattern') or 'Unknown'}

📝 Description:
{lead.get('company_description', '')[:300]}...
"""

    # Primary email (best guess)
    primary_email = (lead.get("company_email") or
                    emails.get("from_description", [None])[0] or
                    emails.get("from_hunter", [None])[0] or
                    emails.get("common", {}).get("founders"))

    return {
        "id": lead.get("id"),
        "name": lead.get("company_name"),
        "email": primary_email,
        "phone": "",
        "company": lead.get("company_name"),
        "source": lead.get("source", "yc"),
        "tags": lead.get("industry", []),
        "status": "lead",
        "created_at": lead.get("extracted_at"),
        "last_contact": None,
        "notes": contact_info,
        # Extra fields
        "website": lead.get("company_website"),
        "domain": lead.get("company_domain"),
        "linkedin_company": lead.get("company_linkedin"),
        "linkedin_founder": "",
        "twitter": "",
        "batch": lead.get("batch"),
        "is_hiring": lead.get("is_hiring"),
        "yc_score": lead.get("score"),
        "all_emails": emails,
    }


def push_to_crm(leads: List[Dict]) -> Dict:
    print(f"\n💾 Pushing {len(leads)} leads to CRM...")

    existing = load_crm()
    existing_ids = {c.get("id") for c in existing}

    added = 0
    new_clients = []

    for lead in leads:
        if lead.get("id") in existing_ids:
            continue

        client = convert_to_crm(lead)
        new_clients.append(client)
        existing_ids.add(lead.get("id"))
        added += 1

        if added % 50 == 0:
            print(f"  📊 {added} added...")

    all_clients = existing + new_clients
    save_crm(all_clients)

    return {"added": added, "total": len(all_clients)}


# ─── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("🚀 RAGSPRO YC Lead Scraper v4.0")
    print("📧 Email extraction + Hunter.io integration")
    print("=" * 60)

    if not HUNTER_API_KEY:
        print("\n⚠️  HUNTER_API_KEY not set - email enrichment limited")
        print("   Add to .env: HUNTER_API_KEY=your_key_here")
    else:
        print(f"\n✅ Hunter.io enabled (API key: ...{HUNTER_API_KEY[-4:]})")

    # Fetch companies
    companies = fetch_yc_companies()
    if not companies:
        print("❌ No data fetched")
        return
    print(f"✅ Total companies: {len(companies)}")

    # Process each company
    print(f"\n🔍 Processing companies (batches: {TARGET_BATCHES})...")
    leads = []

    for i, company in enumerate(companies):
        lead = process_company(company)
        if lead:
            leads.append(lead)

        if (i + 1) % 500 == 0:
            print(f"  Processed {i+1}/{len(companies)}...")

    print(f"✅ Found {len(leads)} leads from target batches")

    # Push to CRM
    stats = push_to_crm(leads)

    # Summary
    print("\n" + "=" * 60)
    print("🎉 DONE!")
    print("=" * 60)
    print(f"📊 New leads: {stats['added']}")
    print(f"📊 Total in CRM: {stats['total']}")

    # Show sample
    if leads:
        sample = leads[0]
        emails = sample.get("all_emails", {})
        print(f"\n📋 Sample: {sample['company_name']}")
        print(f"   Website: {sample.get('company_website')}")
        print(f"   LinkedIn: {sample.get('company_linkedin')}")
        print(f"   Emails from desc: {emails.get('from_description', [])[:2]}")
        print(f"   Emails from Hunter: {emails.get('from_hunter', [])[:2]}")

    print(f"\n💡 Next steps:")
    print(f"   1. Open Agency OS → Clients page")
    print(f"   2. Click on any YC lead to see full contact info")
    print(f"   3. Use 'company_email' or emails from notes")


if __name__ == "__main__":
    main()
