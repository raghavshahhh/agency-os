#!/usr/bin/env python3
"""
RAGSPRO Content Factory
Auto-generate content for Instagram, YouTube, LinkedIn
Integrates with Remotion for video creation
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR

CONTENT_QUEUE_FILE = DATA_DIR / "content_queue.json"
CONTENT_ASSETS_FILE = DATA_DIR / "content_assets.json"
POSTED_CONTENT_FILE = DATA_DIR / "posted_content.json"


@dataclass
class ContentPiece:
    """Standard content format"""
    id: str
    platform: str  # instagram, youtube, linkedin, twitter
    content_type: str  # reel, carousel, story, short, post
    title: str
    caption: str
    hashtags: List[str]
    scheduled_for: str
    status: str = "draft"  # draft, ready, scheduled, posted, failed
    assets: List[str] = None  # Paths to images/videos
    remotion_config: Dict = None  # For video content
    engagement_prediction: int = 0
    created_at: str = ""
    posted_at: str = ""
    post_url: str = ""
    metrics: Dict = None

    def __post_init__(self):
        if self.assets is None:
            self.assets = []
        if self.hashtags is None:
            self.hashtags = []
        if self.remotion_config is None:
            self.remotion_config = {}
        if self.metrics is None:
            self.metrics = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        return asdict(self)


class HashtagLibrary:
    """Curated hashtags by category"""

    CATEGORIES = {
        "ai_automation": [
            "#AI", "#Automation", "#Chatbot", "#AIAgent",
            "#NoCode", "#LowCode", "#n8n", "#Make",
            "#BusinessAutomation", "#AIforBusiness"
        ],
        "development": [
            "#WebDevelopment", "#AppDevelopment", "#React",
            "#NextJS", "#Python", "#FullStack", "#Developer",
            "#Coding", "#Programming", "#Tech"
        ],
        "entrepreneurship": [
            "#Entrepreneur", "#Startup", "#SaaS", "#IndieHacker",
            "#BuildInPublic", "#Solopreneur", "#BusinessGrowth",
            "#DigitalMarketing", "#Freelancer", "#AgencyLife"
        ],
        "indian_market": [
            "#IndianStartup", "#DesiEntrepreneur", "#IndiaTech",
            "#MadeInIndia", "#StartupIndia", "#DelhiStartup",
            "#MumbaiStartup", "#BangaloreStartup"
        ],
        "content": [
            "#ContentCreator", "#TechContent", "#Educational",
            "#Tutorial", "#LearnToCode", "#TechTips",
            "#DayInTheLife", "#BehindTheScenes"
        ]
    }

    @classmethod
    def get_for_post(cls, primary: str, count: int = 10) -> List[str]:
        """Get hashtags for a specific post type"""
        tags = cls.CATEGORIES.get(primary, [])
        return tags[:count]

    @classmethod
    def get_mixed(cls, categories: List[str], count: int = 10) -> List[str]:
        """Get mixed hashtags from multiple categories"""
        tags = []
        for cat in categories:
            tags.extend(cls.CATEGORIES.get(cat, []))
        return list(set(tags))[:count]


class CaptionGenerator:
    """Generate captions for different content types"""

    TEMPLATES = {
        "ai_tip": {
            "hook": "This {tool} just saved me {hours} hours this week 🔥",
            "body": "I was spending hours on {task} every week. Then I discovered {solution}.",
            "benefits": "Now I can focus on {higher_value} instead of manual work.",
            "cta": "Save this post and follow for more automation tips! 👇",
            "hashtag_cats": ["ai_automation", "entrepreneurship"]
        },
        "build_in_public": {
            "hook": "Week {week} of building {project} 📊",
            "body": "Shipped: {shipped}\nChallenges: {challenges}",
            "metrics": "Current metrics: {metrics}",
            "cta": "Follow along as we build in public! What should we build next?",
            "hashtag_cats": ["entrepreneurship", "development", "content"]
        },
        "client_win": {
            "hook": "We just helped {client} achieve {result} 🚀",
            "body": "Before: {before}\nAfter: {after}",
            "method": "How we did it: {method}",
            "cta": "DM 'RESULTS' to see how we can do the same for you.",
            "hashtag_cats": ["entrepreneurship", "ai_automation"]
        },
        "educational_carousel": {
            "hook": "The ultimate guide to {topic} 📚",
            "body": "Swipe through for the complete breakdown 👉",
            "slide_count": "{count} slides that will change how you think about {topic}",
            "cta": "Save this for later and share with someone who needs it!",
            "hashtag_cats": ["content", "development", "ai_automation"]
        },
        "motivation": {
            "hook": "Your Monday reminder: {reminder} 💪",
            "body": "{inspirational_quote}",
            "cta": "Drop a 🔥 if you're building something great this week!",
            "hashtag_cats": ["entrepreneurship", "content"]
        }
    }

    @classmethod
    def generate(cls, template_name: str, variables: Dict) -> Dict:
        """Generate caption from template"""
        template = cls.TEMPLATES.get(template_name, {})

        caption_parts = []
        for key in ["hook", "body", "benefits", "metrics", "method", "slide_count", "cta"]:
            if key in template and key in variables:
                caption_parts.append(template[key].format(**variables))

        caption = "\n\n".join(caption_parts)

        return {
            "caption": caption,
            "hashtags": HashtagLibrary.get_mixed(template.get("hashtag_cats", ["content"]), 10),
            "template": template_name
        }


class RemotionConfig:
    """Generate Remotion configs for video content"""

    VIDEO_TEMPLATES = {
        "ai_tool_showcase": {
            "duration": 30,  # seconds
            "dimensions": [1080, 1920],  # 9:16 for Reels
            "components": [
                {"type": "title", "text": "{hook}", "duration": 3, "style": "bold"},
                {"type": "screen_recording", "source": "{demo_video}", "duration": 15},
                {"type": "text_overlay", "text": "{benefit}", "duration": 5},
                {"type": "cta", "text": "Follow for more", "duration": 5}
            ],
            "music": "upbeat_tech",
            "transitions": "quick_cuts"
        },
        "build_in_public": {
            "duration": 60,
            "dimensions": [1080, 1920],
            "components": [
                {"type": "intro", "text": "Week {week} Update", "duration": 5},
                {"type": "code_timelapse", "source": "{screen_captures}", "duration": 30},
                {"type": "text_list", "items": "{features_built}", "duration": 15},
                {"type": "metrics", "data": "{stats}", "duration": 8},
                {"type": "cta", "text": "Follow the journey", "duration": 5}
            ],
            "music": "lofi_coding",
            "transitions": "smooth"
        },
        "client_testimonial": {
            "duration": 30,
            "dimensions": [1080, 1920],
            "components": [
                {"type": "quote", "text": "{testimonial}", "duration": 8},
                {"type": "before_after", "data": "{metrics}", "duration": 12},
                {"type": "client_info", "name": "{client_name}", "company": "{company}", "duration": 5},
                {"type": "cta", "text": "Get similar results", "duration": 5}
            ],
            "music": "professional",
            "transitions": "elegant"
        },
        "tutorial_short": {
            "duration": 45,
            "dimensions": [1080, 1920],
            "components": [
                {"type": "hook", "text": "Learn {topic} in 1 min", "duration": 3},
                {"type": "step_by_step", "steps": "{tutorial_steps}", "duration": 35},
                {"type": "recap", "text": "Save this!", "duration": 5}
            ],
            "music": "educational",
            "transitions": "numbered"
        }
    }

    @classmethod
    def generate_config(cls, template_name: str, variables: Dict) -> Dict:
        """Generate Remotion configuration"""
        template = cls.VIDEO_TEMPLATES.get(template_name, {})

        # Replace variables in components
        components = []
        for comp in template.get("components", []):
            comp_copy = comp.copy()
            for key, value in comp_copy.items():
                if isinstance(value, str) and "{" in value:
                    try:
                        comp_copy[key] = value.format(**variables)
                    except:
                        pass
            components.append(comp_copy)

        return {
            "template": template_name,
            "duration": template.get("duration", 30),
            "dimensions": template.get("dimensions", [1080, 1920]),
            "components": components,
            "music": template.get("music", "generic"),
            "transitions": template.get("transitions", "basic"),
            "output_format": "mp4",
            "fps": 30
        }


class ContentScheduler:
    """Schedule content for optimal posting times"""

    OPTIMAL_TIMES = {
        "instagram_reel": ["11:00", "19:00"],  # IST
        "instagram_carousel": ["09:00", "17:00"],
        "instagram_story": ["08:00", "13:00", "20:00"],
        "youtube_short": ["17:00", "20:00"],
        "youtube_long": ["11:00", "16:00"],
        "linkedin_post": ["08:00", "12:00", "17:00"],
        "twitter": ["09:00", "15:00", "19:00"]
    }

    def __init__(self):
        self.queue_file = CONTENT_QUEUE_FILE
        self.posted_file = POSTED_CONTENT_FILE

    def get_next_slot(self, platform: str, content_type: str) -> str:
        """Get next available posting slot"""
        key = f"{platform}_{content_type}"
        times = self.OPTIMAL_TIMES.get(key, ["09:00"])

        # Find next available time
        now = datetime.now()
        for time_str in times:
            hour, minute = map(int, time_str.split(":"))
            slot = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if slot > now:
                return slot.isoformat()

        # Return first slot tomorrow
        hour, minute = map(int, times[0].split(":"))
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=hour, minute=minute).isoformat()

    def schedule_content(self, content: ContentPiece) -> ContentPiece:
        """Schedule content for optimal time"""
        content.scheduled_for = self.get_next_slot(content.platform, content.content_type)
        content.status = "scheduled"
        return content

    def save_to_queue(self, content_list: List[ContentPiece]):
        """Save content to queue"""
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing
        existing = []
        if self.queue_file.exists():
            with open(self.queue_file, 'r') as f:
                existing = json.load(f)

        # Add new
        for content in content_list:
            existing.append(content.to_dict())

        with open(self.queue_file, 'w') as f:
            json.dump(existing, f, indent=2)

    def get_scheduled_content(self) -> List[Dict]:
        """Get all scheduled content"""
        if self.queue_file.exists():
            with open(self.queue_file, 'r') as f:
                return json.load(f)
        return []


class ContentFactory:
    """Main content factory class"""

    def __init__(self):
        self.scheduler = ContentScheduler()
        self.caption_gen = CaptionGenerator()
        self.remotion = RemotionConfig()

    def create_ai_tip_post(self, tool: str, hours_saved: int, task: str) -> ContentPiece:
        """Create AI tip carousel/Reel"""
        variables = {
            "tool": tool,
            "hours": hours_saved,
            "task": task,
            "solution": f"{tool} automation",
            "higher_value": "strategy and growth"
        }

        caption_data = self.caption_gen.generate("ai_tip", variables)

        return ContentPiece(
            id=f"aitip_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            platform="instagram",
            content_type="carousel",
            title=f"AI Tip: {tool}",
            caption=caption_data["caption"],
            hashtags=caption_data["hashtags"],
            scheduled_for="",
            engagement_prediction=75
        )

    def create_build_in_public_post(self, week: int, project: str, shipped: str, metrics: str) -> ContentPiece:
        """Create build in public update"""
        variables = {
            "week": week,
            "project": project,
            "shipped": shipped,
            "challenges": "Scaling the backend",
            "metrics": metrics
        }

        caption_data = self.caption_gen.generate("build_in_public", variables)

        # Generate Remotion config for Reel
        remotion_vars = {
            "week": week,
            "features_built": shipped,
            "stats": metrics
        }
        remotion_config = self.remotion.generate_config("build_in_public", remotion_vars)

        return ContentPiece(
            id=f"bip_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            platform="instagram",
            content_type="reel",
            title=f"Week {week} - {project}",
            caption=caption_data["caption"],
            hashtags=caption_data["hashtags"],
            scheduled_for="",
            remotion_config=remotion_config,
            engagement_prediction=85
        )

    def create_client_win_post(self, client: str, result: str) -> ContentPiece:
        """Create client testimonial post"""
        variables = {
            "client": client,
            "result": result,
            "before": "manual lead tracking",
            "after": "fully automated pipeline",
            "method": "AI-powered CRM + Auto-outreach"
        }

        caption_data = self.caption_gen.generate("client_win", variables)

        return ContentPiece(
            id=f"win_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            platform="instagram",
            content_type="reel",
            title=f"Client Win: {client}",
            caption=caption_data["caption"],
            hashtags=caption_data["hashtags"],
            scheduled_for="",
            engagement_prediction=90
        )

    def create_educational_carousel(self, topic: str, slide_count: int) -> ContentPiece:
        """Create educational carousel"""
        variables = {
            "topic": topic,
            "count": slide_count
        }

        caption_data = self.caption_gen.generate("educational_carousel", variables)

        return ContentPiece(
            id=f"edu_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            platform="instagram",
            content_type="carousel",
            title=f"Guide: {topic}",
            caption=caption_data["caption"],
            hashtags=caption_data["hashtags"],
            scheduled_for="",
            engagement_prediction=80
        )

    def generate_weekly_content(self) -> List[ContentPiece]:
        """Generate a week's worth of content"""
        content_pieces = []

        # Monday: Motivation
        content_pieces.append(self._create_motivation_post("Start your week with automation"))

        # Tuesday: AI Tip
        content_pieces.append(self.create_ai_tip_post("ChatGPT", 10, "content creation"))

        # Wednesday: Build in Public
        content_pieces.append(self.create_build_in_public_post(
            week=1, project="Agency OS", shipped="Lead scraper v2", metrics="13k+ leads"
        ))

        # Thursday: Client Win (if available)
        content_pieces.append(self.create_client_win_post("LegalTech Startup", "10x lead conversion"))

        # Friday: Educational
        content_pieces.append(self.create_educational_carousel("AI Automation", 5))

        # Saturday: Behind the scenes
        content_pieces.append(self._create_bts_post())

        # Sunday: Week recap
        content_pieces.append(self._create_recap_post())

        # Schedule all content
        scheduled = [self.scheduler.schedule_content(c) for c in content_pieces]

        # Save to queue
        self.scheduler.save_to_queue(scheduled)

        return scheduled

    def _create_motivation_post(self, reminder: str) -> ContentPiece:
        variables = {
            "reminder": reminder,
            "inspirational_quote": "The best time to automate was yesterday. The second best time is today."
        }
        caption_data = self.caption_gen.generate("motivation", variables)

        return ContentPiece(
            id=f"mot_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            platform="instagram",
            content_type="story",
            title="Monday Motivation",
            caption=caption_data["caption"],
            hashtags=caption_data["hashtags"],
            scheduled_for="",
            engagement_prediction=60
        )

    def _create_bts_post(self) -> ContentPiece:
        return ContentPiece(
            id=f"bts_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            platform="instagram",
            content_type="story",
            title="Behind the Scenes",
            caption="Saturday vibes: Coffee + Code ☕💻\n\nWhat are you building this weekend?",
            hashtags=HashtagLibrary.get_for_post("content", 8),
            scheduled_for="",
            engagement_prediction=55
        )

    def _create_recap_post(self) -> ContentPiece:
        return ContentPiece(
            id=f"recap_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            platform="instagram",
            content_type="reel",
            title="Week Recap",
            caption="Week in review 📊\n\nWhat we shipped:\n✅ New features\n✅ Client wins\n✅ Lessons learned\n\nNext week: Even bigger!",
            hashtags=HashtagLibrary.get_for_post("entrepreneurship", 10),
            scheduled_for="",
            engagement_prediction=70
        )


# Convenience functions
def generate_weekly_content() -> List[Dict]:
    factory = ContentFactory()
    content = factory.generate_weekly_content()
    return [c.to_dict() for c in content]


def get_content_queue() -> List[Dict]:
    scheduler = ContentScheduler()
    return scheduler.get_scheduled_content()


def get_hashtags(category: str, count: int = 10) -> List[str]:
    return HashtagLibrary.get_for_post(category, count)


if __name__ == "__main__":
    content = generate_weekly_content()
    print(f"Generated {len(content)} content pieces for this week")
