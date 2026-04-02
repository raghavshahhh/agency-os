#!/usr/bin/env python3
"""
RAGS Pro Auto-Proposal Generator
Uses NVIDIA LLM to create personalized proposals
"""

import json
import requests
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

DATA_DIR = Path(__file__).parent.parent / "data"
PROPOSALS_DIR = DATA_DIR / "proposals"
PROPOSALS_DIR.mkdir(exist_ok=True)

SERVICES = {
    "chatbot": {
        "name": "AI Chatbot Development",
        "price": 25000,
        "duration": "1 week",
        "deliverables": [
            "WhatsApp/Telegram/Web chatbot",
            "Lead qualification flow",
            "Auto-response system",
            "Admin dashboard",
            "Integration with your CRM",
        ],
    },
    "automation": {
        "name": "Workflow Automation",
        "price": 35000,
        "duration": "2 weeks",
        "deliverables": [
            "n8n/Make.com setup",
            "3 custom integrations",
            "Automated data sync",
            "Error handling & alerts",
            "Documentation & training",
        ],
    },
    "scraper": {
        "name": "Lead Scraper Tool",
        "price": 45000,
        "duration": "2 weeks",
        "deliverables": [
            "Multi-source scraping (Reddit, LinkedIn)",
            "Email extraction & validation",
            "Auto-outreach system",
            "Dashboard with analytics",
            "CSV/JSON export",
        ],
    },
    "saas": {
        "name": "SaaS MVP Development",
        "price": 75000,
        "duration": "3 weeks",
        "deliverables": [
            "Full-stack Next.js app",
            "Authentication & database",
            "Core features implementation",
            "Payment integration",
            "Deployment & hosting",
        ],
    },
}


def call_nvidia_llm(prompt: str, max_tokens: int = 1000) -> str:
    """Call NVIDIA LLM"""
    try:
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "meta/llama-3.1-8b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return None
    except Exception as e:
        print(f"LLM error: {e}")
        return None


def generate_proposal(client_info: dict, service_type: str) -> dict:
    """Generate AI-powered proposal"""
    service = SERVICES.get(service_type, SERVICES["automation"])

    prompt = f"""Create a professional proposal for a client.

Client Info:
- Name: {client_info.get('name', 'Client')}
- Company: {client_info.get('company', 'Company')}
- Industry: {client_info.get('industry', 'General')}
- Pain Points: {client_info.get('pain_points', 'Manual work, slow processes')}

Service: {service['name']}
Price: ₹{service['price']:,}
Duration: {service['duration']}

Write:
1. Executive Summary (2-3 sentences on why this solution fits their pain points)
2. Problem Statement (what they're struggling with)
3. Solution Overview (how my service solves it)
4. Expected Results (quantifiable outcomes)
5. Timeline (breakdown by days)

Keep it professional but conversational. Gen-Z founder energy - confident, not corporate.
"""

    content = call_nvidia_llm(prompt, max_tokens=800)

    if not content:
        # Fallback template
        content = f"""## Executive Summary

I'll build a custom {service['name'].lower()} that eliminates your manual work and saves 10+ hours per week.

## Problem Statement

You're currently spending too much time on repetitive tasks that could be automated. This is costing you money and slowing your growth.

## Solution

{service['name']} - A complete automation system that handles the work for you.

## Expected Results

- 80% reduction in manual tasks
- 3x faster response time
- 24/7 operation without human intervention

## Timeline

{service['duration']} from start to delivery."""

    proposal = {
        "id": f"PROP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "client": client_info,
        "service": service,
        "content": content,
        "generated_at": datetime.now().isoformat(),
        "status": "generated",
        "price": service["price"],
    }

    # Save proposal
    filename = PROPOSALS_DIR / f"{proposal['id']}.json"
    with open(filename, "w") as f:
        json.dump(proposal, f, indent=2)

    # Generate HTML version
    html_content = generate_html_proposal(proposal)
    html_file = PROPOSALS_DIR / f"{proposal['id']}.html"
    with open(html_file, "w") as f:
        f.write(html_content)

    return proposal


def generate_html_proposal(proposal: dict) -> str:
    """Generate HTML proposal"""
    service = proposal["service"]
    content = proposal["content"].replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Proposal - {service['name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
        .header {{ border-bottom: 2px solid #6366f1; padding-bottom: 20px; margin-bottom: 30px; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #6366f1; }}
        .price {{ font-size: 32px; color: #6366f1; margin: 20px 0; }}
        .cta {{ background: #6366f1; color: white; padding: 15px 30px; text-decoration: none; border-radius: 30px; display: inline-block; margin-top: 20px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">RAGS Pro</div>
        <p>AI Automation Agency</p>
    </div>

    <h1>Proposal: {service['name']}</h1>
    <p><strong>For:</strong> {proposal['client'].get('name', 'Client')}</p>
    <p><strong>Date:</strong> {proposal['generated_at'][:10]}</p>

    <div class="price">₹{service['price']:,}</div>
    <p><strong>Duration:</strong> {service['duration']}</p>

    <div class="content">
        {content}
    </div>

    <h2>Deliverables</h2>
    <ul>
        {''.join(f'<li>{d}</li>' for d in service['deliverables'])}
    </ul>

    <h2>Payment Terms</h2>
    <p>50% upfront to start project<br>
    50% on delivery</p>

    <a href="#" class="cta">Accept Proposal & Pay</a>

    <div class="footer">
        <p><strong>Raghav Shah</strong><br>
        Founder, RAGS Pro<br>
        raghav@ragspro.com<br>
        +91 98765 43210</p>
    </div>
</body>
</html>"""


def generate_contract(client_info: dict, service_type: str, proposal_id: str) -> dict:
    """Generate service agreement"""
    service = SERVICES.get(service_type, SERVICES["automation"])

    contract = {
        "id": f"CONT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "proposal_id": proposal_id,
        "client": client_info,
        "service": service,
        "terms": {
            "payment": "50% upfront, 50% on delivery",
            "timeline": service["duration"],
            "revisions": "2 rounds of revisions included",
            "support": "30 days free support after delivery",
            "confidentiality": "All client data kept confidential",
            "ip_rights": "Client owns all code and IP",
        },
        "generated_at": datetime.now().isoformat(),
    }

    # Save contract
    filename = PROPOSALS_DIR / f"{contract['id']}.json"
    with open(filename, "w") as f:
        json.dump(contract, f, indent=2)

    return contract


if __name__ == "__main__":
    # Test
    test_client = {
        "name": "Test Client",
        "company": "TestCorp",
        "industry": "SaaS",
        "pain_points": "Slow lead response, manual data entry",
    }

    proposal = generate_proposal(test_client, "automation")
    print(f"Generated proposal: {proposal['id']}")
    print(f"Price: ₹{proposal['price']:,}")
