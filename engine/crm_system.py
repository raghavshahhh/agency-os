#!/usr/bin/env python3
"""
RAGS Pro CRM System
Track clients, deals, and revenue
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
CRM_FILE = DATA_DIR / "crm_clients.json"
DEALS_FILE = DATA_DIR / "crm_deals.json"

class CRMSystem:
    """Simple CRM for tracking clients and deals"""

    def __init__(self):
        self.clients = self.load_clients()
        self.deals = self.load_deals()

    def load_clients(self) -> List[Dict]:
        """Load clients from file"""
        if CRM_FILE.exists():
            with open(CRM_FILE, 'r') as f:
                return json.load(f)
        return []

    def load_deals(self) -> List[Dict]:
        """Load deals from file"""
        if DEALS_FILE.exists():
            with open(DEALS_FILE, 'r') as f:
                return json.load(f)
        return []

    def save_clients(self):
        """Save clients to file"""
        CRM_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CRM_FILE, 'w') as f:
            json.dump(self.clients, f, indent=2)

    def save_deals(self):
        """Save deals to file"""
        DEALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DEALS_FILE, 'w') as f:
            json.dump(self.deals, f, indent=2)

    def add_client(self, name: str, email: str, phone: str = "", company: str = "",
                   source: str = "", tags: List[str] = None) -> Dict:
        """Add new client"""
        client = {
            "id": f"CLI_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "name": name,
            "email": email,
            "phone": phone,
            "company": company,
            "source": source,
            "tags": tags or [],
            "status": "lead",  # lead, prospect, client, churned
            "created_at": datetime.now().isoformat(),
            "last_contact": None,
            "notes": "",
        }
        self.clients.append(client)
        self.save_clients()
        return client

    def add_deal(self, client_id: str, title: str, value: int, service: str) -> Dict:
        """Add new deal"""
        deal = {
            "id": f"DEAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "client_id": client_id,
            "title": title,
            "value": value,
            "service": service,
            "status": "new",  # new, proposal_sent, negotiating, won, lost
            "stage": "lead",
            "probability": 20,  # %
            "created_at": datetime.now().isoformat(),
            "expected_close": (datetime.now() + timedelta(days=14)).isoformat(),
            "activities": [],
        }
        self.deals.append(deal)
        self.save_deals()
        return deal

    def update_deal_status(self, deal_id: str, status: str):
        """Update deal status"""
        for deal in self.deals:
            if deal["id"] == deal_id:
                deal["status"] = status
                deal["activities"].append({
                    "type": "status_change",
                    "from": deal.get("status"),
                    "to": status,
                    "at": datetime.now().isoformat(),
                })

                if status == "won":
                    deal["closed_at"] = datetime.now().isoformat()
                    # Update client status
                    client = self.get_client(deal["client_id"])
                    if client:
                        client["status"] = "client"

                self.save_deals()
                self.save_clients()
                return True
        return False

    def add_activity(self, deal_id: str, activity_type: str, note: str):
        """Add activity to deal"""
        for deal in self.deals:
            if deal["id"] == deal_id:
                deal["activities"].append({
                    "type": activity_type,
                    "note": note,
                    "at": datetime.now().isoformat(),
                })
                self.save_deals()
                return True
        return False

    def get_client(self, client_id: str) -> Optional[Dict]:
        """Get client by ID"""
        return next((c for c in self.clients if c["id"] == client_id), None)

    def get_deals_pipeline(self) -> Dict:
        """Get deals by pipeline stage"""
        stages = {
            "lead": [],
            "proposal_sent": [],
            "negotiating": [],
            "won": [],
            "lost": [],
        }
        for deal in self.deals:
            stage = deal.get("status", "lead")
            if stage in stages:
                stages[stage].append(deal)
        return stages

    def get_revenue_forecast(self) -> Dict:
        """Get revenue forecast"""
        total_pipeline = sum(d["value"] for d in self.deals if d["status"] != "won")
        weighted = sum(d["value"] * d.get("probability", 20) / 100
                      for d in self.deals if d["status"] != "won")
        won = sum(d["value"] for d in self.deals if d["status"] == "won")

        return {
            "total_pipeline": total_pipeline,
            "weighted_forecast": weighted,
            "won_revenue": won,
            "target": 50000,  # ₹50k/month
            "progress": (won / 50000) * 100,
        }

    def get_dashboard(self) -> Dict:
        """Get CRM dashboard data"""
        return {
            "total_clients": len(self.clients),
            "total_deals": len(self.deals),
            "pipeline": self.get_deals_pipeline(),
            "revenue": self.get_revenue_forecast(),
            "recent_deals": sorted(self.deals, key=lambda x: x["created_at"], reverse=True)[:5],
        }

    def generate_report(self) -> str:
        """Generate text report"""
        dash = self.get_dashboard()
        rev = dash["revenue"]

        report = f"""
🎯 RAGS PRO CRM REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📊 OVERVIEW
• Total Clients: {dash['total_clients']}
• Total Deals: {dash['total_deals']}

💰 REVENUE
• Won: ₹{rev['won_revenue']:,}
• Pipeline: ₹{rev['total_pipeline']:,}
• Weighted Forecast: ₹{rev['weighted_forecast']:,}
• Monthly Target: ₹{rev['target']:,}
• Progress: {rev['progress']:.1f}%

📈 PIPELINE
• Leads: {len(dash['pipeline']['lead'])}
• Proposal Sent: {len(dash['pipeline']['proposal_sent'])}
• Negotiating: {len(dash['pipeline']['negotiating'])}
• Won: {len(dash['pipeline']['won'])}
• Lost: {len(dash['pipeline']['lost'])}

🆕 RECENT DEALS
"""
        for deal in dash['recent_deals'][:3]:
            report += f"• {deal['title']} - ₹{deal['value']:,} ({deal['status']})\n"

        return report


if __name__ == "__main__":
    crm = CRMSystem()

    # Add test data
    client = crm.add_client(
        name="Test Client",
        email="test@example.com",
        phone="+91 98765 43210",
        company="TestCorp",
        source="Website"
    )

    deal = crm.add_deal(
        client_id=client["id"],
        title="AI Chatbot Project",
        value=25000,
        service="chatbot"
    )

    print(crm.generate_report())
