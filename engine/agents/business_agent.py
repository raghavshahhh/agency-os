#!/usr/bin/env python3
"""
RAGSPRO Business Intelligence Agent
Expert agent that knows everything about RAGSPRO and finds opportunities
"""

import json
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


class BusinessIntelligenceAgent(BaseExpertAgent):
    """
    Expert Business Intelligence Agent - The business strategist
    - Knows everything about RAGSPRO business
    - Tracks revenue, clients, metrics
    - Identifies business opportunities
    - Monitors agent health and reports errors
    """

    def __init__(self, comm_bus):
        profile = AgentProfile(
            id="business_agent",
            name="Vikram",
            role=AgentRole.BUSINESS,
            avatar="💼",
            expertise=[
                "Business Strategy",
                "Revenue Optimization",
                "Client Management",
                "Opportunity Identification",
                "Performance Analytics",
                "Risk Management",
                "Growth Hacking",
                "Pricing Strategy",
                "Market Positioning",
                "Agent Orchestration"
            ],
            personality="Strategic, numbers-focused, always thinking about growth, protective of the business",
            goals=[
                "Maximize RAGSPRO revenue",
                "Identify high-value opportunities",
                "Monitor all agent performance",
                "Ensure business continuity"
            ]
        )
        super().__init__(profile, comm_bus)

        self.knowledge_base = {
            "business_profile": {
                "name": "RAGSPRO",
                "founder": "Raghav Shah (Bhupender Pratap)",
                "email": "ragsproai@gmail.com",
                "website": "ragspro.com",
                "location": "Delhi, India",
                "age": 22,
                "revenue_goal": 50000,  # ₹50,000/month
                "current_revenue": 0,
                "currency": "₹"
            },
            "services": [
                {"name": "AI Agent Development", "price": 5000, "description": "Custom AI agents for automation"},
                {"name": "Marketing Automation", "price": 3000, "description": "End-to-end marketing automation"},
                {"name": "Lead Generation System", "price": 4000, "description": "AI-powered lead gen setup"},
                {"name": "Agency OS Setup", "price": 8000, "description": "Complete agency operating system"}
            ],
            "clients": [],
            "opportunities": [],
            "metrics": {
                "leads_generated": 0,
                "clients_acquired": 0,
                "content_pieces": 0,
                "emails_sent": 0
            },
            "agent_health": {},
            "alerts": []
        }

        self._save_knowledge()

    def _handle_message(self, message: Message):
        """Handle incoming messages"""
        if message.message_type == "alert":
            # Handle error alerts from other agents
            self._handle_alert(message)
        elif message.message_type == "request":
            data = message.data
            if data.get("request_type") == "business_report":
                report = self._generate_business_report()
                self.send_message(
                    message.from_agent,
                    "Business report generated",
                    "response",
                    {"report": report}
                )
            elif data.get("request_type") == "opportunities":
                opportunities = self._identify_opportunities()
                self.send_message(
                    message.from_agent,
                    f"Found {len(opportunities)} opportunities",
                    "response",
                    {"opportunities": opportunities}
                )

    def _handle_alert(self, message: Message):
        """Handle error alerts from other agents"""
        alert_data = message.data
        error = alert_data.get("error", "Unknown error")
        agent = message.from_agent

        # Log the alert
        self.knowledge_base["alerts"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "error": error,
            "severity": alert_data.get("severity", "medium")
        })

        # Update agent health
        self.knowledge_base["agent_health"][agent] = {
            "last_error": error,
            "error_count": self.knowledge_base["agent_health"].get(agent, {}).get("error_count", 0) + 1,
            "last_alert": datetime.now().isoformat(),
            "status": "error"
        }

        self._save_knowledge()

        # Log activity
        self.log_activity(f"Alert from {agent}", {"error": error[:100]})

        # If critical, take action
        if alert_data.get("severity") == "critical":
            self.broadcast_idea(
                f"🚨 CRITICAL: {agent} needs immediate attention!",
                {"error": error, "action_required": "Check logs and restart agent"}
            )

    def _generate_business_report(self) -> Dict:
        """Generate comprehensive business report"""
        business = self.knowledge_base["business_profile"]
        metrics = self.knowledge_base["metrics"]
        opportunities = self.knowledge_base["opportunities"]

        # Calculate progress
        revenue_progress = (business["current_revenue"] / business["revenue_goal"]) * 100

        report = {
            "generated_at": datetime.now().isoformat(),
            "business_summary": {
                "name": business["name"],
                "revenue_progress": f"{revenue_progress:.1f}%",
                "current_revenue": f"{business['currency']}{business['current_revenue']}",
                "revenue_goal": f"{business['currency']}{business['revenue_goal']}",
            },
            "performance_metrics": metrics,
            "active_opportunities": len([o for o in opportunities if o.get("status") == "active"]),
            "agent_health": {
                agent: {"status": health["status"], "last_error": health.get("last_error", "None")[:50]}
                for agent, health in self.knowledge_base["agent_health"].items()
            },
            "recommendations": self._generate_recommendations()
        }

        self.log_activity("Generated business report")

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate business recommendations"""
        recommendations = []
        metrics = self.knowledge_base["metrics"]
        business = self.knowledge_base["business_profile"]

        # Revenue recommendations
        if business["current_revenue"] < business["revenue_goal"] * 0.5:
            recommendations.append("Focus on client acquisition - revenue is below 50% of goal")

        # Lead recommendations
        if metrics["leads_generated"] > 20 and metrics["clients_acquired"] == 0:
            recommendations.append("High leads but no conversions - review outreach strategy")

        # Content recommendations
        if metrics["content_pieces"] < 7:
            recommendations.append("Increase content output - aim for 1 piece daily minimum")

        # Agent recommendations
        for agent, health in self.knowledge_base["agent_health"].items():
            if health.get("error_count", 0) > 3:
                recommendations.append(f"Review {agent} - multiple errors detected")

        return recommendations

    def _identify_opportunities(self) -> List[Dict]:
        """Identify business opportunities"""
        opportunities = [
            {
                "id": "opp_001",
                "type": "service_expansion",
                "title": "Add AI Consulting Service",
                "description": "High demand for AI strategy consulting",
                "potential_revenue": 15000,
                "effort": "Medium",
                "priority": "High"
            },
            {
                "id": "opp_002",
                "type": "partnership",
                "title": "Partner with Marketing Agencies",
                "description": "White-label AI automation for agencies",
                "potential_revenue": 25000,
                "effort": "Low",
                "priority": "High"
            },
            {
                "id": "opp_003",
                "type": "product",
                "title": "Launch Agency OS Template",
                "description": "Sell pre-built Agency OS on Gumroad",
                "potential_revenue": 5000,
                "effort": "Low",
                "priority": "Medium"
            },
            {
                "id": "opp_004",
                "type": "content",
                "title": "YouTube Channel for AI Tutorials",
                "description": "Build authority, drive leads through tutorials",
                "potential_revenue": 10000,
                "effort": "High",
                "priority": "Medium"
            }
        ]

        self.knowledge_base["opportunities"] = opportunities
        self._save_knowledge()

        self.log_activity("Identified opportunities", {"count": len(opportunities)})

        return opportunities

    def update_metric(self, metric_name: str, value: int, increment: bool = False):
        """Update business metrics"""
        if increment:
            current = self.knowledge_base["metrics"].get(metric_name, 0)
            self.knowledge_base["metrics"][metric_name] = current + value
        else:
            self.knowledge_base["metrics"][metric_name] = value

        self._save_knowledge()

    def update_revenue(self, amount: int):
        """Update revenue"""
        self.knowledge_base["business_profile"]["current_revenue"] += amount
        self._save_knowledge()
        self.log_activity("Revenue updated", {"amount": amount})

    def get_dashboard_data(self) -> Dict:
        """Get data for dashboard"""
        business = self.knowledge_base["business_profile"]
        metrics = self.knowledge_base["metrics"]
        revenue_progress = (business["current_revenue"] / business["revenue_goal"]) * 100

        return {
            "profile": {
                "name": self.profile.name,
                "avatar": self.profile.avatar,
                "role": self.profile.role.value,
                "expertise": self.profile.expertise[:5],
                "status": self.profile.status
            },
            "business_summary": {
                "company": business["name"],
                "founder": business["founder"],
                "revenue_progress": f"{revenue_progress:.1f}%",
                "current_revenue": f"{business['currency']}{business['current_revenue']:,}",
                "revenue_goal": f"{business['currency']}{business['revenue_goal']:,}",
            },
            "services": self.knowledge_base["services"],
            "metrics": metrics,
            "active_opportunities": len([o for o in self.knowledge_base.get("opportunities", []) if o.get("status") == "active"]),
            "agent_health_summary": {
                "healthy": len([a for a in self.knowledge_base["agent_health"].values() if a.get("status") == "healthy"]),
                "errors": len([a for a in self.knowledge_base["agent_health"].values() if a.get("status") == "error"])
            },
            "ideas_generated": self.profile.ideas_generated,
            "tasks_completed": self.profile.tasks_completed
        }

    def run_daily_business_review(self):
        """Run daily business review"""
        self.log_activity("Running daily business review")

        report = self._generate_business_report()
        opportunities = self._identify_opportunities()

        # Broadcast key insights
        self.broadcast_idea(
            f"Daily Business Review: {report['business_summary']['revenue_progress']} to revenue goal",
            {
                "metrics": report["performance_metrics"],
                "top_opportunity": opportunities[0] if opportunities else None,
                "recommendations": report["recommendations"][:3]
            }
        )


if __name__ == "__main__":
    from . import AgentCommunicationBus

    bus = AgentCommunicationBus()
    agent = BusinessIntelligenceAgent(bus)

    print("Business Intelligence Agent Profile:")
    print(json.dumps(agent.get_dashboard_data(), indent=2))
