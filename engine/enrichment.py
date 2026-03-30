#!/usr/bin/env python3
"""
RAGSPRO Lead Enrichment Engine
Find verified emails and phones using Hunter.io, Apollo.io, Clearbit
+ Email permutation + MX verification
"""

import json
import re
import time
import dns.resolver
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR

# API Keys (loaded from env via config)
import os
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")
CLEARBIT_API_KEY = os.getenv("CLEARBIT_API_KEY", "")

LEADS_FILE = DATA_DIR / "leads.json"
ENRICHMENT_LOG_FILE = DATA_DIR / "enrichment_log.json"

# Rate limiting tracking
_hunter_last_call = 0
_apollo_last_call = 0
_clearbit_last_call = 0


def _rate_limit_hunter():
    """Hunter.io: 1 request per second on free tier"""
    global _hunter_last_call
    elapsed = time.time() - _hunter_last_call
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    _hunter_last_call = time.time()


def _rate_limit_apollo():
    """Apollo.io: reasonable rate limiting"""
    global _apollo_last_call
    elapsed = time.time() - _apollo_last_call
    if elapsed < 0.5:
        time.sleep(0.5 - elapsed)
    _apollo_last_call = time.time()


def _rate_limit_clearbit():
    """Clearbit: 1 request per second"""
    global _clearbit_last_call
    elapsed = time.time() - _clearbit_last_call
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    _clearbit_last_call = time.time()


