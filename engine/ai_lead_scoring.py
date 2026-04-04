"""
AI Lead Scoring System - Score leads based on multiple factors
Uses LLM API for scoring and enrichment
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
import time

DATA_DIR = Path(__file__).parent.parent / "data"

@dataclass
class LeadScore:
    """Lead score result"""
    lead_id: str
    overall_score: int  # 0-100
    fit_score: int  # How well they match ideal client
    intent_score: int  # Purchase intent
    engagement_score: int  # Engagement potential
    budget_score: int  # Budget match
    timeline_score: int  # Timeline match
    priority: str  # hot/warm/cold
    reasoning: str
    recommended_action: str
    estimated_deal_value: int
    confidence: float

class AILeadScorer:
    """AI-powered lead scoring engine"""

    # Scoring weights
    WEIGHTS = {
        'fit': 0.25,
        'intent': 0.30,
        'engagement': 0.20,
        'budget': 0.15,
        'timeline': 0.10
    }

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.provider = "anthropic" if "claude" in model.lower() else "openai"

        # Ideal client profile (ICP)
        self.icp = {
            "industries": ["SaaS", "AI/ML", "E-commerce", "Healthcare", "Fintech"],
            "company_size": "10-500 employees",
            "budget_range": "₹50,000 - ₹5,00,000",
            "decision_timeline": "1-3 months",
            "pain_points": [
                "Need AI automation",
                "Manual processes slowing growth",
                "Need better lead generation",
                "Want to scale content production"
            ]
        }

    def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call LLM API"""
        if not self.api_key:
            # Fallback: return mock response for testing
            return self._mock_response()

        try:
            if self.provider == "anthropic":
                return self._call_anthropic(prompt, max_tokens)
            else:
                return self._call_openai(prompt, max_tokens)
        except Exception as e:
            print(f"LLM API error: {e}")
            return self._mock_response()

    def _call_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Call Anthropic Claude API"""
        headers = {
            "x-api-key": self.api_key,
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
        else:
            raise Exception(f"Anthropic API error: {response.status_code}")

    def _call_openai(self, prompt: str, max_tokens: int) -> str:
        """Call OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"OpenAI API error: {response.status_code}")

    def _mock_response(self) -> str:
        """Generate mock scoring for testing"""
        return json.dumps({
            "fit_score": 75,
            "intent_score": 60,
            "engagement_score": 70,
            "budget_score": 65,
            "timeline_score": 80,
            "priority": "warm",
            "reasoning": "Good fit for services but needs nurturing",
            "recommended_action": "Send personalized case study and schedule discovery call",
            "estimated_deal_value": 150000,
            "confidence": 0.75
        })

    def score_lead(self, lead: Dict[str, Any]) -> LeadScore:
        """Score a single lead using AI"""
        lead_id = lead.get("id", "unknown")

        # Build scoring prompt
        prompt = f"""You are an expert B2B sales analyst. Score this lead based on our ideal client profile.

IDEAL CLIENT PROFILE:
- Industries: {', '.join(self.icp['industries'])}
- Company Size: {self.icp['company_size']}
- Budget Range: {self.icp['budget_range']}
- Decision Timeline: {self.icp['decision_timeline']}

LEAD INFORMATION:
- Source: {lead.get('platform', 'Unknown')}
- Title: {lead.get('title', 'N/A')}
- Description/Requirements: {lead.get('requirement', lead.get('description', 'N/A'))[:500]}
- Posted: {lead.get('posted_at', 'N/A')}
- Contact: {lead.get('contact', {})}
- Current Status: {lead.get('status', 'NEW')}

Score this lead on a scale of 0-100 for each dimension:
1. FIT_SCORE: How well does this lead match our ideal client profile?
2. INTENT_SCORE: What's their purchase intent based on the requirements?
3. ENGAGEMENT_SCORE: How likely are they to engage with outreach?
4. BUDGET_SCORE: Do they seem to have budget for our services?
5. TIMELINE_SCORE: What's their urgency/timeline?

Also provide:
- PRIORITY: hot/warm/cold
- REASONING: Brief explanation (2-3 sentences)
- RECOMMENDED_ACTION: What should we do next?
- ESTIMATED_DEAL_VALUE: Estimated value in INR
- CONFIDENCE: 0-1 confidence score

Respond ONLY in valid JSON format:
{{
    "fit_score": 75,
    "intent_score": 60,
    "engagement_score": 70,
    "budget_score": 65,
    "timeline_score": 80,
    "priority": "warm",
    "reasoning": "explanation here",
    "recommended_action": "action here",
    "estimated_deal_value": 150000,
    "confidence": 0.75
}}"""

        # Get AI response
        response = self._call_llm(prompt)

        # Parse JSON response
        try:
            # Extract JSON if wrapped in markdown
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)
        except Exception as e:
            print(f"Failed to parse AI response: {e}")
            result = json.loads(self._mock_response())

        # Calculate overall score
        overall = int(
            result.get("fit_score", 50) * self.WEIGHTS['fit'] +
            result.get("intent_score", 50) * self.WEIGHTS['intent'] +
            result.get("engagement_score", 50) * self.WEIGHTS['engagement'] +
            result.get("budget_score", 50) * self.WEIGHTS['budget'] +
            result.get("timeline_score", 50) * self.WEIGHTS['timeline']
        )

        return LeadScore(
            lead_id=lead_id,
            overall_score=overall,
            fit_score=result.get("fit_score", 50),
            intent_score=result.get("intent_score", 50),
            engagement_score=result.get("engagement_score", 50),
            budget_score=result.get("budget_score", 50),
            timeline_score=result.get("timeline_score", 50),
            priority=result.get("priority", "cold"),
            reasoning=result.get("reasoning", ""),
            recommended_action=result.get("recommended_action", ""),
            estimated_deal_value=result.get("estimated_deal_value", 0),
            confidence=result.get("confidence", 0.5)
        )

    def score_batch(self, leads: List[Dict[str, Any]], batch_size: int = 5) -> List[LeadScore]:
        """Score multiple leads in batches"""
        results = []

        for i in range(0, len(leads), batch_size):
            batch = leads[i:i + batch_size]
            for lead in batch:
                try:
                    score = self.score_lead(lead)
                    results.append(score)
                    time.sleep(0.5)  # Rate limiting
                except Exception as e:
                    print(f"Error scoring lead {lead.get('id')}: {e}")
                    continue

        return results

    def sort_leads_by_score(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort leads by AI score"""
        scored_leads = []

        for lead in leads:
            # Check if already scored
            if "ai_score" in lead:
                scored_leads.append(lead)
            else:
                try:
                    score = self.score_lead(lead)
                    lead["ai_score"] = {
                        "overall": score.overall_score,
                        "priority": score.priority,
                        "reasoning": score.reasoning,
                        "estimated_value": score.estimated_deal_value,
                        "scored_at": datetime.now().isoformat()
                    }
                    scored_leads.append(lead)
                except Exception as e:
                    print(f"Error scoring: {e}")
                    lead["ai_score"] = {"overall": 50, "priority": "cold"}
                    scored_leads.append(lead)

        # Sort by score descending
        scored_leads.sort(key=lambda x: x.get("ai_score", {}).get("overall", 0), reverse=True)
        return scored_leads

    def get_hot_leads(self, leads: List[Dict[str, Any]], threshold: int = 75) -> List[Dict[str, Any]]:
        """Get leads with high scores"""
        scored = self.sort_leads_by_score(leads)
        return [l for l in scored if l.get("ai_score", {}).get("overall", 0) >= threshold]

    def generate_scoring_report(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate scoring analytics report"""
        scored = self.sort_leads_by_score(leads)

        priority_counts = {"hot": 0, "warm": 0, "cold": 0}
        total_value = 0

        for lead in scored:
            priority = lead.get("ai_score", {}).get("priority", "cold")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            total_value += lead.get("ai_score", {}).get("estimated_value", 0)

        return {
            "total_leads": len(scored),
            "hot_leads": priority_counts["hot"],
            "warm_leads": priority_counts["warm"],
            "cold_leads": priority_counts["cold"],
            "total_pipeline_value": total_value,
            "average_score": sum(l.get("ai_score", {}).get("overall", 0) for l in scored) / len(scored) if scored else 0,
            "top_leads": scored[:10],
            "generated_at": datetime.now().isoformat()
        }


# Simple rule-based scorer for fallback
class RuleBasedLeadScorer:
    """Rule-based scoring when AI is unavailable"""

    KEYWORDS_HIGH_INTENT = [
        "hiring", "looking for", "need", "urgent", "asap",
        "budget", "ready to", "start immediately", "looking to hire"
    ]

    KEYWORDS_BUDGET = [
        "$", "₹", "budget", "rate", "pay", "cost", "price",
        "hourly", "fixed", "monthly", "retainer"
    ]

    def score_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Score using rules"""
        title = lead.get("title", "").lower()
        desc = lead.get("requirement", lead.get("description", "")).lower()
        text = f"{title} {desc}"

        # Intent score
        intent = sum(10 for kw in self.KEYWORDS_HIGH_INTENT if kw in text)
        intent = min(intent, 100)

        # Budget score
        budget = sum(15 for kw in self.KEYWORDS_BUDGET if kw in text)
        budget = min(budget, 100)

        # Engagement (based on contact info)
        contact = lead.get("contact", {})
        engagement = 50
        if contact.get("emails"):
            engagement += 25
        if contact.get("linkedin"):
            engagement += 15
        if contact.get("phone"):
            engagement += 10

        # Timeline (based on urgency words)
        urgency_words = ["urgent", "asap", "immediately", "today", "this week"]
        timeline = sum(20 for uw in urgency_words if uw in text)
        timeline = min(timeline, 100)

        # Fit (based on industry keywords)
        fit_keywords = ["ai", "ml", "automation", "software", "saas", "app", "website"]
        fit = sum(15 for kw in fit_keywords if kw in text)
        fit = min(fit, 100)

        overall = int(
            fit * 0.25 +
            intent * 0.30 +
            engagement * 0.20 +
            budget * 0.15 +
            timeline * 0.10
        )

        priority = "hot" if overall >= 75 else "warm" if overall >= 50 else "cold"

        return {
            "overall": overall,
            "fit": fit,
            "intent": intent,
            "engagement": engagement,
            "budget": budget,
            "timeline": timeline,
            "priority": priority,
            "scored_at": datetime.now().isoformat()
        }


# Factory function
def get_scorer(use_ai: bool = True) -> AILeadScorer:
    """Get appropriate scorer"""
    if use_ai and (os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")):
        return AILeadScorer()
    return RuleBasedLeadScorer()
