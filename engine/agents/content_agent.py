#!/usr/bin/env python3
"""
RAGSPRO Content Creation Agent
Expert agent for generating social media content
Uses NVIDIA NIM for AI-powered content generation
"""

import json
import random
from datetime import datetime
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


class ContentCreationAgent(BaseExpertAgent):
    """
    Expert Content Creation Agent - The creative genius
    - Generates content for Instagram, LinkedIn, Twitter/X, YouTube
    - Creates carousels, reels, videos, threads
    - Uses brand voice and strategy from MarketingAgent
    - Optimizes for each platform
    """

    def __init__(self, comm_bus):
        profile = AgentProfile(
            id="content_agent",
            name="Alex",
            role=AgentRole.CONTENT,
            avatar="✍️",
            expertise=[
                "Copywriting",
                "Instagram Content",
                "LinkedIn Articles",
                "Twitter Threads",
                "YouTube Scripts",
                "Hashtag Research",
                "Visual Content Strategy",
                "Viral Hook Writing",
                "Storytelling",
                "SEO Copywriting"
            ],
            personality="Creative, witty, always has the perfect hook, understands viral psychology",
            goals=[
                "Create scroll-stopping content",
                "Maximize engagement on every post",
                "Build consistent brand voice",
                "Generate content that converts"
            ]
        )
        super().__init__(profile, comm_bus)

        # Content templates and patterns
        self.knowledge_base = {
            "hooks": {
                "instagram": [
                    "POV: You finally found the AI tool that...",
                    "Stop doing this if you want to grow...",
                    "This changed everything for my agency...",
                    "3 AI tools that will 10x your output:",
                    "I spent ₹1L on marketing so you don't have to..."
                ],
                "linkedin": [
                    "I helped a client 10x their leads in 30 days. Here's how:",
                    "The biggest mistake I see agency owners make:",
                    "3 lessons from running an AI agency for 6 months:",
                    "Most people get AI automation wrong. Here's the fix:",
                    "Unpopular opinion: {controversial_take}"
                ],
                "twitter": [
                    "Hot take: {controversial_take}",
                    "3 AI tools that actually work (no fluff):",
                    "Agency owners, stop doing this 👇",
                    "The AI automation playbook (Thread):",
                    "I built an AI agency from ₹0 to ₹50K. Here's what I learned:"
                ]
            },
            "content_patterns": {
                "carousel": {
                    "structure": ["Hook slide", "Problem", "Solution", "Steps", "CTA"],
                    "slide_count": 5
                },
                "reel": {
                    "structure": ["Hook (0-3s)", "Value delivery", "CTA"],
                    "duration": "30-60s"
                },
                "thread": {
                    "structure": ["Strong opener", "Main points", "Takeaways", "CTA"],
                    "tweet_count": "5-10"
                }
            },
            "brand_voice": {
                "words_to_use": ["crushing it", "10x", "scale", "automate", "growth"],
                "words_to_avoid": ["synergy", "leverage", "robust", "scalable"],
                "tone": "Direct, energetic, no fluff"
            },
            "hashtag_sets": {
                "instagram": ["#aiagency", "#marketingautomation", "#leadgeneration", "#aicommunity", "#growthhacking"],
                "linkedin": ["#artificialintelligence", "#marketing", "#agencylife", "#automation", "#businessgrowth"],
                "twitter": ["#AI", "#Marketing", "#Automation", "#AgencyLife", "#BuildInPublic"]
            }
        }

        self.content_queue: List[ContentPiece] = []
        self._save_knowledge()

    def _handle_message(self, message: Message):
        """Handle incoming messages"""
        if message.message_type == "request":
            data = message.data
            if data.get("request_type") == "create_content":
                self._create_content(message)
            elif data.get("request_type") == "content_ideas":
                ideas = self._generate_content_ideas(data.get("platform"), data.get("count", 5))
                self.send_message(
                    message.from_agent,
                    f"Generated {len(ideas)} content ideas",
                    "response",
                    {"ideas": ideas}
                )

    def _create_content(self, message: Message):
        """Create content based on request"""
        data = message.data
        platform = data.get("platform")
        content_type = data.get("content_type")
        topic = data.get("topic", self._get_random_topic())
        brand_voice = data.get("brand_voice", self.knowledge_base.get("brand_voice"))

        try:
            # Generate content based on platform and type
            content_piece = self._generate_content_piece(platform, content_type, topic)

            # Save content
            self._save_content(content_piece)

            # Notify marketing agent
            self.send_message(
                "marketing_agent",
                f"Content ready for {platform}",
                "content_ready",
                {"content": content_piece}
            )

            # Log activity
            self.log_activity(f"Created {content_type} for {platform}", {"topic": topic})
            self.profile.tasks_completed += 1

        except Exception as e:
            self.send_message(
                "business_agent",
                f"Content creation failed: {str(e)}",
                "alert",
                {"error": str(e), "platform": platform}
            )

    def _generate_content_piece(self, platform: str, content_type: str, topic: str) -> Dict:
        """Generate a complete content piece"""
        content_id = f"{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        generators = {
            ("instagram", "carousel"): self._generate_instagram_carousel,
            ("instagram", "reel"): self._generate_reel_script,
            ("instagram", "post"): self._generate_instagram_post,
            ("linkedin", "post"): self._generate_linkedin_post,
            ("linkedin", "article"): self._generate_linkedin_article,
            ("twitter", "thread"): self._generate_twitter_thread,
            ("twitter", "post"): self._generate_tweet,
            ("youtube", "video"): self._generate_youtube_script,
        }

        generator = generators.get((platform, content_type), self._generate_generic_content)
        content = generator(topic)

        return {
            "id": content_id,
            "platform": platform,
            "content_type": content_type,
            "topic": topic,
            **content,
            "created_at": datetime.now().isoformat(),
            "status": "draft"
        }

    def _generate_instagram_carousel(self, topic: str) -> Dict:
        """Generate Instagram carousel content"""
        hooks = self.knowledge_base["hooks"]["instagram"]
        hashtags = self.knowledge_base["hashtag_sets"]["instagram"]

        title = random.choice(hooks).format(topic=topic)

        slides = [
            {"type": "title", "text": title, "design": "bold text on gradient"},
            {"type": "problem", "text": f"Here's why most agencies struggle with {topic}...", "bullet_points": ["No systems", "Manual work", "Inconsistent results"]},
            {"type": "solution", "text": "The AI-powered solution:", "bullet_points": ["Automated workflows", "24/7 lead generation", "Scalable systems"]},
            {"type": "steps", "text": "3 steps to implement:", "steps": ["Step 1: Audit current process", "Step 2: Identify automation opportunities", "Step 3: Deploy AI agents"]},
            {"type": "cta", "text": "Follow @ragspro for more AI automation tips! 💪", "design": "branded outro"}
        ]

        caption = f"{title}\n\nSwipe for the full breakdown 👉\n\nWhich slide hit home? Comment below! 👇\n\n{' '.join(hashtags[:8])}"

        return {
            "title": title,
            "caption": caption,
            "slides": slides,
            "hashtags": hashtags,
            "image_prompt": f"Instagram carousel slide: {title}, modern design, gradient background, bold typography"
        }

    def _generate_reel_script(self, topic: str) -> Dict:
        """Generate Instagram Reel script"""
        hooks = self.knowledge_base["hooks"]["instagram"]

        script = {
            "hook": random.choice(hooks).format(topic=topic),
            "scene_1": {"duration": "0-3s", "visual": "Face to camera, high energy", "text": "POV: You discovered AI automation"},
            "scene_2": {"duration": "3-15s", "visual": "Screen recording or B-roll", "text": f"Showing {topic} automation in action"},
            "scene_3": {"duration": "15-25s", "visual": "Back to face or results screen", "text": "Results speak for themselves"},
            "scene_4": {"duration": "25-30s", "visual": "CTA screen", "text": "Follow for more AI hacks!"},
            "caption": f"This reel took 5 minutes to make with AI 🔥\n\nSave this for later! 📌\n\n#reels #ai #automation",
            "hashtags": ["#reels", "#ai", "#automation", "#marketing", "#agency"]
        }

        return {
            "title": f"Reel: {topic}",
            "caption": script["caption"],
            "script": script,
            "hashtags": script["hashtags"],
            "image_prompt": f"Instagram reel thumbnail: {topic}, eye-catching, vibrant colors, text overlay"
        }

    def _generate_linkedin_post(self, topic: str) -> Dict:
        """Generate LinkedIn post"""
        hooks = self.knowledge_base["hooks"]["linkedin"]
        hashtags = self.knowledge_base["hashtag_sets"]["linkedin"]

        hook = random.choice(hooks).format(topic=topic, controversial_take="AI won't replace you, but someone using AI will")

        body = f"""{hook}

After helping 50+ agencies implement AI automation, here's what actually works:

1. Start with one repetitive task
2. Build systems, not just scripts
3. Measure everything
4. Scale what works

The agencies winning right now aren't doing more.
They're doing less, better, with AI.

Thoughts? Agree or disagree? 👇

#{' #'.join([h.replace('#', '') for h in hashtags[:5]])}"""

        return {
            "title": hook[:100],
            "caption": body,
            "hashtags": hashtags,
            "image_prompt": f"LinkedIn post image: professional, {topic}, clean design, corporate aesthetic"
        }

    def _generate_linkedin_article(self, topic: str) -> Dict:
        """Generate LinkedIn article outline"""
        return {
            "title": f"The Complete Guide to {topic} for Agencies",
            "caption": f"I just published a comprehensive guide on {topic}.\n\nIn this article, I cover:\n✅ The current landscape\n✅ Common mistakes\n✅ Step-by-step implementation\n✅ Real case studies\n\nLink in comments 👇",
            "hashtags": self.knowledge_base["hashtag_sets"]["linkedin"],
            "image_prompt": f"LinkedIn article header: {topic}, professional design, article cover",
            "article_outline": {
                "introduction": f"Why {topic} matters now",
                "section_1": "The problem with current approaches",
                "section_2": "AI-powered solutions",
                "section_3": "Implementation guide",
                "conclusion": "Next steps and CTA"
            }
        }

    def _generate_twitter_thread(self, topic: str) -> Dict:
        """Generate Twitter thread"""
        hooks = self.knowledge_base["hooks"]["twitter"]
        hashtags = self.knowledge_base["hashtag_sets"]["twitter"]

        hook = random.choice(hooks).format(topic=topic, controversial_take="Most agencies are using AI wrong")

        tweets = [
            f"{hook}\n\nA thread on what actually works: 🧵",
            "1/ First, stop trying to automate everything at once.\n\nPick ONE repetitive task.\n\nMaster it.\n\nThen move to the next.",
            "2/ The real power isn't in the AI tools.\n\nIt's in the SYSTEMS you build around them.",
            "3/ Document everything.\n\nIf you can't explain it simply, you don't understand it well enough.",
            "4/ Start measuring before you start optimizing.\n\nYou can't improve what you don't track.",
            f"5/ Want to learn more about {topic}?\n\nFollow @ragspro for daily AI automation tips.\n\nRT the first tweet to share this thread! 🙏"
        ]

        return {
            "title": hook,
            "caption": tweets[0],
            "thread": tweets,
            "hashtags": hashtags,
            "image_prompt": f"Twitter thread visual: {topic}, thread emoji, clean design"
        }

    def _generate_tweet(self, topic: str) -> Dict:
        """Generate single tweet"""
        tweets = [
            f"The best time to start using AI for {topic} was 6 months ago.\n\nThe second best time is today.",
            f"Your competitors are already using AI for {topic}.\n\nAre you?",
            f"3 AI tools for {topic}:\n\n1. ChatGPT for copy\n2. Midjourney for visuals\n3. RAGSPRO for automation\n\nWhat else would you add?",
        ]

        return {
            "title": topic,
            "caption": random.choice(tweets),
            "hashtags": self.knowledge_base["hashtag_sets"]["twitter"][:3]
        }

    def _generate_youtube_script(self, topic: str) -> Dict:
        """Generate YouTube video script"""
        return {
            "title": f"How to {topic} with AI (Complete Tutorial)",
            "caption": f"In this video, I show you exactly how to use AI for {topic}.\n\nTimestamps:\n0:00 - Intro\n1:30 - The Problem\n3:00 - The Solution\n10:00 - Step-by-Step Tutorial\n20:00 - Results\n22:00 - Final Thoughts\n\nDon't forget to subscribe for more AI tutorials!",
            "hashtags": ["#AI", "#Tutorial", "#Automation", "#Agency"],
            "image_prompt": f"YouTube thumbnail: {topic}, face with expression, bold text, 1280x720, high contrast",
            "script": {
                "intro": f"Hey everyone! In today's video, we're diving deep into {topic}...",
                "main_content": "[Detailed tutorial content would go here]",
                "outro": "If you found this helpful, hit that like button and subscribe!"
            }
        }

    def _generate_generic_content(self, topic: str) -> Dict:
        """Generate generic content"""
        return {
            "title": f"Content about {topic}",
            "caption": f"Here's what you need to know about {topic}...",
            "hashtags": ["#AI", "#Automation"]
        }

    def _get_random_topic(self) -> str:
        """Get a random content topic"""
        topics = [
            "lead generation",
            "content automation",
            "AI agents",
            "marketing automation",
            "client acquisition",
            "agency scaling",
            "social media automation",
            "email automation",
            "AI workflows",
            "automation tools"
        ]
        return random.choice(topics)

    def _generate_content_ideas(self, platform: str, count: int = 5) -> List[Dict]:
        """Generate content ideas"""
        templates = [
            {"type": "educational", "format": "how-to", "topic": "How to set up your first AI agent"},
            {"type": "motivational", "format": "story", "topic": "From 0 to first client in 30 days"},
            {"type": "controversial", "format": "opinion", "topic": "Why most agencies fail with AI"},
            {"type": "tactical", "format": "listicle", "topic": "5 AI tools that actually work"},
            {"type": "behind_scenes", "format": "vlog", "topic": "A day in the life of an AI agency"},
        ]
        return templates[:count]

    def _save_content(self, content_piece: Dict):
        """Save content to file"""
        today = datetime.now().strftime("%Y-%m-%d")
        content_dir = DATA_DIR / "content" / today
        content_dir.mkdir(parents=True, exist_ok=True)

        platform = content_piece["platform"]
        filename = f"{content_piece['content_type']}.json"
        filepath = content_dir / platform / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(content_piece, f, indent=2)

        # Also save caption as text
        txt_path = content_dir / f"{platform}_{content_piece['content_type']}.txt"
        with open(txt_path, 'w') as f:
            f.write(content_piece.get("caption", ""))

    def get_dashboard_data(self) -> Dict:
        """Get data for dashboard"""
        return {
            "profile": {
                "name": self.profile.name,
                "avatar": self.profile.avatar,
                "role": self.profile.role.value,
                "expertise": self.profile.expertise[:5],
                "status": self.profile.status
            },
            "content_stats": {
                "templates_available": sum(len(v) for v in self.knowledge_base["hooks"].values()),
                "platforms_supported": ["instagram", "linkedin", "twitter", "youtube"],
                "content_types": ["carousel", "reel", "post", "thread", "article", "video"]
            },
            "ideas_generated": self.profile.ideas_generated,
            "tasks_completed": self.profile.tasks_completed,
            "recent_content": self.ideas[-3:] if self.ideas else []
        }


if __name__ == "__main__":
    from . import AgentCommunicationBus

    bus = AgentCommunicationBus()
    agent = ContentCreationAgent(bus)

    # Test content generation
    print("Content Agent Profile:")
    print(json.dumps(agent.get_dashboard_data(), indent=2))
