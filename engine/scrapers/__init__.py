#!/usr/bin/env python3
"""
RAGSPRO Unified Scraper Module
Combines: Reddit + Apify (Google Maps) + LinkedIn + Y Combinator
Single import: from engine.scrapers import UnifiedScraper
"""

import json
import re
import time
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

try:
    import requests
except ImportError:
    print("⚠️ requests not installed. Run: pip install requests")
    requests = None

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, LEAD_KEYWORDS

LEADS_FILE = DATA_DIR / "leads.json"

@dataclass
class Lead:
    """Standardized lead format across all sources"""
    id: str
    name: str
    title: str
    company: str
    requirement: str
    url: str
    platform: str
    score: int
    status: str = "NEW"
    extracted_at: str = ""
    posted_at: str = ""
    location: str = ""
    industry: str = ""
    phone: str = ""
    contact: Dict = None
    source: str = ""
    metadata: Dict = None
    pain_points: List = None
    tags: List = None

    def __post_init__(self):
        if not self.extracted_at:
            self.extracted_at = datetime.now().isoformat()
        if self.contact is None:
            self.contact = {"emails": [], "phones": [], "linkedin": "", "website": ""}
        if self.metadata is None:
            self.metadata = {}
        if self.pain_points is None:
            self.pain_points = []
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict:
        return asdict(self)


class ContactExtractor:
    """Extract contact information from text"""

    @staticmethod
    def extract_emails(text: str) -> List[str]:
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        return list(set(e for e in emails if not any(x in e.lower() for x in [
            'example.com', 'test.com', 'domain.com', 'email.com', 'linkedin.com'
        ])))

    @staticmethod
    def extract_phones(text: str) -> List[str]:
        patterns = [
            r'\+91[\s-]?\d{5}[\s-]?\d{5}',
            r'\+1[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}',
            r'\(\d{3}\)[\s-]?\d{3}[\s-]?\d{4}',
        ]
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))

    @staticmethod
    def extract_linkedin(text: str) -> List[str]:
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


class LeadScorer:
    """Score leads based on relevance to RAGSPRO services"""

    HIGH_VALUE_KEYWORDS = ["chatbot", "ai chatbot", "automation", "ai agent", "saas",
                           "web app", "webapp", "dashboard", "platform", "mvp"]
    DEV_KEYWORDS = ["website", "landing page", "react", "next.js", "nextjs",
                    "python", "node", "fullstack", "full stack", "backend",
                    "api", "scraping", "bot", "mobile app"]
    URGENCY_KEYWORDS = ["urgent", "asap", "immediately", "right away", "this week", "today"]

    @classmethod
    def score(cls, title: str, text: str = "", platform: str = "") -> int:
        score = 0
        combined = (title + " " + text).lower()

        # [HIRING] tag = highest signal
        if "[hiring]" in combined:
            score += 30

        # Budget mentions
        if re.search(r'\$[\d,]+', combined):
            score += 25
        if 'budget' in combined:
            score += 15

        # High-value keywords
        for kw in cls.HIGH_VALUE_KEYWORDS:
            if kw in combined:
                score += 20

        # Dev keywords
        for kw in cls.DEV_KEYWORDS:
            if kw in combined:
                score += 10

        # Urgency
        for kw in cls.URGENCY_KEYWORDS:
            if kw in combined:
                score += 15

        # Platform bonuses
        if platform == "LinkedIn Jobs":
            score += 10
        if platform == "Google Maps":
            score += 5

        return min(score, 100)


