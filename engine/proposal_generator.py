#!/usr/bin/env python3
"""
RAGS Pro Auto-Proposal Generator v2
Uses NVIDIA LLM or Anthropic to create personalized proposals
"""

import json
import requests
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import uuid

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

DATA_DIR = Path(__file__).parent.parent / "data"
PROPOSALS_DIR = DATA_DIR / "proposals"
PROPOSALS_DIR.mkdir(exist_ok=True)

@dataclass
class ProposalSection:
    title: str
    content: str
    order: int

@dataclass
class Proposal:
    id: str
    lead_id: str
    client_name: str
    project_title: str
    sections: List[ProposalSection]
    pricing: Dict[str, Any]
    timeline: str
    terms: str
    status: str
    created_at: str
    sent_at: Optional[str]

SERVICES = {
    "chatbot": {
        "name": "AI Chatbot Development",
        "price": 25000,
        "price_range": {"min": 15000, "max": 50000},
        "duration": "1-2 weeks",
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
        "price_range": {"min": 25000, "max": 75000},
        "duration": "2-3 weeks",
        "deliverables": [
            "n8n/Make.com setup",
            "3-5 custom integrations",
            "Automated data sync",
            "Error handling & alerts",
            "Documentation & training",
        ],
    },
    "scraper": {
        "name": "Lead Scraper Tool",
        "price": 45000,
        "price_range": {"min": 35000, "max": 80000},
        "duration": "2-3 weeks",
        "deliverables": [
            "Custom web scraper",
            "Multi-source extraction",
            "Data enrichment",
            "Export to CSV/CRM",
            "Scheduling & monitoring",
        ],
    },
    "website": {
        "name": "Website Development",
        "price": 50000,
        "price_range": {"min": 35000, "max": 150000},
        "duration": "3-6 weeks",
        "deliverables": [
            "Custom responsive website",
            "CMS integration",
            "SEO optimization",
            "Performance tuning",
            "Analytics setup",
        ],
    },
    "ai_agent": {
        "name": "AI Agent System",
        "price": 75000,
        "price_range": {"min": 50000, "max": 200000},
        "duration": "4-6 weeks",
        "deliverables": [
            "Custom AI agent development",
            "Multi-channel integration",
            "Knowledge base setup",
            "Training & fine-tuning",
            "Monitoring dashboard",
        ],
    },
    "full_stack": {
        "name": "Full-Stack Development",
        "price": 150000,
        "price_range": {"min": 100000, "max": 500000},
        "duration": "6-12 weeks",
        "deliverables": [
            "Complete web application",
            "Database design",
            "API development",
            "Frontend & backend",
            "Deployment & hosting",
        ],
    },
}


class ProposalGeneratorV2:
    """Enhanced proposal generator with AI capabilities"""

    def __init__(self):
        self.data_dir = DATA_DIR
        self.proposals_dir = PROPOSALS_DIR
        self.proposals_dir.mkdir(parents=True, exist_ok=True)

    def _call_llm(self, prompt: str, max_tokens: int = 1500) -> str:
        """Call LLM API (NVIDIA or Anthropic)"""

        # Try Anthropic first
        if ANTHROPIC_API_KEY:
            try:
                return self._call_anthropic(prompt, max_tokens)
            except Exception as e:
                print(f"Anthropic error: {e}")

        # Try NVIDIA
        if NVIDIA_API_KEY:
            try:
                return self._call_nvidia(prompt, max_tokens)
            except Exception as e:
                print(f"NVIDIA error: {e}")

        # Fallback
        return self._generate_fallback(prompt)

    def _call_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Call Anthropic Claude API"""
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": "claude-sonnet-4-6",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        raise Exception(f"API error: {response.status_code}")

    def _call_nvidia(self, prompt: str, max_tokens: int) -> str:
        """Call NVIDIA API"""
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "meta/llama3-70b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }

        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        raise Exception(f"API error: {response.status_code}")

    def _generate_fallback(self, prompt: str) -> str:
        """Fallback response when AI is unavailable"""
        return """Executive Summary: This project will deliver significant value through automation and AI.

Scope: Custom solution tailored to your requirements.

Deliverables: Complete system with documentation and support.

Timeline: As discussed in our conversation.

Investment: Competitive pricing with clear ROI."""

    def _get_lead_context(self, lead: Dict) -> str:
        """Extract context from lead data"""
        title = lead.get("title", "")
        requirement = lead.get("requirement", lead.get("description", ""))
        platform = lead.get("platform", "")
        contact = lead.get("contact", {})

        # Try to extract budget hints
        budget_hints = []
        for keyword in ["$", "₹", "budget", "rate", "pay", "cost"]:
            if keyword in title.lower() or keyword in requirement.lower():
                budget_hints.append(f"Mentioned: {keyword}")

        context = f"""
