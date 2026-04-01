#!/usr/bin/env python3
"""
RAGSPRO Opportunity Finder — Daily income opportunities
Reddit + IndieHackers + Fiverr trends
"""

import json
import requests
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict

DATA_DIR = Path(__file__).parent.parent / "data"
OPPORTUNITIES_FILE = DATA_DIR / "opportunities.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def load_opportunities() -> List[Dict]:
    """Load existing opportunities"""
    if OPPORTUNITIES_FILE.exists():
        try:
            with open(OPPORTUNITIES_FILE, 'r') as f:
                data = json.load(f)
                return data.get("opportunities", [])
        except:
            pass
    return []


def save_opportunities(opps: List[Dict]):
    """Save opportunities"""
    OPPORTUNITIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "opportunities": opps,
        "last_updated": datetime.now().isoformat()
    }
    with open(OPPORTUNITIES_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def scan_reddit_forhire() -> List[Dict]:
    """Scan r/forhire for AI/automation jobs"""
    opps = []
    try:
        url = "https://www.reddit.com/r/forhire/search.json?q=AI+automation+developer&sort=new&limit=10"
        response = requests.get(url, headers=HEADERS, timeout=30)

        if response.status_code != 200:
            return opps

        data = response.json()
        posts = data.get("data", {}).get("children", [])

        for post_data in posts:
            post = post_data.get("data", {})
            title = post.get("title", "")

            if not title.startswith("[Hiring]"):
                continue

            budget_match = re.search(r'\$([\d,]+)', title + post.get("selftext", ""))
            budget = int(budget_match.group(1).replace(',', '')) if budget_match else 0

            if budget < 500:
                continue

            opp = {
                "id": f"reddit_{post.get('id', '')}",
                "title": title[:80],
                "source": "Reddit r/forhire",
                "source_url": f"https://reddit.com{post.get('permalink', '')}",
                "niche": "AI/Automation",
                "type": "hiring_post",
                "description": post.get("selftext", "")[:200],
                "budget": budget,
                "price_point": f"${budget}",
                "income_score": min(budget // 500, 10),
                "effort_score": 6,
                "roi": round((budget / 500) * 1.5, 1),
                "competition": "medium",
                "validated": True,
                "discovered_at": datetime.now().isoformat(),
                "action_required": "Send DM/application"
            }
            opps.append(opp)

    except Exception as e:
        print(f"Reddit error: {e}")

    return opps


def scan_indiehackers() -> List[Dict]:
    """Scan r/indiehackers for startup help"""
    opps = []
    try:
        url = "https://www.reddit.com/r/indiehackers/new.json?limit=15"
        response = requests.get(url, headers=HEADERS, timeout=30)

        if response.status_code != 200:
            return opps

        data = response.json()
        posts = data.get("data", {}).get("children", [])

        for post_data in posts:
            post = post_data.get("data", {})
            title = post.get("title", "").lower()
            text = post.get("selftext", "").lower()

            signals = ["looking for developer", "need developer", "build my", "need help"]
            if not any(s in title + text for s in signals):
                continue

            opp = {
                "id": f"ih_{post.get('id', '')}",
                "title": post.get("title", "")[:80],
                "source": "IndieHackers",
                "source_url": f"https://reddit.com{post.get('permalink', '')}",
                "niche": "Startup MVP",
                "type": "startup_help",
                "description": post.get("selftext", "")[:200],
                "price_point": "$1,000 - $10,000",
                "income_score": 7,
                "effort_score": 7,
                "roi": 8.0,
                "competition": "low",
                "validated": True,
                "discovered_at": datetime.now().isoformat(),
                "action_required": "Comment + DM author"
            }
            opps.append(opp)

    except Exception as e:
        print(f"IndieHackers error: {e}")

    return opps


def get_competitor_gaps() -> List[Dict]:
    """Hardcoded competitor gaps"""
    return [
        {
            "id": "comp_builderai",
            "title": "Gap: Builder.ai too expensive ($5K-50K+)",
            "source": "Competitor Analysis",
            "source_url": "https://builder.ai",
            "niche": "SMB AI Apps",
            "type": "competitor_gap",
            "description": "Builder.ai charges $5K-50K+. You can do same at 1/3 price.",
            "suggested_service": "AI apps at ₹50K-2L ($600-2400)",
            "price_point": "₹50,000 - ₹2,00,000",
            "income_score": 9,
            "effort_score": 6,
            "roi": 9.5,
            "competition": "medium",
            "validated": True,
            "discovered_at": datetime.now().isoformat(),
            "action_required": "Update pricing page"
        },
        {
            "id": "comp_fiverr",
            "title": "Gap: Fiverr AI quality issues",
            "source": "Competitor Analysis",
            "source_url": "https://fiverr.com",
            "niche": "Professional AI",
            "type": "competitor_gap",
            "description": "Fiverr has cheap AI devs but quality issues. Position as premium.",
            "suggested_service": "Professional AI with support",
            "price_point": "$500 - $5,000",
            "income_score": 7,
            "effort_score": 5,
            "roi": 8.0,
            "competition": "high",
            "validated": True,
            "discovered_at": datetime.now().isoformat(),
            "action_required": "Create Fiverr gig"
        }
    ]


def find_opportunities() -> List[Dict]:
    """Find all opportunities"""
    print("🔍 Finding opportunities...")

    all_opps = []

    # Scan sources
    all_opps.extend(scan_reddit_forhire())
    all_opps.extend(scan_indiehackers())
    all_opps.extend(get_competitor_gaps())

    # Merge with existing
    existing = load_opportunities()
    existing_ids = {o.get("id") for o in existing}
    new_opps = [o for o in all_opps if o.get("id") not in existing_ids]

    # Keep last 50
    combined = existing + new_opps
    combined = combined[-50:]

    save_opportunities(combined)

    print(f"✅ Found {len(new_opps)} new opportunities")
    print(f"📊 Total: {len(combined)}")

    return new_opps


def get_daily_brief() -> str:
    """Get brief for Raghav"""
    opps = load_opportunities()
    opps.sort(key=lambda x: x.get("roi", 0), reverse=True)

    lines = ["🎯 Top Opportunities:", ""]
    for i, opp in enumerate(opps[:3], 1):
        lines.append(f"{i}. {opp['title']}")
        lines.append(f"   Budget: {opp.get('price_point', 'N/A')} | ROI: {opp.get('roi', 0)}")
        lines.append(f"   Action: {opp['action_required']}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    find_opportunities()
    print("\n" + get_daily_brief())