class RedditScraper:
    """Scrape Reddit for [HIRING] posts"""

    def __init__(self):
        if requests is None:
            raise ImportError("requests module not available. Run: pip install requests")
    """Scrape Reddit for [HIRING] posts"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    SUBREDDITS = [
        {"name": "r/forhire [HIRING]", "url": "https://www.reddit.com/r/forhire/search.json?q=flair%3AHiring&sort=new&limit=50&t=week"},
        {"name": "r/slavelabour [OFFER]", "url": "https://www.reddit.com/r/slavelabour/search.json?q=flair%3AOffer&sort=new&limit=30&t=week"},
        {"name": "r/startups hiring", "url": "https://www.reddit.com/r/startups/search.json?q=%5BHiring%5D+OR+%22we+are+hiring%22+OR+%22looking+to+hire%22&sort=new&limit=25&t=week"},
        {"name": "r/smallbusiness", "url": "https://www.reddit.com/r/smallbusiness/search.json?q=%5BHiring%5D+OR+%22need+a+website%22+OR+%22need+an+app%22+OR+%22looking+for+developer%22&sort=new&limit=25&t=week"},
        {"name": "r/entrepreneur", "url": "https://www.reddit.com/r/Entrepreneur/search.json?q=%5BHiring%5D+OR+%22need+developer%22+OR+%22need+help+building%22&sort=new&limit=25&t=week"},
        {"name": "r/indiehackers", "url": "https://www.reddit.com/r/indiehackers/search.json?q=%5BHiring%5D+OR+%22looking+for+developer%22+OR+%22need+developer%22&sort=new&limit=25&t=week"},
        {"name": "r/indianstartups", "url": "https://www.reddit.com/r/indianstartups/search.json?q=%5BHiring%5D+OR+%22we+are+hiring%22&sort=new&limit=25&t=week"},
    ]

    HIRING_SIGNALS = [
        "[hiring]", "looking to hire", "need to hire", "want to hire",
        "hiring a", "hiring for", "seeking a developer", "need a developer",
        "need developer", "need an app", "need a website", "need someone to build",
        "need help building", "job posting", "position available",
        "we are hiring", "we're hiring", "budget is", "will pay"
    ]

    REJECT_SIGNALS = [
        "[for hire]", "[forhire]", "hire me", "i am a developer",
        "i'm a freelancer", "available for work", "open to work",
        "seeking work", "my portfolio", "offering my services",
        "dm me if interested", "check out my work", "years of experience"
    ]

    def is_hiring_post(self, title: str, text: str) -> bool:
        combined = (title + " " + text[:500]).lower()

        for signal in self.REJECT_SIGNALS:
            if signal in combined:
                return False

        for signal in self.HIRING_SIGNALS:
            if signal in combined:
                return True

        has_budget = bool(re.search(r'\$[\d,]+', title)) or 'budget' in title.lower()
        return has_budget and any(x in combined for x in ["need", "looking for", "want"])

    def process_post(self, post_data: Dict, source_name: str) -> Optional[Lead]:
        post = post_data.get("data", {})
        title = post.get("title", "")
        text = post.get("selftext", "")
        author = post.get("author", "unknown")
        permalink = post.get("permalink", "")

        if not title or not self.is_hiring_post(title, text):
            return None

        score = LeadScorer.score(title, text, "Reddit")
        if score < 15:
            return None

        full_text = title + " " + text
        extractor = ContactExtractor()

        return Lead(
            id=f"reddit_{post.get('id', '')}",
            name=author,
            title=title[:150],
            company="",
            requirement=text[:600],
            url=f"https://reddit.com{permalink}",
            platform=source_name,
            score=score,
            posted_at=datetime.fromtimestamp(post.get("created_utc", 0)).isoformat() if post.get("created_utc") else "",
            contact={
                "emails": extractor.extract_emails(full_text),
                "linkedin": extractor.extract_linkedin(full_text)[0] if extractor.extract_linkedin(full_text) else "",
                "phones": extractor.extract_phones(full_text),
                "reddit_user": f"u/{author}"
            },
            source="reddit"
        )

    def scrape(self) -> List[Lead]:
        """Scrape all Reddit sources"""
        print("🔍 Scraping Reddit for [HIRING] posts...")
        new_leads = []

        for source in self.SUBREDDITS:
            try:
                response = requests.get(source["url"], headers=self.HEADERS, timeout=30)
                if response.status_code == 429:
                    time.sleep(5)
                    response = requests.get(source["url"], headers=self.HEADERS, timeout=30)

                if response.status_code != 200:
                    continue

                data = response.json()
                posts = data.get("data", {}).get("children", [])

                for post_data in posts:
                    lead = self.process_post(post_data, source["name"])
                    if lead:
                        new_leads.append(lead)

                time.sleep(2)
            except Exception as e:
                print(f"  ✗ Error scraping {source['name']}: {e}")

        return new_leads


class ApifyScraper:
    """Scrape Google Maps and LinkedIn Jobs via Apify"""

    def __init__(self):
        if requests is None:
            raise ImportError("requests module not available. Run: pip install requests")

        self.token = os.getenv("APIFY_TOKEN", "")
        if not self.token:
            env_file = Path.home() / ".apify" / "token"
            if env_file.exists():
                self.token = env_file.read_text().strip()

    def _wait_for_run(self, actor_id: str, run_id: str) -> Optional[str]:
        """Wait for Apify actor run to complete"""
        for _ in range(30):
            time.sleep(10)
            status_response = requests.get(
                f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            status = status_response.json()["data"]["status"]

            if status == "SUCCEEDED":
                return status_response.json()["data"]["defaultDatasetId"]
            elif status in ["FAILED", "TIMED-OUT", "ABORTED"]:
                return None
        return None

    def scrape_google_maps(self, query: str, max_results: int = 30) -> List[Lead]:
        """Scrape Google Maps for business leads"""
        if not self.token:
            print("⚠️ APIFY_TOKEN not set")
            return []

        print(f"🔍 Scraping Google Maps: '{query}'...")

        actor_id = "compass~crawler-google-places"
        run_response = requests.post(
            f"https://api.apify.com/v2/acts/{actor_id}/runs",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"queries": query, "maxCrawledPlaces": max_results, "language": "en", "region": "in"}
        )

        if run_response.status_code != 201:
            return []

        run_id = run_response.json()["data"]["id"]
        dataset_id = self._wait_for_run(actor_id, run_id)

        if not dataset_id:
            return []

        dataset_response = requests.get(
            f"https://api.apify.com/v2/datasets/{dataset_id}/items",
            headers={"Authorization": f"Bearer {self.token}"},
            params={"format": "json", "clean": "true"}
        )

        results = dataset_response.json()
        leads = []

        for place in results:
            lead = Lead(
                id=f"gmaps_{place.get('placeId', 'unknown')}",
                name=place.get("title", ""),
                company=place.get("title", ""),
                title=f"{place.get('title', '')} - {place.get('categoryName', 'Business')}",
                requirement=place.get("description", ""),
                industry=place.get("categoryName", ""),
                url=place.get("website", ""),
                platform="Google Maps",
                score=80 if place.get("website") else 60,
                location=place.get("address", ""),
                phone=place.get("phone", ""),
                contact={
                    "emails": [],
                    "phones": [place.get("phone", "")] if place.get("phone") else [],
                    "website": place.get("website", "")
                },
                source="apify_google_maps",
                metadata={
                    "rating": place.get("totalScore"),
                    "reviews": place.get("reviewsCount")
                }
            )
            leads.append(lead)

        return leads

    def scrape_linkedin_jobs(self, keywords: str = "AI developer", location: str = "India", max_results: int = 25) -> List[Lead]:
        """Scrape LinkedIn job postings"""
        if not self.token:
            return []

        print(f"🔍 Scraping LinkedIn Jobs: '{keywords}'...")

        actor_id = "apify~linkedin-jobs-scraper"
        run_response = requests.post(
            f"https://api.apify.com/v2/acts/{actor_id}/runs",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"searchTerms": keywords, "location": location, "maxResults": max_results}
        )

        if run_response.status_code != 201:
            return []

        run_id = run_response.json()["data"]["id"]
        dataset_id = self._wait_for_run(actor_id, run_id)

        if not dataset_id:
            return []

        dataset_response = requests.get(
            f"https://api.apify.com/v2/datasets/{dataset_id}/items",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        results = dataset_response.json()
        leads = []

        for job in results:
            lead = Lead(
                id=f"linkedin_{job.get('id', 'unknown')}",
                name=job.get("companyName", ""),
                company=job.get("companyName", ""),
                title=f"{job.get('title', '')} at {job.get('companyName', '')}",
                requirement=job.get("description", ""),
                industry=job.get("industry", ""),
                url=job.get("jobUrl", ""),
                platform="LinkedIn",
                score=85,
                location=job.get("location", ""),
                posted_at=job.get("postedAt", ""),
                contact={
                    "emails": [],
                    "website": job.get("companyUrl", "")
                },
                source="apify_linkedin",
                metadata={
                    "salary": job.get("salary"),
                    "seniority": job.get("seniorityLevel"),
                    "workType": job.get("workType")
                }
            )
            leads.append(lead)

        return leads


class UnifiedScraper:
    """Main scraper class - combines all sources"""

    def __init__(self):
        self.reddit = RedditScraper()
        self.apify = ApifyScraper()

    def _load_existing(self) -> tuple:
        """Load existing leads and IDs"""
        if LEADS_FILE.exists():
            try:
                with open(LEADS_FILE, 'r') as f:
                    existing = json.load(f)
                    return existing, {l.get("id") for l in existing}
            except:
                pass
        return [], set()

    def _save_leads(self, leads: List[Dict]):
        """Save leads to file"""
        LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LEADS_FILE, 'w') as f:
            json.dump(leads, f, indent=2, default=str)

    def scrape_reddit(self) -> List[Lead]:
        """Scrape Reddit only"""
        return self.reddit.scrape()

    def scrape_google_maps(self, queries: List[str] = None) -> List[Lead]:
        """Scrape Google Maps for multiple cities"""
        if queries is None:
            queries = [
                "software companies in Delhi",
                "software companies in Mumbai",
                "software companies in Bangalore",
                "tech startups in India"
            ]

        all_leads = []
        for query in queries:
            leads = self.apify.scrape_google_maps(query, max_results=30)
            all_leads.extend(leads)
            time.sleep(2)

        return all_leads

    def scrape_linkedin_jobs(self, keywords: List[str] = None) -> List[Lead]:
        """Scrape LinkedIn jobs with multiple keywords"""
        if keywords is None:
            keywords = ["AI developer", "chatbot developer", "automation engineer", "Next.js developer"]

        all_leads = []
        for keyword in keywords:
            leads = self.apify.scrape_linkedin_jobs(keyword, "India", 25)
            all_leads.extend(leads)
            time.sleep(2)

        return all_leads

    def run_full_scrape(self) -> Dict:
        """Run complete scraping from all sources"""
        print("=" * 60)
        print("🚀 RAGSPRO Unified Scraper - Full Run")
        print("=" * 60)

        existing, existing_ids = self._load_existing()
        all_new_leads = []
        stats = {"reddit": 0, "google_maps": 0, "linkedin": 0}

        # Reddit
        try:
            reddit_leads = self.scrape_reddit()
            for lead in reddit_leads:
                if lead.id not in existing_ids:
                    all_new_leads.append(lead)
                    existing_ids.add(lead.id)
            stats["reddit"] = len([l for l in reddit_leads if l.id in existing_ids])
            print(f"✅ Reddit: {stats['reddit']} new leads")
        except Exception as e:
            print(f"❌ Reddit error: {e}")

        # Google Maps
        try:
            gmaps_leads = self.scrape_google_maps()
            for lead in gmaps_leads:
                if lead.id not in existing_ids:
                    all_new_leads.append(lead)
                    existing_ids.add(lead.id)
            stats["google_maps"] = len([l for l in gmaps_leads if l.id in existing_ids])
            print(f"✅ Google Maps: {stats['google_maps']} new leads")
        except Exception as e:
            print(f"❌ Google Maps error: {e}")

        # LinkedIn Jobs
        try:
            linkedin_leads = self.scrape_linkedin_jobs()
            for lead in linkedin_leads:
                if lead.id not in existing_ids:
                    all_new_leads.append(lead)
                    existing_ids.add(lead.id)
            stats["linkedin"] = len([l for l in linkedin_leads if l.id in existing_ids])
            print(f"✅ LinkedIn Jobs: {stats['linkedin']} new leads")
        except Exception as e:
            print(f"❌ LinkedIn error: {e}")

        # Merge and save
        existing.extend([l.to_dict() for l in all_new_leads])
        existing.sort(key=lambda x: x.get("score", 0), reverse=True)
        self._save_leads(existing)

        total_new = len(all_new_leads)
        print(f"\n{'=' * 60}")
        print(f"✅ Total new leads: {total_new}")
        print(f"📊 Total in database: {len(existing)}")
        print(f"{'=' * 60}")

        return {
            "new_leads": total_new,
            "total_leads": len(existing),
            "by_source": stats,
            "top_leads": [l.to_dict() for l in sorted(all_new_leads, key=lambda x: x.score, reverse=True)[:5]]
        }


# Convenience function for scheduler
def run_daily_scrape() -> Dict:
    """Run daily scrape - called by scheduler"""
    scraper = UnifiedScraper()
    return scraper.run_full_scrape()


if __name__ == "__main__":
    result = run_daily_scrape()
    print(f"\nScraping complete: {result['new_leads']} new leads added")