Lead Source: {platform}
Project Title: {title}
Requirements: {requirement[:500]}
Budget Indicators: {', '.join(budget_hints) if budget_hints else 'Not mentioned'}
"""
        return context

    def generate_proposal(self, lead: Dict, service_type: str = "automation",
                         tier: str = "standard") -> Proposal:
        """Generate AI-powered proposal"""

        service = SERVICES.get(service_type, SERVICES["automation"])
        lead_context = self._get_lead_context(lead)

        # Get client name
        client_name = lead.get("name", "")
        if not client_name or client_name == "Unknown":
            contact = lead.get("contact", {})
            if contact.get("reddit_user"):
                client_name = contact["reddit_user"].replace("u/", "").title()
            else:
                client_name = "Valued Client"

        # Adjust price based on tier
        price_range = service["price_range"]
        if tier == "basic":
            price = price_range["min"]
        elif tier == "premium":
            price = price_range["max"]
        else:
            price = service["price"]

        # Generate AI content
        prompt = f"""You are a professional proposal writer for RAGSPRO, an AI development agency.

LEAD INFORMATION:
{lead_context}

SERVICE: {service['name']}
PRICE: ₹{price:,}
DURATION: {service['duration']}

Write a compelling proposal with these sections:

1. EXECUTIVE SUMMARY (2-3 sentences)
2. SCOPE OF WORK (bullet points)
3. DELIVERABLES (numbered list)
4. TIMELINE (phases)
5. INVESTMENT (justify the price)
6. NEXT STEPS (clear CTA)

