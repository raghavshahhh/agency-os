#!/usr/bin/env python3
"""
RAGSPRO Content Engine - Generates daily social media content
Platforms: LinkedIn, Twitter, Instagram, Reel Script
Uses NVIDIA NIM (Qwen) API
"""

import json
import sys
import requests
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    NVIDIA_API_KEY, NVIDIA_API_URL, NVIDIA_MODEL,
    AGENCY_NAME, AGENCY_TAGLINE, SERVICES,
    LINKEDIN_TOPICS, SOCIAL_LINKS, get_today_folder
)


def call_nvidia(prompt, max_tokens=600):
    """Call NVIDIA NIM API for content generation with error handling"""
    if not NVIDIA_API_KEY:
        print("✗ NVIDIA_API_KEY not set!")
        return None

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": NVIDIA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are the social media content creator for {AGENCY_NAME}, "
                    f"an AI agency that offers: {', '.join(SERVICES)}. "
                    f"Tagline: {AGENCY_TAGLINE}. "
                    "Write engaging, professional content. Use emojis strategically. "
                    "Never use generic filler. Be specific and value-driven."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        # Validate response structure
        if not isinstance(data, dict):
            print(f"✗ API Error: Invalid response format")
            return None

        choices = data.get("choices", [])
        if not choices or not isinstance(choices, list):
            print(f"✗ API Error: No choices in response")
            return None

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            print(f"✗ API Error: Invalid choice format")
            return None

        message = first_choice.get("message", {})
        if not isinstance(message, dict):
            print(f"✗ API Error: Invalid message format")
            return None

        content = message.get("content", "")
        if not content:
            print(f"✗ API Error: Empty content")
            return None

        return content.strip()

    except requests.exceptions.Timeout:
        print(f"✗ API Error: Request timeout after 60s")
        return None
    except requests.exceptions.ConnectionError:
        print(f"✗ API Error: Connection failed")
        return None
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else 0
        if status_code == 429:
            print(f"✗ API Error: Rate limited (429). Try again in a few minutes.")
        else:
            print(f"✗ API Error: HTTP {status_code}")
        return None
    except json.JSONDecodeError:
        print(f"✗ API Error: Invalid JSON response")
        return None
    except Exception as e:
        print(f"✗ API Error: {type(e).__name__}: {str(e)[:50]}")
        return None


def generate_linkedin(topic=None):
    """Generate LinkedIn post (~300 words)"""
    if not topic:
        day_of_week = datetime.now().weekday()
        topic = LINKEDIN_TOPICS.get(day_of_week, "AI automation for businesses")

    prompt = f"""Write a LinkedIn post about: {topic}

Guidelines:
- 250-350 words
- Hook in first line (pattern interrupt)
- Use line breaks for readability
- Include 2-3 bullet points or numbered list
- End with a question or CTA
- Add 3-5 relevant hashtags at the end
- Professional but conversational tone
- Mention {AGENCY_NAME} naturally (not forcefully)
- Include a personal insight or story angle

Write ONLY the post text, ready to copy-paste."""

    return call_nvidia(prompt, max_tokens=600)


def generate_twitter(topic=None):
    """Generate Twitter/X post (under 280 chars)"""
    if not topic:
        day_of_week = datetime.now().weekday()
        topic = LINKEDIN_TOPICS.get(day_of_week, "AI automation")

    prompt = f"""Write a Twitter post about: {topic}

Guidelines:
- MUST be under 280 characters total
- Punchy, high-impact one-liner
- Include 1-2 emojis
- Add 1-2 hashtags (count in character limit)
- No fluff, every word matters

Write ONLY the tweet text."""

    return call_nvidia(prompt, max_tokens=100)


def generate_instagram(topic=None):
    """Generate Instagram caption"""
    if not topic:
        day_of_week = datetime.now().weekday()
        topic = LINKEDIN_TOPICS.get(day_of_week, "tech productivity")

    prompt = f"""Write an Instagram caption about: {topic}

Guidelines:
- 100-150 words
- Start with a hook emoji + bold statement
- Conversational, relatable tone
- Include a CTA (save/share/comment)
- Add 15-20 relevant hashtags at the end (separated by spaces)
- Make it visual and engaging

Write ONLY the caption text."""

    return call_nvidia(prompt, max_tokens=400)


def generate_reel_script(topic=None):
    """Generate Reel/Short video script"""
    if not topic:
        day_of_week = datetime.now().weekday()
        topic = LINKEDIN_TOPICS.get(day_of_week, "AI tips")

    prompt = f"""Write a 30-60 second Instagram Reel script about: {topic}

Guidelines:
- Hook (first 3 seconds): attention-grabbing question or statement
- Body: 3 quick points or steps
- CTA: follow/save/share
- Format as:
  [HOOK] ...
  [POINT 1] ...
  [POINT 2] ...
  [POINT 3] ...
  [CTA] ...
- Keep language simple, punchy, spoken-word style
- Include text overlay suggestions in [brackets]

Write ONLY the script."""

    return call_nvidia(prompt, max_tokens=400)


def main():
    """Generate all daily content"""
    print(f"📝 {AGENCY_NAME} Content Engine")
    print("=" * 40)
    print(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")

    today_folder = get_today_folder()
    print(f"📂 Saving to: {today_folder}\n")

    day_of_week = datetime.now().weekday()
    topic = LINKEDIN_TOPICS.get(day_of_week, "AI automation")
    print(f"🎯 Today's theme: {topic}\n")

    content_files = {
        "linkedin.txt": ("LinkedIn", generate_linkedin),
        "twitter.txt": ("Twitter", generate_twitter),
        "instagram.txt": ("Instagram", generate_instagram),
        "reel.txt": ("Reel Script", generate_reel_script),
    }

    generated = 0
    results = {}

    for filename, (label, generator) in content_files.items():
        filepath = today_folder / filename
        print(f"  Generating {label}...", end="", flush=True)

        content = generator(topic)
        if content:
            filepath.write_text(content)
            results[label] = content
            generated += 1
            print(f" ✓ ({len(content)} chars)")
        else:
            print(" ✗ Failed")

        # Rate limiting delay between API calls
        time.sleep(2)

    print(f"\n{'=' * 40}")
    print(f"✅ Generated {generated}/{len(content_files)} pieces of content")
    print(f"📂 Saved to: {today_folder}")

    # Preview
    if results:
        print("\n--- LinkedIn Preview ---")
        linkedin = results.get("LinkedIn", "")
        print(linkedin[:200] + "..." if len(linkedin) > 200 else linkedin)

    return results


if __name__ == "__main__":
    main()
