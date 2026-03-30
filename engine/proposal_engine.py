#!/usr/bin/env python3
"""
RAGSPRO Proposal Engine - Generates proposals for top leads
Saves to data/proposals/YYYY-MM-DD/
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    NVIDIA_API_KEY,
    NVIDIA_API_URL,
    NVIDIA_MODEL,
    get_today_proposals_folder,
    DATA_DIR,
    AGENCY_NAME,
    AGENCY_TAGLINE,
    SERVICES
)


def call_nvidia(prompt, max_tokens=500):
    """Call NVIDIA NIM API"""
    if not NVIDIA_API_KEY:
        print("✗ NVIDIA_API_KEY not set!")
        return None

    import requests

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": NVIDIA_MODEL,
        "messages": [
            {"role": "system", "content": f"You are a proposal writer for {AGENCY_NAME}."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def load_top_leads(limit=5):
    """Load top 5 leads by score"""
    leads_file = DATA_DIR / "leads.json"
    if not leads_file.exists():
        return []

    with open(leads_file, 'r') as f:
        leads = json.load(f)

    # Sort by score descending
    leads.sort(key=lambda x: x.get("score", 0), reverse=True)
    return leads[:limit]


def generate_fiverr_proposal(lead):
    """Generate Fiverr proposal (~150 words)"""
    title = lead.get("title", "")
    requirement = lead.get("requirement", "")
    platform = lead.get("platform", "")

    prompt = f"""Write a Fiverr proposal for this client.

Lead Title: {title}
Requirements: {requirement}

Services offered: {', '.join(SERVICES)}

Guidelines:
- Keep it under 150 words
- Friendly, professional tone
- 2-3 sentences max
- Mention relevant experience
- End with offer to discuss
- No "Dear Sir/Madam"

Write ONLY the proposal text."""

    return call_nvidia(prompt, max_tokens=300)


def generate_upwork_proposal(lead):
    """Generate Upwork proposal (~100 words)"""
    title = lead.get("title", "")
    requirement = lead.get("requirement", "")

    prompt = f"""Write an Upwork proposal.

Job: {title}
Details: {requirement}

Services: {', '.join(SERVICES)}

Guidelines:
- Under 100 words
- Concise and impactful
- Highlight relevant skill
- Include portfolio mention
- Direct, no fluff

Write ONLY the proposal."""

    return call_nvidia(prompt, max_tokens=250)


def generate_cold_email(lead):
    """Generate cold email (3 lines)"""
    title = lead.get("title", "")
    requirement = lead.get("requirement", "")[:200]

    prompt = f"""Write a cold email.

Lead: {title}
Need: {requirement}

Guidelines:
- Exactly 3 lines max
- Line 1: Hook (noticed your post)
- Line 2: Value prop (how RAGSPRO helps)
- Line 3: Soft CTA (want to chat?)
- Personal, not salesy

Write ONLY the email."""

    return call_nvidia(prompt, max_tokens=150)


def save_proposal(lead_id, proposals):
    """Save proposal to file"""
    today_folder = get_today_proposals_folder()
    filepath = today_folder / f"{lead_id}.json"

    with open(filepath, 'w') as f:
        json.dump(proposals, f, indent=2)

    return filepath


def main():
    """Generate proposals for top 5 leads"""
    print("📄 RAGSPRO Proposal Engine")
    print("=" * 40)

    # Load top leads
    top_leads = load_top_leads(5)

    if not top_leads:
        print("✗ No leads found. Run lead_scraper.py first!")
        return

    print(f"Found {len(top_leads)} top leads\n")

    proposals_generated = 0

    for lead in top_leads:
        lead_id = lead.get("id", "unknown")
        title = lead.get("title", "No title")[:50]
        score = lead.get("score", 0)

        print(f"\n🔹 [{score}] {title}...")

        # Generate proposals
        print("  Generating Fiverr...", end="")
        fiverr = generate_fiverr_proposal(lead)
        print(" ✓" if fiverr else " ✗")

        print("  Generating Upwork...", end="")
        upwork = generate_upwork_proposal(lead)
        print(" ✓" if upwork else " ✗")

        print("  Generating Cold Email...", end="")
        email = generate_cold_email(lead)
        print(" ✓" if email else " ✗")

        if fiverr or upwork or email:
            proposals = {
                "lead_id": lead_id,
                "lead_title": lead.get("title", ""),
                "lead_url": lead.get("url", ""),
                "generated_at": datetime.now().isoformat(),
                "fiverr": {
                    "platform": "Fiverr",
                    "type": "Proposal",
                    "content": fiverr or "Generation failed"
                },
                "upwork": {
                    "platform": "Upwork",
                    "type": "Proposal",
                    "content": upwork or "Generation failed"
                },
                "cold_email": {
                    "platform": "Email",
                    "type": "Cold Email",
                    "content": email or "Generation failed"
                }
            }

            filepath = save_proposal(lead_id, proposals)
            proposals_generated += 1
            print(f"  💾 Saved to {filepath.name}")

    print(f"\n✅ Generated proposals for {proposals_generated}/{len(top_leads)} leads")

    # Show preview of first proposal
    if proposals_generated > 0:
        today_folder = get_today_proposals_folder()
        files = list(today_folder.glob("*.json"))
        if files:
            with open(files[0], 'r') as f:
                sample = json.load(f)
            print("\n--- Sample Proposal Preview ---")
            print(f"Lead: {sample['lead_title'][:60]}...")
            print(f"\nFiverr:\n{sample['fiverr']['content'][:200]}...")


if __name__ == "__main__":
    main()