Make it personal, professional, and persuasive. Address their specific needs from the requirements."""

        ai_content = self._call_llm(prompt)

        # Parse AI response into sections
        sections = self._parse_sections(ai_content)

        # Create proposal
        proposal_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        proposal = Proposal(
            id=proposal_id,
            lead_id=lead.get("id", ""),
            client_name=client_name,
            project_title=lead.get("title", "AI Development Project"),
            sections=sections,
            pricing={
                "price": price,
                "currency": "INR",
                "payment_terms": "50% upfront, 50% on completion"
            },
            timeline=service["duration"],
            terms="Includes revisions, 30-day support, and documentation.",
            status="draft",
            created_at=now,
            sent_at=None
        )

        self._save_proposal(proposal)
        return proposal

    def _parse_sections(self, content: str) -> List[ProposalSection]:
        """Parse AI content into structured sections"""
        sections = []

        # Try to find section headers
        section_markers = [
            ("Executive Summary", 1),
            ("Scope of Work", 2),
            ("Deliverables", 3),
            ("Timeline", 4),
            ("Investment", 5),
            ("Next Steps", 6)
        ]

        lines = content.split('\n')
        current_section = None
        current_content = []

        for line in lines:
            line_lower = line.lower().strip()

            # Check if this line starts a new section
            found_section = None
            for marker, order in section_markers:
                if marker.lower() in line_lower or marker.upper() in line:
                    found_section = (marker, order)
                    break

            if found_section:
                # Save previous section
                if current_section and current_content:
                    sections.append(ProposalSection(
                        title=current_section[0],
                        content='\n'.join(current_content).strip(),
                        order=current_section[1]
                    ))
                current_section = found_section
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section and current_content:
            sections.append(ProposalSection(
                title=current_section[0],
                content='\n'.join(current_content).strip(),
                order=current_section[1]
            ))

        # If parsing failed, create generic sections
        if len(sections) < 3:
            sections = [
                ProposalSection("Executive Summary", content, 1),
                ProposalSection("Scope of Work", "Custom solution development", 2),
                ProposalSection("Deliverables", "Complete working system", 3),
                ProposalSection("Timeline", "As discussed", 4),
                ProposalSection("Investment", "Competitive pricing", 5),
                ProposalSection("Next Steps", "Schedule a call", 6)
            ]

        return sections

    def _save_proposal(self, proposal: Proposal):
        """Save proposal to file"""
        proposal_file = self.proposals_dir / f"{proposal.id}.json"

        data = {
            "id": proposal.id,
            "lead_id": proposal.lead_id,
            "client_name": proposal.client_name,
            "project_title": proposal.project_title,
            "sections": [{"title": s.title, "content": s.content, "order": s.order} for s in proposal.sections],
            "pricing": proposal.pricing,
            "timeline": proposal.timeline,
            "terms": proposal.terms,
            "status": proposal.status,
            "created_at": proposal.created_at,
            "sent_at": proposal.sent_at
        }

        with open(proposal_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Get proposal by ID"""
        proposal_file = self.proposals_dir / f"{proposal_id}.json"

        if not proposal_file.exists():
            return None

        with open(proposal_file, 'r') as f:
            data = json.load(f)

        sections = [ProposalSection(**s) for s in data.get("sections", [])]

        return Proposal(
            id=data["id"],
            lead_id=data["lead_id"],
            client_name=data["client_name"],
            project_title=data["project_title"],
            sections=sections,
            pricing=data["pricing"],
            timeline=data["timeline"],
            terms=data["terms"],
            status=data["status"],
            created_at=data["created_at"],
            sent_at=data.get("sent_at")
        )

    def get_all_proposals(self) -> List[Proposal]:
        """Get all proposals"""
        proposals = []

        for proposal_file in self.proposals_dir.glob("*.json"):
            try:
                proposal = self.get_proposal(proposal_file.stem)
                if proposal:
                    proposals.append(proposal)
            except Exception as e:
                print(f"Error loading {proposal_file}: {e}")

        return sorted(proposals, key=lambda p: p.created_at, reverse=True)

    def update_proposal_status(self, proposal_id: str, status: str) -> bool:
        """Update proposal status"""
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return False

        proposal.status = status
        if status == "sent":
            proposal.sent_at = datetime.now().isoformat()

        self._save_proposal(proposal)
        return True

    def export_proposal_text(self, proposal: Proposal) -> str:
        """Export as formatted text"""
        text = f"""PROPOSAL
{'='*60}

Project: {proposal.project_title}
Client: {proposal.client_name}
Date: {datetime.now().strftime('%B %d, %Y')}

"""

        for section in sorted(proposal.sections, key=lambda s: s.order):
            text += f"\n{section.title.upper()}\n{'-'*60}\n\n{section.content}\n\n"

        text += f"""
{'='*60}

INVESTMENT: ₹{proposal.pricing.get('price', 0):,}
TIMELINE: {proposal.timeline}
TERMS: {proposal.terms}

Prepared by RAGSPRO
AI Development Agency
📧 ragsproai@gmail.com
🌐 ragspro.com
"""

        return text

    def get_proposal_stats(self) -> Dict[str, Any]:
        """Get proposal statistics"""
        proposals = self.get_all_proposals()

        if not proposals:
            return {
                "total": 0, "draft": 0, "sent": 0, "accepted": 0,
                "rejected": 0, "potential_value": 0, "won_value": 0
            }

        sent_proposals = [p for p in proposals if p.status == "sent"]
        accepted_proposals = [p for p in proposals if p.status == "accepted"]

        return {
            "total": len(proposals),
            "draft": len([p for p in proposals if p.status == "draft"]),
            "sent": len(sent_proposals),
            "accepted": len(accepted_proposals),
            "rejected": len([p for p in proposals if p.status == "rejected"]),
            "potential_value": sum(p.pricing.get("price", 0) for p in proposals if p.status in ["draft", "sent"]),
            "won_value": sum(p.pricing.get("price", 0) for p in accepted_proposals),
            "conversion_rate": len(accepted_proposals) / len(sent_proposals) * 100 if sent_proposals else 0
        }

    def suggest_service(self, lead: Dict) -> str:
        """Suggest best service based on lead requirements"""
        title = lead.get("title", "").lower()
        requirement = lead.get("requirement", "").lower()
        text = f"{title} {requirement}"

        # Keyword matching
        keywords = {
            "chatbot": ["chatbot", "bot", "whatsapp", "telegram", "messaging", "chat"],
            "automation": ["automation", "workflow", "integrate", "connect", "sync", "automate"],
            "scraper": ["scraper", "scrape", "extract", "data", "leads", "scraping"],
            "website": ["website", "web", "site", "landing page", "web app"],
            "ai_agent": ["ai", "agent", "autonomous", "llm", "gpt", "claude"],
            "full_stack": ["full stack", "app", "application", "platform", "saas"]
        }

        scores = {}
        for service, words in keywords.items():
            score = sum(2 if word in title else 1 for word in words if word in text)
            scores[service] = score

        # Return highest scoring service
        if scores:
            return max(scores, key=scores.get)
        return "automation"  # default


# Backwards compatibility - keep old class name
ProposalGenerator = ProposalGeneratorV2

# Global instance
proposal_generator = ProposalGeneratorV2()
