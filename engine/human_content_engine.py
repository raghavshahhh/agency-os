#!/usr/bin/env python3
"""
RAGSPRO Human Content Engine
Gen-Z energy, Hinglish mix, no corporate BS
"""

import json
import random
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CONTENT_DIR = DATA_DIR / "content"

# Raghav's voice patterns
RAGHAV_PATTERNS = {
    "hooks": [
        "oye bkl, sunn",
        "samajh gaya?",
        "real talk:",
        "no cap:",
        "plot twist:",
        "unpopular opinion:",
        "sach bolun?",
        "tension mat le, but...",
        "22 saal ki umar mein maine seekha:",
        "Delhi ka ladka bol raha hai..."
    ],
    "transitions": [
        "ab sunn",
        "ek aur baat",
        "aur haan",
        "by the way",
        "side note:",
        "fun fact:"
    ],
    "closings": [
        "samajh gaya?",
        "koi doubt?",
        "DM karna",
        "let's build",
        "RAGSPRO out ✌️",
        "peace out ✌️",
        "build karte hain 💪"
    ],
    "emojis": ["🔥", "💪", "⚡", "🚀", "💯", "✨", "👀", "🎯", "💰", "📈"]
}

# Content templates by platform
CONTENT_TEMPLATES = {
    "linkedin": {
        "styles": [
            "story_hook",
            "contrarian",
            "how_to",
            "behind_scenes",
            "client_win"
        ],
        "structure": [
            "hook\n\nstory\n\nlesson\n\nCTA"
        ]
    },
    "twitter": {
        "styles": ["one_liner", "thread_start", "hot_take"],
        "max_chars": 280
    },
    "instagram": {
        "styles": ["carousel_caption", "reel_hook", "story"],
        "hashtag_count": 15
    }
}


def generate_linkedin_post(topic: str = None) -> str:
    """Generate LinkedIn post with Raghav's voice"""

    if not topic:
        topics = [
            "building LAW AI",
            "20-day MVP",
            "AI automation",
            "client story",
            "startup journey"
        ]
        topic = random.choice(topics)

    hook = random.choice(RAGHAV_PATTERNS["hooks"])
    emoji = random.choice(RAGHAV_PATTERNS["emojis"])
    closing = random.choice(RAGHAV_PATTERNS["closings"])

    # Story-based template
    if topic == "building LAW AI":
        content = f"""{hook} {emoji}

2024 mein ek lawyer ne mujhe bola: "Beta, legal documents 2 ghante mein ban sakte hain?"

Maine kaha: "Nahi uncle, 2 minute mein."

Unhone haske ignore kar diya.

Aaj unki firm 50+ lawyers use karti hai LAW AI.

Moral: Log tumhari umar dekhte hain, tumhara output nahi.

{closing}

#LegalTech #AI #SaaS #NoCode"""

    elif topic == "20-day MVP":
        content = f"""{hook} {emoji}

Client: "MVP kitne time mein?"

Agencies: "3 months, ₹5 lakh"

Me: "20 din, ₹50k"

Client: *skeptical*

Day 20: Product live, client happy, main soya nahi 😅

Ab samajh aaya kyu log slow hain.

Speed = Confidence + No meetings

{closing}

#MVP #StartupIndia #RAGSPRO"""

    elif topic == "AI automation":
        content = f"""{hook} {emoji}

Bhai ne 6 mahine se Excel mein data entry kar raha tha.

Maine ek weekend mein AI agent bana diya.

Ab wo Netflix dekh raha hai, data apne aap enter ho raha hai.

Cost: ₹15,000
Time saved: 20 hours/week
ROI: Infinite

Automation is not the future. It's the present.

{closing}

#Automation #AI #Productivity"""

    else:
        content = f"""{hook} {emoji}

22 saal, Delhi, ₹0 revenue.

Log bolte hain: "Job kar lo pehle"

Main bolta hun: "Product build kar lo pehle"

4 products later:
- LAW AI: 10+ lawyers
- GymFlow: Live
- Agency OS: Building

Age is just a number. Execution is everything.

{closing}

#SoloFounder #Delhi #BuildInPublic"""

    return content


def generate_twitter_post(topic: str = None) -> str:
    """Generate Twitter/X post"""

    tweets = [
        "oye bkl, 2025 mein bhi manual data entry? 🤦‍♂️ AI agent banao, so jao 🔥",
        "20 din = MVP ready 💪 Log 6 mahine sochte hain, main 20 din mein ship kar deta hun 🚀",
        "real talk: AI se darr nahi, use karna seekho 💯 #AI #NoCode",
        "Delhi ka ladka, global clients 🔥 Proof ki location matter nahi, skill matters 💪",
        "samajh gaya? 👀 MVP chahiye → DM karo → 20 din mein live 🎯 Simple.",
        "no cap: Maine 4 products banaye, ₹0 marketing 💰 Content = Marketing",
        "plot twist: Lawyers jo AI se darte the, ab usse ₹50k/month bana rahe hain 😂🔥",
        "22 saal, ₹50k MRR goal 📈 Watch me build in public 💪 #RAGSPRO"
    ]

    return random.choice(tweets)


def generate_instagram_caption(topic: str = None) -> str:
    """Generate Instagram caption"""

    hook = random.choice(RAGHAV_PATTERNS["hooks"])
    emoji = random.choice(RAGHAV_PATTERNS["emojis"])

    caption = f"""{hook} {emoji}

Swipe to see how I built an AI tool that drafts legal documents in 2 minutes ⚡

Lawyers used to take 2 hours.
Now? 2 minutes.

Tech stack:
✅ Next.js 14
✅ OpenAI
✅ Supabase
✅ 20 days

Save karo, share karo, DM karo 📩

.
.
.
.
.
#LegalTech #AI #SaaS #StartupIndia #Delhi #NoCode #IndieHackers #BuildInPublic #RAGSPRO #AITools #LawyerLife #TechStartup #MVP #AIAutomation"""

    return caption


def generate_reel_script(topic: str = None) -> str:
    """Generate Reel/Short script"""

    script = """[HOOK - 0-3s]
Text: "oye bkl, lawyer ko 2 min mein document banake dikhaya 😂"
Visual: Shocked lawyer face

[POINT 1 - 3-10s]
Text: "Pehle: 2 ghante manual typing"
Visual: Typing animation, tired face

[POINT 2 - 10-17s]
Text: "Ab: 2 minutes AI magic ✨"
Visual: Form fill → Generated document

[POINT 3 - 17-25s]
Text: "Lawyer: 'Ye kaise hua?!' 🤯"
Visual: Reaction clip, AI interface

[CTA - 25-30s]
Text: "DM for demo 📩 | Follow for more 🔥"
Visual: Profile pic, follow button
Music: Trending audio"""

    return script


def generate_all_content():
    """Generate all daily content"""
    print("📝 RAGSPRO Human Content Engine")
    print("=" * 40)

    today = datetime.now().strftime("%Y-%m-%d")
    today_folder = CONTENT_DIR / today
    today_folder.mkdir(parents=True, exist_ok=True)

    content_files = {
        "linkedin.txt": generate_linkedin_post(),
        "twitter.txt": generate_twitter_post(),
        "instagram.txt": generate_instagram_caption(),
        "reel.txt": generate_reel_script()
    }

    for filename, content in content_files.items():
        filepath = today_folder / filename
        filepath.write_text(content)
        print(f"✅ {filename}: {len(content)} chars")

    print(f"\n📂 Saved to: {today_folder}")
    return today_folder


if __name__ == "__main__":
    generate_all_content()
