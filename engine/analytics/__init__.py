#!/usr/bin/env python3
"""
RAGSPRO Analytics Module
Track all marketing metrics and generate reports
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR

ANALYTICS_FILE = DATA_DIR / "marketing_analytics.json"
REPORTS_DIR = DATA_DIR / "reports"


@dataclass
class MetricSnapshot:
    """Single point-in-time metric"""
    timestamp: str
    platform: str
    metric_name: str
    value: float
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MarketingAnalytics:
    """Track and analyze all marketing metrics"""

    def __init__(self):
        self.data_file = ANALYTICS_FILE
        self.reports_dir = REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def record_metric(self, platform: str, metric: str, value: float, metadata: Dict = None):
        """Record a metric snapshot"""
        snapshot = MetricSnapshot(
            timestamp=datetime.now().isoformat(),
            platform=platform,
            metric_name=metric,
            value=value,
            metadata=metadata or {}
        )

        # Load existing
        data = self._load_data()

        if platform not in data:
            data[platform] = {}
        if metric not in data[platform]:
            data[platform][metric] = []

        data[platform][metric].append(asdict(snapshot))

        # Save
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_data(self) -> Dict:
        """Load analytics data"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {}

    def get_metric_history(self, platform: str, metric: str, days: int = 30) -> List[Dict]:
        """Get metric history for time period"""
        data = self._load_data()
        history = data.get(platform, {}).get(metric, [])

        # Filter by date
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        return [h for h in history if h.get("timestamp", "") > cutoff]

    def get_latest_value(self, platform: str, metric: str) -> Optional[float]:
        """Get latest metric value"""
        history = self.get_metric_history(platform, metric, days=365)
        if history:
            return history[-1].get("value")
        return None

    def calculate_growth(self, platform: str, metric: str, days: int = 30) -> float:
        """Calculate growth rate over period"""
        history = self.get_metric_history(platform, metric, days)
        if len(history) < 2:
            return 0.0

        old = history[0].get("value", 0)
        new = history[-1].get("value", 0)

        if old == 0:
            return 100.0 if new > 0 else 0.0

        return ((new - old) / old) * 100

    def generate_daily_report(self) -> Dict:
        """Generate daily marketing report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "period": "daily",
            "metrics": {}
        }

        # Lead metrics
        leads_file = DATA_DIR / "leads.json"
        if leads_file.exists():
            with open(leads_file) as f:
                leads = json.load(f)

            new_today = len([l for l in leads if l.get("status") == "NEW"])
            contacted = len([l for l in leads if l.get("status") == "CONTACTED"])
            hot = len([l for l in leads if l.get("status") == "HOT_LEAD"])

            report["metrics"]["leads"] = {
                "total": len(leads),
                "new_today": new_today,
                "contacted": contacted,
                "hot_leads": hot
            }

        # Email metrics
        email_log = DATA_DIR / "email_automation_log.json"
        if email_log.exists():
            with open(email_log) as f:
                emails = json.load(f)

            today = datetime.now().strftime("%Y-%m-%d")
            sent_today = sum(
                1 for lead_emails in emails.values()
                for e in lead_emails
                if today in e.get("sent_at", "")
            )

            report["metrics"]["emails"] = {
                "sent_today": sent_today
            }

        # Content metrics
        queue_file = DATA_DIR / "content_queue.json"
        if queue_file.exists():
            with open(queue_file) as f:
                content = json.load(f)

            scheduled = len([c for c in content if c.get("status") == "scheduled"])
            posted = len([c for c in content if c.get("status") == "posted"])

            report["metrics"]["content"] = {
                "scheduled": scheduled,
                "posted": posted
            }

        return report

    def generate_weekly_report(self) -> Dict:
        """Generate weekly marketing report"""
        daily = self.generate_daily_report()

        report = {
            "generated_at": datetime.now().isoformat(),
            "period": "weekly",
            "summary": daily["metrics"],
            "insights": [],
            "recommendations": []
        }

        # Generate insights
        if daily["metrics"].get("leads", {}).get("new_today", 0) > 10:
            report["insights"].append("High lead generation day! Consider scaling this source.")

        if daily["metrics"].get("emails", {}).get("sent_today", 0) == 0:
            report["recommendations"].append("Email automation may be paused. Check scheduler.")

        report["recommendations"].extend([
            "Review top-performing content and create similar pieces",
            "Engage with new followers within 1 hour for algorithm boost",
            "Schedule next week's content calendar",
            "Follow up on hot leads from this week"
        ])

        return report

    def save_report(self, report: Dict, report_type: str = "daily"):
        """Save report to file"""
        date_str = datetime.now().strftime("%Y%m%d")
        filename = self.reports_dir / f"{report_type}_report_{date_str}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

    def get_all_reports(self) -> List[Path]:
        """Get list of all saved reports"""
        return sorted(self.reports_dir.glob("*.json"), reverse=True)


class CompetitorBenchmark:
    """Benchmark against competitors"""

    COMPETITORS = {
        "codingninjas": {"followers": 50000, "engagement": 2.5},
        "scaler.official": {"followers": 100000, "engagement": 3.0},
        "thearvindgupta": {"followers": 25000, "engagement": 4.5},
    }

    def get_benchmark(self, our_followers: int, our_engagement: float) -> Dict:
        """Compare against competitors"""
        avg_comp_followers = sum(c["followers"] for c in self.COMPETITORS.values()) / len(self.COMPETITORS)
        avg_comp_engagement = sum(c["engagement"] for c in self.COMPETITORS.values()) / len(self.COMPETITORS)

        return {
            "our_followers": our_followers,
            "avg_competitor_followers": avg_comp_followers,
            "follower_gap": our_followers - avg_comp_followers,
            "our_engagement": our_engagement,
            "avg_competitor_engagement": avg_comp_engagement,
            "engagement_gap": our_engagement - avg_comp_engagement,
            "status": "ahead" if our_engagement > avg_comp_engagement else "behind"
        }


# Convenience functions
def get_daily_report() -> Dict:
    analytics = MarketingAnalytics()
    return analytics.generate_daily_report()


def get_weekly_report() -> Dict:
    analytics = MarketingAnalytics()
    return analytics.generate_weekly_report()


def record_metric(platform: str, metric: str, value: float):
    analytics = MarketingAnalytics()
    analytics.record_metric(platform, metric, value)


if __name__ == "__main__":
    report = get_daily_report()
    print(f"Report generated with {len(report['metrics'])} metric categories")