def extract_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from LinkedIn or website URL"""
    if not url:
        return None

    # Clean up URL
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    # Extract domain
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www.
        if domain.startswith("www."):
            domain = domain[4:]
        return domain if domain else None
    except:
        return None


def extract_company_from_text(text: str) -> Optional[str]:
    """Extract company name from text using patterns"""
    if not text:
        return None

    text_lower = text.lower()

    # Pattern: "at CompanyName" or "with CompanyName"
    patterns = [
        r'at\s+([A-Z][A-Za-z0-9\s&]+?)(?:\s|$|\.|,|!|\?)',
        r'with\s+([A-Z][A-Za-z0-9\s&]+?)(?:\s|$|\.|,|!|\?)',
        r'from\s+([A-Z][A-Za-z0-9\s&]+?)(?:\s|$|\.|,||!|\?)',
        r'company\s*:?\s*([A-Z][A-Za-z0-9\s&]+?)(?:\s|$|\.|,|!|\?)',
        r'we\s+are\s+([A-Z][A-Za-z0-9\s&]+?)(?:\s|$|\.|,|!|\?)',
        r'our\s+company\s+([A-Z][A-Za-z0-9\s&]+?)(?:\s|$|\.|,|!|\?)',
        r'working\s+at\s+([A-Z][A-Za-z0-9\s&]+?)(?:\s|$|\.|,|!|\?)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            company = match.strip()
            # Filter out common false positives
            if company and len(company) > 2 and len(company) < 50:
                if company.lower() not in ['the', 'our', 'my', 'this', 'that', 'your', 'we', 'they']:
                    return company

    return None


def extract_name_from_title_or_text(title: str, text: str) -> Tuple[str, str]:
    """Extract first and last name from title or text"""
    full_text = f"{title} {text}" if text else title

    # Look for "I'm [Name]" or "I am [Name]" or "My name is [Name]"
    patterns = [
        r"[Ii]'m\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)",
        r"[Ii]\s+am\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)",
        r"[Mm]y\s+name\s+is\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)",
        r"[Cc]ontact\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)",
        r"[Rr]each\s+out\s+to\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, full_text)
        if match:
            return match.group(1), match.group(2)

    return "", ""


def generate_email_permutations(first: str, last: str, domain: str) -> List[str]:
    """Generate common email patterns"""
    if not domain or (not first and not last):
        return []

    first = first.lower().replace(" ", "")
    last = last.lower().replace(" ", "")
    first_initial = first[0] if first else ""
    last_initial = last[0] if last else ""

    patterns = [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first}_{last}@{domain}",
        f"{first}-{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{first_initial}{last}@{domain}",
        f"{first}{last_initial}@{domain}",
        f"{first_initial}.{last}@{domain}",
        f"{first}.{last_initial}@{domain}",
        f"{last}@{domain}",
        f"{first_initial}{last_initial}@{domain}",
        f"{first}-{last_initial}@{domain}",
        f"{first}_{last_initial}@{domain}",
    ]

    return list(set(patterns))


def verify_mx_record(domain: str) -> bool:
    """Check if domain has valid MX records"""
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return len(answers) > 0
    except:
        return False


def verify_email_smtp(email: str, timeout: int = 5) -> Dict:
    """
    Verify email via SMTP without sending
    Returns: {"valid": bool, "reason": str}
    """
    import smtplib
    import socket

    try:
        domain = email.split('@')[1]

        # Get MX records
        records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange)

        # Try SMTP connection
        server = smtplib.SMTP(timeout=timeout)
        server.connect(mx_record)
        server.helo(server.local_hostname)
        server.mail('me@example.com')
        code, message = server.rcpt(email)
        server.quit()

        if code == 250:
            return {"valid": True, "reason": "SMTP verified"}
        else:
            return {"valid": False, "reason": f"SMTP rejected: {code}"}

    except Exception as e:
        return {"valid": False, "reason": f"Verification failed: {str(e)[:50]}"}


def hunter_domain_search(domain: str) -> Dict:
    """
    Search Hunter.io for emails by domain
    Free tier: 50 requests/month, 1/sec rate limit
    """
    if not HUNTER_API_KEY:
        return {"success": False, "error": "Hunter API key not configured", "emails": []}

    _rate_limit_hunter()

    try:
        url = "https://api.hunter.io/v2/domain-search"
        params = {
            "domain": domain,
            "api_key": HUNTER_API_KEY,
            "limit": 10
        }

        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        if response.status_code == 200:
            emails = []
            for email in data.get("data", {}).get("emails", []):
                emails.append({
                    "email": email.get("value"),
                    "type": email.get("type", "work"),
                    "confidence": email.get("confidence", 0),
                    "first_name": email.get("first_name", ""),
                    "last_name": email.get("last_name", ""),
                    "position": email.get("position", ""),
                    "source": "hunter.io"
                })

            return {
                "success": True,
                "emails": emails,
                "domain": domain,
                "organization": data.get("data", {}).get("organization", "")
            }
        else:
            return {
                "success": False,
                "error": data.get("errors", [{}])[0].get("details", "Unknown error"),
                "emails": []
            }

    except Exception as e:
        return {"success": False, "error": str(e), "emails": []}


def apollo_enrich_lead(name: str, company: str, linkedin_url: str = "") -> Dict:
    """
    Enrich lead via Apollo.io
    Free tier: 50 credits/month
    """
    if not APOLLO_API_KEY:
        return {"success": False, "error": "Apollo API key not configured", "emails": [], "phones": []}

    _rate_limit_apollo()

    try:
        url = "https://api.apollo.io/v1/people/match"
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": APOLLO_API_KEY
        }

        payload = {}
        if name:
            parts = name.split()
            if len(parts) >= 2:
                payload["first_name"] = parts[0]
                payload["last_name"] = " ".join(parts[1:])
        if company:
            payload["organization_name"] = company
        if linkedin_url:
            payload["linkedin_url"] = linkedin_url

        if not payload:
            return {"success": False, "error": "No data to enrich", "emails": [], "phones": []}

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        data = response.json()

        if response.status_code == 200:
            person = data.get("person", {})

            emails = []
            if person.get("email"):
                emails.append({
                    "email": person["email"],
                    "type": "work",
                    "confidence": 95,
                    "first_name": person.get("first_name", ""),
                    "last_name": person.get("last_name", ""),
                    "source": "apollo.io"
                })

            phones = []
            if person.get("phone_number"):
                phones.append({
                    "phone": person["phone_number"],
                    "type": "work",
                    "source": "apollo.io"
                })

            return {
                "success": True,
                "emails": emails,
                "phones": phones,
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "title": person.get("title", ""),
                "company": person.get("organization", {}).get("name", company) if person.get("organization") else company
            }
        else:
            return {
                "success": False,
                "error": data.get("error", "Unknown error"),
                "emails": [],
                "phones": []
            }

    except Exception as e:
        return {"success": False, "error": str(e), "emails": [], "phones": []}


def clearbit_enrich_domain(domain: str) -> Dict:
    """
    Enrich company data via Clearbit
    Free tier: 20 requests/month
    """
    if not CLEARBIT_API_KEY:
        return {"success": False, "error": "Clearbit API key not configured"}

    _rate_limit_clearbit()

    try:
        url = f"https://company.clearbit.com/v2/companies/find"
        headers = {"Authorization": f"Bearer {CLEARBIT_API_KEY}"}
        params = {"domain": domain}

        response = requests.get(url, headers=headers, params=params, timeout=30)
        data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "name": data.get("name", ""),
                "domain": data.get("domain", domain),
                "industry": data.get("category", {}).get("industry", ""),
                "employees": data.get("metrics", {}).get("employees", 0),
                "linkedin": data.get("linkedin", {}).get("handle", ""),
                "source": "clearbit"
            }
        else:
            return {
                "success": False,
                "error": data.get("error", {}).get("message", "Unknown error")
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


def enrich_lead(lead: Dict, use_apollo: bool = True, use_hunter: bool = True) -> Dict:
    """
    Main enrichment function - tries multiple sources
    Returns enriched lead dict with new contact info
    """
    result = {
        "lead_id": lead.get("id"),
        "enriched_at": datetime.now().isoformat(),
        "sources_used": [],
        "emails_found": [],
        "phones_found": [],
        "company_info": {},
        "score_increase": 0
    }

    # Extract current info
    contact = lead.get("contact", {})
    title = lead.get("title", "")
    requirement = lead.get("requirement", "")
    full_text = f"{title} {requirement}"

    linkedin = contact.get("linkedin", "")
    existing_email = contact.get("email", "")

    # Try to get company domain
    domain = None
    if linkedin:
        domain = extract_domain_from_url(linkedin)

    if not domain:
        company = extract_company_from_text(full_text)
        if company:
            # Try to find domain via Clearbit or guess
            clearbit_result = clearbit_enrich_domain(company.lower().replace(" ", "") + ".com")
            if clearbit_result.get("success"):
                domain = clearbit_result["domain"]
                result["company_info"] = clearbit_result
                result["sources_used"].append("clearbit")

    # Get name for enrichment
    first, last = extract_name_from_title_or_text(title, requirement)
    if not first:
        name = lead.get("name", "")
        if name and name != "unknown":
            parts = name.replace("u/", "").replace("_", " ").split()
            if len(parts) >= 2:
                first, last = parts[0], parts[-1]
            elif parts:
                first = parts[0]

    # 1. Try Apollo.io (most accurate for B2B)
    if use_apollo and APOLLO_API_KEY:
        company_name = result.get("company_info", {}).get("name") or extract_company_from_text(full_text) or ""
        apollo_result = apollo_enrich_lead(
            name=f"{first} {last}".strip() if first else lead.get("name", ""),
            company=company_name,
            linkedin_url=linkedin
        )

        if apollo_result.get("success"):
            result["sources_used"].append("apollo")
            for email in apollo_result.get("emails", []):
                result["emails_found"].append(email)
            for phone in apollo_result.get("phones", []):
                result["phones_found"].append(phone)

    # 2. Try Hunter.io for domain-based search
    if use_hunter and HUNTER_API_KEY and domain and len(result["emails_found"]) < 3:
        hunter_result = hunter_domain_search(domain)
        if hunter_result.get("success"):
            result["sources_used"].append("hunter")
            for email in hunter_result.get("emails", []):
                # Avoid duplicates
                if email["email"] not in [e["email"] for e in result["emails_found"]]:
                    result["emails_found"].append(email)

    # 3. Email permutation as fallback
    if domain and first and len(result["emails_found"]) == 0:
        permutations = generate_email_permutations(first, last, domain)
        verified_any = False

        for email in permutations[:5]:  # Check first 5 to save time
            mx_valid = verify_mx_record(domain)
            if mx_valid:
                # Add as "guessed" with lower confidence
                result["emails_found"].append({
                    "email": email,
                    "type": "guessed",
                    "confidence": 50,
                    "first_name": first,
                    "last_name": last,
                    "source": "permutation"
                })
                verified_any = True

        if verified_any:
            result["sources_used"].append("permutation")

    # Calculate score increase
    if result["emails_found"]:
        verified = len([e for e in result["emails_found"] if e.get("confidence", 0) >= 80])
        guessed = len([e for e in result["emails_found"] if e.get("confidence", 0) < 80])
        result["score_increase"] = verified * 50 + guessed * 30

    if result["phones_found"]:
        result["score_increase"] += len(result["phones_found"]) * 30

    return result


def update_lead_with_enrichment(lead: Dict, enrichment: Dict) -> Dict:
    """Merge enrichment results into lead dict"""
    if not enrichment.get("emails_found") and not enrichment.get("phones_found"):
        return lead

    contact = lead.get("contact", {})

    # Add emails
    all_emails = contact.get("emails", [])
    if isinstance(all_emails, str):
        all_emails = [all_emails] if all_emails else []

    for email_data in enrichment.get("emails_found", []):
        email = email_data.get("email")
        if email and email not in all_emails:
            all_emails.append(email)

    # Add phones
    all_phones = contact.get("phones", [])
    if isinstance(all_phones, str):
        all_phones = [all_phones] if all_phones else []

    for phone_data in enrichment.get("phones_found", []):
        phone = phone_data.get("phone")
        if phone and phone not in all_phones:
            all_phones.append(phone)

    # Update contact
    contact["emails"] = all_emails
    contact["phones"] = all_phones

    # Set primary email/phone if empty
    if not contact.get("email") and all_emails:
        # Prefer highest confidence
        best = max(enrichment.get("emails_found", []), key=lambda x: x.get("confidence", 0), default={})
        contact["email"] = best.get("email", all_emails[0])

    if not contact.get("phone") and all_phones:
        contact["phone"] = all_phones[0]

    lead["contact"] = contact

    # Update score
    lead["score"] = lead.get("score", 0) + enrichment.get("score_increase", 0)

    # Mark as enriched
    lead["enriched_at"] = enrichment.get("enriched_at")
    lead["enrichment_sources"] = enrichment.get("sources_used", [])

    return lead


def log_enrichment(lead_id: str, enrichment: Dict):
    """Log enrichment attempt"""
    log = []
    if ENRICHMENT_LOG_FILE.exists():
        try:
            with open(ENRICHMENT_LOG_FILE, 'r') as f:
                log = json.load(f)
        except:
            log = []

    log.append({
        "lead_id": lead_id,
        "timestamp": datetime.now().isoformat(),
        "emails_found": len(enrichment.get("emails_found", [])),
        "phones_found": len(enrichment.get("phones_found", [])),
        "sources": enrichment.get("sources_used", []),
        "score_increase": enrichment.get("score_increase", 0)
    })

    ENRICHMENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ENRICHMENT_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2, default=str)


def enrich_single_lead(lead_id: str) -> Dict:
    """Enrich a single lead by ID and save to DB"""
    # Load leads
    leads = []
    if LEADS_FILE.exists():
        with open(LEADS_FILE, 'r') as f:
            leads = json.load(f)

    # Find lead
    lead = None
    for l in leads:
        if l.get("id") == lead_id:
            lead = l
            break

    if not lead:
        return {"success": False, "error": "Lead not found"}

    # Enrich
    enrichment = enrich_lead(lead, use_apollo=True, use_hunter=True)

    # Update lead
    updated_lead = update_lead_with_enrichment(lead, enrichment)

    # Save
    for i, l in enumerate(leads):
        if l.get("id") == lead_id:
            leads[i] = updated_lead
            break

    with open(LEADS_FILE, 'w') as f:
        json.dump(leads, f, indent=2, default=str)

    # Log
    log_enrichment(lead_id, enrichment)

    return {
        "success": True,
        "emails_found": len(enrichment.get("emails_found", [])),
        "phones_found": len(enrichment.get("phones_found", [])),
        "sources": enrichment.get("sources_used", []),
        "score_increase": enrichment.get("score_increase", 0)
    }


def get_enrichment_stats() -> Dict:
    """Get enrichment statistics"""
    leads = []
    if LEADS_FILE.exists():
        with open(LEADS_FILE, 'r') as f:
            leads = json.load(f)

    enriched = [l for l in leads if l.get("enriched_at")]
    with_emails = [l for l in leads if l.get("contact", {}).get("email")]
    with_phones = [l for l in leads if l.get("contact", {}).get("phone")]

    return {
        "total_leads": len(leads),
        "enriched_leads": len(enriched),
        "leads_with_emails": len(with_emails),
        "leads_with_phones": len(with_phones),
        "enrichment_rate": len(enriched) / len(leads) * 100 if leads else 0,
        "contact_rate": len(with_emails) / len(leads) * 100 if leads else 0
    }


if __name__ == "__main__":
    # Test enrichment
    print("🎯 RAGSPRO Lead Enrichment Engine")
    print("=" * 50)

    # Check API keys
    print(f"\nAPI Status:")
    print(f"  Hunter.io: {'✅' if HUNTER_API_KEY else '❌ Not configured'}")
    print(f"  Apollo.io: {'✅' if APOLLO_API_KEY else '❌ Not configured'}")
    print(f"  Clearbit: {'✅' if CLEARBIT_API_KEY else '❌ Not configured'}")

    # Show stats
    stats = get_enrichment_stats()
    print(f"\n📊 Enrichment Stats:")
    print(f"  Total leads: {stats['total_leads']}")
    print(f"  Enriched: {stats['enriched_leads']} ({stats['enrichment_rate']:.1f}%)")
    print(f"  With emails: {stats['leads_with_emails']} ({stats['contact_rate']:.1f}%)")
    print(f"  With phones: {stats['leads_with_phones']}")

    print("\n✅ Enrichment module ready")
