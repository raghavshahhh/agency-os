#!/usr/bin/env python3
"""
RAGSPRO YouTube Intelligence Module
Analyze @raghavshahh channel performance + content strategy
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import sys

try:
    import requests
except ImportError:
    requests = None

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR

YOUTUBE_FILE = DATA_DIR / "youtube_analytics.json"


@dataclass
class VideoMetrics:
    """Individual video performance"""
    video_id: str
    title: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    avg_watch_time: str = "0:00"
    ctr: float = 0.0  # Click-through rate
    published_at: str = ""
    category: str = ""  # tutorial, vlog, short, etc.
    tags: List[str] = None
    thumbnail_url: str = ""

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self):
        return asdict(self)


@dataclass
class ChannelMetrics:
    """Channel-level metrics"""
    channel_id: str
    subscriber_count: int = 0
    total_views: int = 0
    video_count: int = 0
    avg_views_per_video: int = 0
    top_performing_videos: List[Dict] = None
    best_upload_times: List[str] = None
    audience_retention: float = 0.0
    growth_rate: float = 0.0  # Subscribers per month
    recorded_at: str = ""

    def __post_init__(self):
        if self.top_performing_videos is None:
            self.top_performing_videos = []
        if self.best_upload_times is None:
            self.best_upload_times = []
        if not self.recorded_at:
            self.recorded_at = datetime.now().isoformat()

    def to_dict(self):
        return asdict(self)


class YouTubeAPI:
    """YouTube Data API wrapper"""

    def __init__(self, api_key: str = None):
        if requests is None:
            raise ImportError("requests module not available. Run: pip install requests")

        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    def get_channel_stats(self, channel_id: str) -> Optional[Dict]:
        """Get channel statistics via YouTube API"""
        if not self.api_key:
            return {"note": "Set YOUTUBE_API_KEY for real data"}

        url = f"{self.base_url}/channels"
        params = {
            "part": "statistics,snippet",
            "id": channel_id,
            "key": self.api_key
        }

        try:
            import requests
            response = requests.get(url, params=params)
            data = response.json()

            if data.get("items"):
                channel = data["items"][0]
                stats = channel["statistics"]
                return {
                    "subscriber_count": int(stats.get("subscriberCount", 0)),
                    "view_count": int(stats.get("viewCount", 0)),
                    "video_count": int(stats.get("videoCount", 0)),
                    "title": channel["snippet"]["title"],
                    "description": channel["snippet"]["description"]
                }
        except Exception as e:
            print(f"YouTube API error: {e}")

        return None


class YouTubeStrategy:
    """YouTube content strategy for RAGSPRO"""

    CONTENT_TYPES = [
        {
            "type": "Shorts",
            "frequency": "3-5 per week",
            "duration": "30-60 seconds",
            "purpose": "Reach + Subscriber growth",
            "topics": [
                "Quick AI tool demos",
                "Coding tips",
                "Day in the life",
                "Before/after automation",
                "Hot takes on tech trends"
            ]
        },
        {
            "type": "Tutorials",
            "frequency": "1 per week",
            "duration": "10-20 minutes",
            "purpose": "Authority + SEO",
            "topics": [
                "Build an AI agent from scratch",
                "n8n complete tutorial",
                "Next.js + Supabase project",
                "Python automation scripts",
                "Deploy to production guide"
            ]
        },
        {
            "type": "Build in Public",
            "frequency": "1 per week",
            "duration": "5-15 minutes",
            "purpose": "Community + Transparency",
            "topics": [
                "Building LAW AI - weekly update",
                "Client project walkthrough",
                "Revenue milestone reveals",
                "Lessons learned from failures",
                "Solo founder journey"
            ]
        },
        {
            "type": "Live Coding",
            "frequency": "1-2 per month",
            "duration": "60-90 minutes",
            "purpose": "Deep engagement",
            "topics": [
                "Build a feature live",
                "Q&A with viewers",
                "Review subscriber projects",
                "Debug production issues live"
            ]
        }
    ]

    OPTIMAL_SCHEDULE = {
        "Shorts": [
            {"day": "Monday", "time": "5:00 PM IST"},
            {"day": "Wednesday", "time": "5:00 PM IST"},
            {"day": "Friday", "time": "5:00 PM IST"}
        ],
        "Long-form": [
            {"day": "Saturday", "time": "11:00 AM IST"}
        ]
    }

    VIDEO_TEMPLATES = {
        "hook_patterns": [
            "Stop doing [task] manually...",
            "I automated my entire business in 30 days",
            "This AI tool saved me 20 hours/week",
            "The fastest way to build [thing]",
            "Why I quit [thing] for [thing]"
        ],
        "thumbnail_rules": [
            "Face + expression visible",
            "Big bold text (3-4 words max)",
            "Bright/contrasting colors",
            "Arrow pointing to important element",
            "Before/after split possible"
        ],
        "retention_hooks": [
            "But here's what nobody tells you...",
            "Wait for the part where...",
            "The mistake that cost me $X...",
            "At minute 5, I reveal..."
        ]
    }

    def get_content_calendar(self) -> Dict:
        """Generate weekly content calendar"""
        return {
            "Monday": {
                "type": "Short",
                "topic": "AI Tool Tuesday preview",
                "duration": "45s"
            },
            "Tuesday": {
                "type": "Short",
                "topic": "Quick AI tip/demo",
                "duration": "60s"
            },
            "Wednesday": {
                "type": "None",
                "topic": "Community engagement",
                "note": "Reply to comments, shorts only"
            },
            "Thursday": {
                "type": "Short",
                "topic": "Coding tip or meme",
                "duration": "30s"
            },
            "Friday": {
                "type": "Short",
                "topic": "Week wrap + preview",
                "duration": "45s"
            },
            "Saturday": {
                "type": "Long-form",
                "topic": "Tutorial or Build in Public",
                "duration": "10-20 min"
            },
            "Sunday": {
                "type": "None",
                "topic": "Rest/planning",
                "note": "Schedule next week's content"
            }
        }

    def get_video_scripts(self, video_type: str) -> Dict:
        """Get script templates for different video types"""
        scripts = {
            "ai_tool_demo": {
                "hook": "This AI tool just saved me 10 hours this week...",
                "setup": "I was spending hours on [task] every week...",
                "demo": "Here's how it works - [screen recording]",
                "benefits": "Now I can focus on [higher value task]...",
                "cta": "Follow for more AI tools that actually work"
            },
            "tutorial": {
                "hook": "Learn how to build [thing] in 10 minutes",
                "overview": "Today we'll build [thing] using [stack]",
                "steps": [
                    "Step 1: Set up the project",
                    "Step 2: Configure the basics",
                    "Step 3: Add the magic sauce",
                    "Step 4: Deploy to production"
                ],
                "common_mistakes": "Don't forget to handle [edge case]...",
                "cta": "Code in description. Subscribe for more tutorials."
            },
            "build_in_public": {
                "hook": "Week X of building [product] - here's what happened",
                "wins": "This week we shipped [feature]...",
                "challenges": "The hard part was [challenge]...",
                "metrics": "Numbers: [revenue/users/etc]",
                "next": "Next week we're tackling [thing]",
                "cta": "Follow along as we build in public"
            }
        }
        return scripts.get(video_type, {})

    def get_seo_optimization(self) -> Dict:
        """SEO best practices for YouTube"""
        return {
            "title_template": "[Result] in [Timeframe] | [Specific Method]",
            "title_examples": [
                "I Built an AI Agent in 30 Minutes (Full Tutorial)",
                "10x Your Productivity with These 5 AI Tools",
                "From Zero to $10k MRR: My SaaS Journey Month 1"
            ],
            "description_structure": [
                "Hook (first 2 lines visible)",
                "Timestamps",
                "Key resources/links",
                "About channel",
                "Hashtags"
            ],
            "tags_strategy": [
                "1-2 broad tags (programming, development)",
                "2-3 specific tags (nextjs, python tutorial)",
                "1-2 trending tags if relevant",
                "Channel name as tag"
            ],
            "end_screen_elements": [
                "Subscribe button",
                "Best performing video",
                "Recent upload"
            ]
        }


class CompetitorChannels:
    """Track competitor YouTube channels"""

    COMPETITORS = [
        {"channel": "Fireship", "niche": "Quick dev tutorials", "subs": "3M+"},
        {"channel": "Theo - t3.gg", "niche": "Build in public", "subs": "200K+"},
        {"channel": "Kent C. Dodds", "niche": "React/Education", "subs": "300K+"},
        {"channel": "Pieter Levels", "niche": "Indie hacking", "subs": "100K+"},
        {"channel": "Indian App Developer", "niche": "Indian dev content", "subs": "500K+"}
    ]

    def get_analysis(self) -> Dict:
        """Analyze competitor positioning"""
        return {
            "differentiation": [
                "Focus on Indian market + AI automation",
                "Show actual client projects (not just tutorials)",
                "Revenue transparency for motivation",
                " Hindi + English content potential"
            ],
            "content_gaps": [
                "Indian SaaS founder stories",
                "AI automation for Indian businesses",
                "n8n/Make.com tutorials in context",
                "Freelancer to agency transition"
            ],
            "collaboration_targets": [
                "Reactify (if active)",
                "Tech creators in Delhi NCR",
                "AI tool review channels"
            ]
        }


class YouTubeAnalyzer:
    """Main YouTube analysis class"""

    CHANNEL_ID = "raghavshahh"  # Handle or actual channel ID

    def __init__(self, api_key: str = None):
        self.api = YouTubeAPI(api_key)
        self.strategy = YouTubeStrategy()
        self.competitors = CompetitorChannels()
        self.data_file = YOUTUBE_FILE

    def get_channel_overview(self) -> Dict:
        """Get current channel status"""
        return {
            "handle": self.CHANNEL_ID,
            "status": "Setup required: Connect YouTube Data API",
            "setup_guide": "https://developers.google.com/youtube/v3/getting-started",
            "content_ready": True,  # Strategy ready to implement
            "priority": "High - YouTube for long-term authority"
        }

    def get_content_strategy(self) -> Dict:
        """Get complete content strategy"""
        return {
            "content_types": self.strategy.CONTENT_TYPES,
            "weekly_schedule": self.strategy.get_content_calendar(),
            "optimal_times": self.strategy.OPTIMAL_SCHEDULE,
            "templates": self.strategy.VIDEO_TEMPLATES,
            "seo": self.strategy.get_seo_optimization()
        }

    def get_video_scripts(self, video_type: str = "ai_tool_demo") -> Dict:
        """Get script templates"""
        return self.strategy.get_video_scripts(video_type)

    def get_growth_plan(self) -> Dict:
        """90-day growth plan"""
        return {
            "month_1": {
                "focus": "Shorts + consistency",
                "target": {"subs": 100, "videos": 12},
                "actions": [
                    "Post 3 Shorts/week",
                    "1 long-form tutorial",
                    "Engage with comments daily",
                    "Optimize thumbnails"
                ]
            },
            "month_2": {
                "focus": "Double down on winners",
                "target": {"subs": 500, "videos": 16},
                "actions": [
                    "Analyze top performing Shorts",
                    "Create similar long-form versions",
                    "Collab with small creators",
                    "Cross-post to Instagram"
                ]
            },
            "month_3": {
                "focus": "Monetization prep",
                "target": {"subs": 1000, "videos": 20},
                "actions": [
                    "Apply for Partner Program",
                    "Add affiliate links",
                    "Mention services in videos",
                    "Build email list from traffic"
                ]
            }
        }

    def generate_full_report(self) -> Dict:
        """Generate complete YouTube intelligence report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "channel": self.get_channel_overview(),
            "content_strategy": self.get_content_strategy(),
            "competitors": self.competitors.get_analysis(),
            "growth_plan": self.get_growth_plan(),
            "immediate_actions": [
                "Create YouTube channel with brand name",
                "Set up channel art + description",
                "Connect to YouTube Data API",
                "Plan first 4 videos (1 month content)",
                "Create thumbnail template in Canva",
                "Set up recording space + mic"
            ],
            "recommended_equipment": {
                "budget": "Phone + natural light + free editing",
                "mid": "Basic mic + ring light + ScreenFlow/Camtasia",
                "pro": "DSLR + professional lighting + Adobe suite"
            }
        }

        # Save report
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(report, f, indent=2)

        return report


# Convenience functions
def generate_youtube_report(api_key: str = None) -> Dict:
    analyzer = YouTubeAnalyzer(api_key)
    return analyzer.generate_full_report()


def get_video_script(video_type: str = "ai_tool_demo") -> Dict:
    strategy = YouTubeStrategy()
    return strategy.get_video_scripts(video_type)


def get_content_calendar() -> Dict:
    strategy = YouTubeStrategy()
    return strategy.get_content_calendar()


if __name__ == "__main__":
    report = generate_youtube_report()
    print(f"YouTube strategy ready with {len(report['growth_plan'])} month plan")
