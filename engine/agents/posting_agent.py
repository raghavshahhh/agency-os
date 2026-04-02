#!/usr/bin/env python3
"""
RAGSPRO Posting Automation Agent
Expert agent for auto-posting to social platforms
Manages content queue and scheduling
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from . import BaseExpertAgent, AgentProfile, AgentRole, Message

# Import DATA_DIR with fallback
try:
    from config import DATA_DIR
except ImportError:
    from pathlib import Path
    DATA_DIR = Path(__file__).parent.parent.parent / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)


class PostingAutomationAgent(BaseExpertAgent):
    """
    Expert Posting Automation Agent - The distribution expert
    - Posts to Instagram, LinkedIn, Twitter/X, YouTube
    - Manages content queue
    - Handles scheduling
    - Tracks post performance
    """

    def __init__(self, comm_bus):
        profile = AgentProfile(
            id="posting_agent",
            name="Zara",
            role=AgentRole.POSTING,
            avatar="📤",
            expertise=[
                "Social Media Posting",
                "Content Scheduling",
                "Platform Optimization",
                "Queue Management",
                "Performance Tracking",
                "Instagram Automation",
                "LinkedIn Automation",
                "Twitter Automation",
                "YouTube Upload",
                "Cross-Platform Distribution"
            ],
            personality="Punctual, organized, always on time, knows the best posting times",
            goals=[
                "Never miss a posting schedule",
                "Maximize reach on every platform",
                "Maintain consistent presence",
                "Track and optimize performance"
            ]
        )
        super().__init__(profile, comm_bus)

        self.knowledge_base = {
            "posting_schedule": {
                "instagram": ["09:00", "12:00", "18:00"],
                "linkedin": ["08:00", "12:00", "17:00"],
                "twitter": ["09:00", "15:00", "19:00"],
                "youtube": ["Saturday 10:00"]
            },
            "best_times": {
                "instagram": {"weekday": ["12:00", "18:00"], "weekend": ["10:00", "14:00"]},
                "linkedin": {"weekday": ["08:00", "12:00", "17:00"], "weekend": []},
                "twitter": {"weekday": ["09:00", "15:00", "19:00"], "weekend": ["10:00", "20:00"]}
            },
            "content_queue": [],
            "posted_content": [],
            "platforms": {
                "instagram": {"enabled": True, "auto_post": False, "last_post": None},
                "linkedin": {"enabled": True, "auto_post": True, "last_post": None},
                "twitter": {"enabled": True, "auto_post": True, "last_post": None},
                "youtube": {"enabled": False, "auto_post": False, "last_post": None}
            }
        }

        self._save_knowledge()

    def _handle_message(self, message: Message):
        """Handle incoming messages"""
        if message.message_type == "request":
            data = message.data
            if data.get("request_type") == "schedule_post":
                self._schedule_post(data.get("content"), data.get("platform"))
            elif data.get("request_type") == "post_now":
                self._post_now(data.get("content"), data.get("platform"))
            elif data.get("request_type") == "get_queue":
                queue = self._get_queue()
                self.send_message(
                    message.from_agent,
                    f"Queue has {len(queue)} items",
                    "response",
                    {"queue": queue}
                )

    def _schedule_post(self, content: Dict, platform: str):
        """Schedule a post"""
        post = {
            "id": content.get("id", f"post_{datetime.now().timestamp()}"),
            "content": content,
            "platform": platform,
            "status": "scheduled",
            "scheduled_for": self._get_next_slot(platform),
            "created_at": datetime.now().isoformat()
        }

        self.knowledge_base["content_queue"].append(post)
        self._save_knowledge()

        self.log_activity(f"Scheduled {platform} post", {"post_id": post["id"]})

        # Confirm to marketing agent
        self.send_message(
            "marketing_agent",
            f"✅ Post scheduled for {platform} at {post['scheduled_for']}",
            "response",
            {"scheduled_post": post}
        )

    def _post_now(self, content: Dict, platform: str) -> Dict:
        """Post immediately to platform"""
        result = {"success": False, "platform": platform, "posted_at": datetime.now().isoformat()}

        try:
            # Simulate posting (in production, integrate with APIs)
            if platform == "instagram":
                result = self._post_to_instagram(content)
            elif platform == "linkedin":
                result = self._post_to_linkedin(content)
            elif platform == "twitter":
                result = self._post_to_twitter(content)
            elif platform == "youtube":
                result = self._post_to_youtube(content)

            # Record the post
            self.knowledge_base["posted_content"].append({
                **result,
                "content": content,
                "posted_at": datetime.now().isoformat()
            })

            # Update platform stats
            self.knowledge_base["platforms"][platform]["last_post"] = datetime.now().isoformat()
            self._save_knowledge()

            self.log_activity(f"Posted to {platform}", {"success": result.get("success")})

            # Notify business agent
            self.send_message(
                "business_agent",
                f"Content posted to {platform}",
                "response",
                {"platform": platform, "content_id": content.get("id")}
            )

        except Exception as e:
            self.send_message(
                "business_agent",
                f"Failed to post to {platform}: {str(e)}",
                "alert",
                {"error": str(e), "platform": platform}
            )
            result["error"] = str(e)

        return result

    def _post_to_instagram(self, content: Dict) -> Dict:
        """Post to Instagram"""
        # Would integrate with Instagram API
        return {
            "success": True,
            "platform": "instagram",
            "post_url": f"https://instagram.com/p/demo_{random.randint(1000, 9999)}",
            "type": content.get("content_type", "post")
        }

    def _post_to_linkedin(self, content: Dict) -> Dict:
        """Post to LinkedIn"""
        # Would integrate with LinkedIn API
        return {
            "success": True,
            "platform": "linkedin",
            "post_url": f"https://linkedin.com/posts/demo_{random.randint(1000, 9999)}",
            "type": content.get("content_type", "post")
        }

    def _post_to_twitter(self, content: Dict) -> Dict:
        """Post to Twitter/X"""
        # Would integrate with Twitter API
        return {
            "success": True,
            "platform": "twitter",
            "post_url": f"https://twitter.com/demo/status/{random.randint(1000000, 9999999)}",
            "type": content.get("content_type", "tweet")
        }

    def _post_to_youtube(self, content: Dict) -> Dict:
        """Post to YouTube"""
        # Would integrate with YouTube API
        return {
            "success": True,
            "platform": "youtube",
            "post_url": f"https://youtube.com/watch?v=demo_{random.randint(1000, 9999)}",
            "type": content.get("content_type", "video")
        }

    def _get_next_slot(self, platform: str) -> str:
        """Get next available posting slot"""
        schedule = self.knowledge_base["posting_schedule"].get(platform, ["12:00"])
        now = datetime.now()

        for time_str in schedule:
            hour, minute = map(int, time_str.split(":"))
            slot = now.replace(hour=hour, minute=minute, second=0)
            if slot > now:
                return slot.isoformat()

        # Return first slot tomorrow
        tomorrow = now + timedelta(days=1)
        hour, minute = map(int, schedule[0].split(":"))
        slot = tomorrow.replace(hour=hour, minute=minute, second=0)
        return slot.isoformat()

    def _get_queue(self) -> List[Dict]:
        """Get scheduled content queue"""
        return [p for p in self.knowledge_base["content_queue"] if p["status"] == "scheduled"]

    def run_scheduled_posting(self):
        """Check and post scheduled content"""
        now = datetime.now()
        queue = self._get_queue()

        for post in queue:
            scheduled_time = datetime.fromisoformat(post["scheduled_for"])
            if scheduled_time <= now:
                # Time to post
                self._post_now(post["content"], post["platform"])
                post["status"] = "posted"

        self._save_knowledge()

    def get_dashboard_data(self) -> Dict:
        """Get data for dashboard"""
        queue = self._get_queue()
        posted = self.knowledge_base["posted_content"]

        # Calculate posts by platform
        posts_by_platform = {}
        for post in posted:
            platform = post.get("platform", "unknown")
            posts_by_platform[platform] = posts_by_platform.get(platform, 0) + 1

        return {
            "profile": {
                "name": self.profile.name,
                "avatar": self.profile.avatar,
                "role": self.profile.role.value,
                "expertise": self.profile.expertise[:5],
                "status": self.profile.status
            },
            "posting_stats": {
                "scheduled": len(queue),
                "posted_total": len(posted),
                "by_platform": posts_by_platform,
                "last_24h": len([p for p in posted if (now - datetime.fromisoformat(p["posted_at"])).days < 1])
            },
            "platform_status": self.knowledge_base["platforms"],
            "next_scheduled": queue[0]["scheduled_for"] if queue else None,
            "ideas_generated": self.profile.ideas_generated,
            "tasks_completed": self.profile.tasks_completed
        }

    def get_content_queue(self) -> List[Dict]:
        """Get content queue for UI display"""
        return self._get_queue()


if __name__ == "__main__":
    from . import AgentCommunicationBus

    bus = AgentCommunicationBus()
    agent = PostingAutomationAgent(bus)

    print("Posting Automation Agent Profile:")
    print(json.dumps(agent.get_dashboard_data(), indent=2))
