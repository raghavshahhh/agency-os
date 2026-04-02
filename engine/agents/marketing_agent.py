#!/usr/bin/env python3
"""
RAGSPRO Marketing Agent
Expert agent that manages all marketing operations
Integrates with content, research, and posting agents
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from . import BaseExpertAgent, AgentProfile, AgentRole, Message, ContentPiece

# Import DATA_DIR with fallback
try:
    from config import DATA_DIR
except ImportError:
    from pathlib import Path
    DATA_DIR = Path(__file__).parent.parent.parent / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)


class MarketingAgent(BaseExpertAgent):
    """
    Expert Marketing Agent - The marketing strategist
    - Knows all marketing channels (Instagram, LinkedIn, X, YouTube)
    - Manages content strategy and calendar
    - Coordinates with ContentAgent, ResearchAgent, PostingAgent
    - Tracks campaign performance
    - Identifies opportunities
    """

    def __init__(self, comm_bus):
        profile = AgentProfile(
            id="marketing_agent",
            name="Sarah",
            role=AgentRole.MARKETING,
            avatar="🎯",
            expertise=[
                "Social Media Strategy",
                "Instagram Marketing",
                "LinkedIn B2B Marketing",
                "Twitter/X Growth",
                "YouTube Content Strategy",
                "Content Calendar Planning",
                "Campaign Management",
                "Brand Positioning",
                "Audience Analysis",
                "Viral Content Strategy"
            ],
            personality="Strategic, creative, data-driven, always thinking 3 steps ahead",
            goals=[
                "Grow RAGSPRO brand presence across all platforms",
                "Generate qualified leads through content",
                "Build authority in AI automation space",
                "Maximize content ROI"
            ]
        )
        super().__init__(profile, comm_bus)

        # Marketing knowledge base
        self.knowledge_base = {
            "brand_voice": {
                "tone": "Professional yet approachable",
                "style": "Hinglish mix, Gen-Z friendly, no corporate fluff",
                "values": ["Innovation", "Results", "Authenticity", "Speed"]
            },
            "target_audience": {
                "primary": "Small business owners, 25-45, India",
                "secondary": "Marketing agencies, freelancers",
                "pain_points": ["No time for marketing", "Can't afford agency", "Don't know AI"]
            },
            "platforms": {
                "instagram": {
                    "posting_times": ["9:00 AM", "12:00 PM", "6:00 PM"],
                    "content_types": ["carousel", "reel", "story", "static"],
                    "hashtag_strategy": "Mix of broad (#marketing) and niche (#aiagency)"
                },
                "linkedin": {
                    "posting_times": ["8:00 AM", "12:00 PM", "5:00 PM"],
                    "content_types": ["text_post", "document", "video", "poll"],
                    "focus": "B2B thought leadership"
                },
                "twitter": {
                    "posting_times": ["9:00 AM", "3:00 PM", "7:00 PM"],
                    "content_types": ["thread", "single", "poll"],
                    "focus": "Quick tips, hot takes, engagement"
                },
                "youtube": {
                    "posting_times": ["Saturday 10:00 AM"],
                    "content_types": ["tutorial", "case_study", "tool_review"],
                    "focus": "Long-form educational content"
                }
            },
            "campaigns": [],
            "content_calendar": {},
            "performance_metrics": {}
        }

        self._save_knowledge()

    def _handle_message(self, message: Message):
        """Handle incoming messages from other agents"""
        if message.message_type == "idea":
            # Evaluate ideas from other agents
            self._evaluate_idea(message)
        elif message.message_type == "request":
            # Handle requests (e.g., content strategy, campaign ideas)
            self._handle_request(message)
        elif message.message_type == "content_ready":
            # Content is ready from ContentAgent
            self._handle_content_ready(message)
        elif message.message_type == "research_insights":
            # Insights from ResearchAgent
            self._handle_research_insights(message)

    def _evaluate_idea(self, message: Message):
        """Evaluate and respond to ideas from other agents"""
        idea = message.content
        sender = message.from_agent

        # Marketing perspective evaluation
        evaluation = self._analyze_marketing_potential(idea, message.data)

        if evaluation["score"] >= 7:
            response = f"🔥 Love this idea from {sender}! {evaluation['feedback']} Let's execute!"
            self.broadcast_idea(f"Approved: {idea}", {"evaluation": evaluation})
        else:
            response = f"💡 Thanks {sender}! {evaluation['feedback']} Let's refine it."

        self.send_message(sender, response, "response", {"evaluation": evaluation})
        self.log_activity(f"Evaluated idea from {sender}", {"score": evaluation["score"]})

    def _analyze_marketing_potential(self, idea: str, data: Dict) -> Dict:
        """Analyze marketing potential of an idea"""
        # Simple scoring based on keywords and data
        score = 5  # Base score
        feedback = []

        # Check for viral potential
        viral_keywords = ["viral", "trend", "hack", "secret", "free", "AI"]
        if any(kw in idea.lower() for kw in viral_keywords):
            score += 2
            feedback.append("Has viral keywords")

        # Check for audience fit
        if "business" in idea.lower() or "agency" in idea.lower():
            score += 1
            feedback.append("Aligns with target audience")

        # Check for platform specificity
        platforms = ["instagram", "linkedin", "twitter", "youtube"]
        if any(p in idea.lower() for p in platforms):
            score += 1
            feedback.append("Platform-specific")

        return {
            "score": min(score, 10),
            "feedback": " ".join(feedback) if feedback else "Needs more refinement",
            "recommendation": "Proceed" if score >= 7 else "Revise"
        }

    def _handle_request(self, message: Message):
        """Handle marketing requests"""
        request_type = message.data.get("request_type")

        if request_type == "content_strategy":
            strategy = self._generate_content_strategy(message.data)
            self.send_message(
                message.from_agent,
                "Here's the content strategy",
                "response",
                {"strategy": strategy}
            )
        elif request_type == "campaign_ideas":
            ideas = self._generate_campaign_ideas()
            self.send_message(
                message.from_agent,
                f"Generated {len(ideas)} campaign ideas",
                "response",
                {"ideas": ideas}
            )

    def _generate_content_strategy(self, data: Dict) -> Dict:
        """Generate platform-specific content strategy"""
        platform = data.get("platform", "all")

        strategies = {
            "instagram": {
                "frequency": "1 post + 2 stories daily",
                "content_mix": ["40% educational", "30% entertaining", "20% promotional", "10% personal"],
                "focus": "Visual storytelling, reels for reach"
            },
            "linkedin": {
                "frequency": "1 post daily, 1 article weekly",
                "content_mix": ["50% thought leadership", "30% case studies", "20% company updates"],
                "focus": "B2B value, professional insights"
            },
            "twitter": {
                "frequency": "3-5 tweets daily, 1 thread weekly",
                "content_mix": ["40% tips", "30% opinions", "20% engagement", "10% promo"],
                "focus": "Quick value, hot takes, conversations"
            },
            "youtube": {
                "frequency": "2 videos weekly",
                "content_mix": ["60% tutorials", "30% case studies", "10% vlogs"],
                "focus": "Deep educational content"
            }
        }

        if platform == "all":
            return strategies
        return strategies.get(platform, strategies)

    def _generate_campaign_ideas(self) -> List[Dict]:
        """Generate campaign ideas"""
        templates = [
            {
                "name": "30 Days of AI Automation",
                "concept": "Daily tips on using AI for business",
                "platforms": ["instagram", "twitter", "linkedin"],
                "duration": "30 days",
                "expected_engagement": "High"
            },
            {
                "name": "Agency Growth Secrets",
                "concept": "Share real case studies and results",
                "platforms": ["linkedin", "youtube"],
                "duration": "Ongoing",
                "expected_engagement": "Medium-High"
            },
            {
                "name": "AI Tools Showdown",
                "concept": "Compare AI tools, RAGSPRO always wins",
                "platforms": ["instagram", "youtube", "twitter"],
                "duration": "Weekly series",
                "expected_engagement": "High"
            },
            {
                "name": "Behind the Scenes",
                "concept": "Show how RAGSPRO builds automation",
                "platforms": ["instagram", "twitter"],
                "duration": "Weekly",
                "expected_engagement": "Medium"
            }
        ]
        return templates

    def _handle_content_ready(self, message: Message):
        """Handle content ready from ContentAgent"""
        content_data = message.data.get("content", {})
        platform = content_data.get("platform")

        # Approve and queue for posting
        self.send_message(
            "posting_agent",
            f"Content ready for {platform}",
            "request",
            {
                "request_type": "schedule_post",
                "content": content_data,
                "platform": platform
            }
        )

        self.log_activity(f"Approved content for {platform}", {"content_id": content_data.get("id")})

    def _handle_research_insights(self, message: Message):
        """Handle insights from ResearchAgent"""
        insights = message.data.get("insights", {})

        # Update strategy based on insights
        if "trending_topics" in insights:
            self.broadcast_idea(
                "New trending topics identified! Adjusting content strategy...",
                {"trends": insights["trending_topics"]}
            )

    def request_content_creation(self, platform: str, content_type: str, topic: str = None):
        """Request content from ContentAgent"""
        self.send_message(
            "content_agent",
            f"Need {content_type} content for {platform}",
            "request",
            {
                "request_type": "create_content",
                "platform": platform,
                "content_type": content_type,
                "topic": topic or self._get_trending_topic(),
                "brand_voice": self.knowledge_base.get("brand_voice")
            }
        )
        self.log_activity(f"Requested {platform} content", {"type": content_type})

    def request_market_research(self, focus: str = "trends"):
        """Request research from ResearchAgent"""
        self.send_message(
            "research_agent",
            f"Need {focus} research for marketing",
            "request",
            {
                "request_type": focus,
                "platforms": ["instagram", "linkedin", "twitter"],
                "keywords": ["AI automation", "marketing agency", "lead generation"]
            }
        )
        self.log_activity(f"Requested market research", {"focus": focus})

    def _get_trending_topic(self) -> str:
        """Get current trending topic from knowledge base"""
        trends = self.knowledge_base.get("current_trends", [])
        if trends:
            return random.choice(trends).get("topic", "AI automation")
        return "AI automation for agencies"

    def get_dashboard_data(self) -> Dict:
        """Get data for marketing dashboard"""
        return {
            "profile": {
                "name": self.profile.name,
                "avatar": self.profile.avatar,
                "role": self.profile.role.value,
                "expertise": self.profile.expertise[:5],
                "status": self.profile.status
            },
            "knowledge_summary": {
                "platforms_managed": list(self.knowledge_base.get("platforms", {}).keys()),
                "active_campaigns": len(self.knowledge_base.get("campaigns", [])),
                "target_audience": self.knowledge_base.get("target_audience", {})
            },
            "ideas_generated": self.profile.ideas_generated,
            "tasks_completed": self.profile.tasks_completed,
            "recent_ideas": self.ideas[-5:] if self.ideas else []
        }

    def run_daily_planning(self):
        """Daily planning routine"""
        self.log_activity("Starting daily marketing planning")

        # Request content for today if not exists
        today = datetime.now().strftime("%Y-%m-%d")
        content_dir = DATA_DIR / "content" / today

        if not content_dir.exists():
            self.request_content_creation("instagram", "carousel")
            self.request_content_creation("linkedin", "post")
            self.request_content_creation("twitter", "thread")

        # Request market research periodically
        if datetime.now().weekday() == 0:  # Monday
            self.request_market_research("trends")

        self.broadcast_idea(
            f"Daily marketing plan complete for {today}",
            {"status": "planned", "platforms": ["instagram", "linkedin", "twitter"]}
        )


if __name__ == "__main__":
    from . import AgentCommunicationBus

    # Test the marketing agent
    bus = AgentCommunicationBus()
    agent = MarketingAgent(bus)

    print("Marketing Agent Profile:")
    print(json.dumps(agent.get_status(), indent=2))
