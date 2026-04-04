"""
n8n Integration - Full API connector for n8n workflows
"""

import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os

DATA_DIR = Path(__file__).parent.parent / "data"

@dataclass
class Workflow:
    id: str
    name: str
    active: bool
    nodes: List[Dict]
    connections: Dict
    settings: Dict
    tags: List[str]
    created_at: str
    updated_at: str

class N8NIntegration:
    """n8n workflow automation integration"""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.getenv("N8N_BASE_URL", "http://localhost:5678")
        self.api_key = api_key or os.getenv("N8N_API_KEY", "")
        self.headers = {
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Any:
        """Make API request to n8n"""
        url = f"{self.base_url}/api/v1/{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 201:
                return response.json()
            else:
                print(f"n8n API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"n8n request error: {e}")
            return None

    # ─── WORKFLOW MANAGEMENT ─────────────────────────────────────────────────────

    def get_workflows(self) -> List[Workflow]:
        """Get all workflows"""
        result = self._make_request("GET", "workflows")
        if result and "data" in result:
            return [Workflow(**w) for w in result["data"]]
        return []

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID"""
        result = self._make_request("GET", f"workflows/{workflow_id}")
        if result:
            return Workflow(**result)
        return None

    def create_workflow(self, name: str, nodes: List[Dict], connections: Dict) -> Optional[Workflow]:
        """Create new workflow"""
        data = {
            "name": name,
            "nodes": nodes,
            "connections": connections,
            "settings": {"executionOrder": "v1"},
            "tags": []
        }

        result = self._make_request("POST", "workflows", data)
        if result:
            return Workflow(**result)
        return None

    def activate_workflow(self, workflow_id: str) -> bool:
        """Activate a workflow"""
        result = self._make_request("POST", f"workflows/{workflow_id}/activate")
        return result is not None

    def deactivate_workflow(self, workflow_id: str) -> bool:
        """Deactivate a workflow"""
        result = self._make_request("POST", f"workflows/{workflow_id}/deactivate")
        return result is not None

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        result = self._make_request("DELETE", f"workflows/{workflow_id}")
        return result is not None

    # ─── EXECUTION MANAGEMENT ────────────────────────────────────────────────────

    def get_executions(self, workflow_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get workflow executions"""
        params = f"?limit={limit}"
        if workflow_id:
            params += f"&workflowId={workflow_id}"

        result = self._make_request("GET", f"executions{params}")
        if result and "data" in result:
            return result["data"]
        return []

    def get_execution(self, execution_id: str) -> Optional[Dict]:
        """Get execution details"""
        return self._make_request("GET", f"executions/{execution_id}")

    def retry_execution(self, execution_id: str) -> Optional[Dict]:
        """Retry a failed execution"""
        return self._make_request("POST", f"executions/{execution_id}/retry")

    # ─── WEBHOOK HANDLING ───────────────────────────────────────────────────────

    def trigger_webhook(self, webhook_path: str, data: Dict) -> Optional[Dict]:
        """Trigger a webhook"""
        url = f"{self.base_url}/webhook/{webhook_path}"

        try:
            response = requests.post(
                url=url,
                json=data,
                timeout=30
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Webhook error: {e}")
            return None

    # ─── PRE-BUILT WORKFLOWS ───────────────────────────────────────────────────────

    def create_lead_scraper_workflow(self) -> Optional[Workflow]:
        """Create automated lead scraper workflow"""
        nodes = [
            {
                "id": "cron",
                "name": "Schedule Trigger",
                "type": "n8n-nodes-base.cron",
                "position": [250, 300],
                "parameters": {
                    "rule": {"interval": [{"field": "hours", "expression": "6"}]}
                }
            },
            {
                "id": "scrape",
                "name": "Scrape Leads",
                "type": "n8n-nodes-base.httpRequest",
                "position": [450, 300],
                "parameters": {
                    "method": "POST",
                    "url": "http://agency-os:8501/api/scrape",
                    "body": {"sources": ["reddit", "yc"]}
                }
            },
            {
                "id": "enrich",
                "name": "Enrich Leads",
                "type": "n8n-nodes-base.httpRequest",
                "position": [650, 300],
                "parameters": {
                    "method": "POST",
                    "url": "http://agency-os:8501/api/enrich"
                }
            },
            {
                "id": "notify",
                "name": "Send Notification",
                "type": "n8n-nodes-base.telegram",
                "position": [850, 300],
                "parameters": {
                    "chatId": "{{$env.TELEGRAM_CHAT_ID}}",
                    "text": "🎯 {{$json.new_leads}} new leads scraped!"
                }
            }
        ]

        connections = {
            "cron": {"main": [[{"node": "scrape", "type": "main", "index": 0}]]},
            "scrape": {"main": [[{"node": "enrich", "type": "main", "index": 0}]]},
            "enrich": {"main": [[{"node": "notify", "type": "main", "index": 0}]]}
        }

        return self.create_workflow("Auto Lead Scraper", nodes, connections)

    def create_outreach_sequence_workflow(self) -> Optional[Workflow]:
        """Create outreach automation workflow"""
        nodes = [
            {
                "id": "webhook",
                "name": "Outreach Webhook",
                "type": "n8n-nodes-base.webhook",
                "position": [250, 300],
                "parameters": {
                    "path": "outreach",
                    "responseMode": "responseNode"
                }
            },
            {
                "id": "score",
                "name": "Score Lead",
                "type": "n8n-nodes-base.httpRequest",
                "position": [450, 300],
                "parameters": {
                    "method": "POST",
                    "url": "http://agency-os:8501/api/score-lead"
                }
            },
            {
                "id": "condition",
                "name": "Hot Lead?",
                "type": "n8n-nodes-base.if",
                "position": [650, 300],
                "parameters": {
                    "conditions": {
                        "options": {
                            "caseSensitive": True,
                            "leftValue": "={{$json.score}}",
                            "operator": {
                                "type": "number",
                                "operation": "gt"
                            },
                            "rightValue": "75"
                        }
                    }
                }
            },
            {
                "id": "send_email",
                "name": "Send Cold Email",
                "type": "n8n-nodes-base.sendEmail",
                "position": [850, 200],
                "parameters": {
                    "to": "={{$json.email}}",
                    "subject": "Quick question about {{$json.company}}",
                    "html": "{{$json.email_body}}"
                }
            },
            {
                "id": "log",
                "name": "Log to CRM",
                "type": "n8n-nodes-base.httpRequest",
                "position": [850, 400],
                "parameters": {
                    "method": "POST",
                    "url": "http://agency-os:8501/api/log-outreach"
                }
            }
        ]

        connections = {
            "webhook": {"main": [[{"node": "score", "type": "main", "index": 0}]]},
            "score": {"main": [[{"node": "condition", "type": "main", "index": 0}]]},
            "condition": {
                "main": [
                    [{"node": "send_email", "type": "main", "index": 0}],
                    [{"node": "log", "type": "main", "index": 0}]
                ]
            },
            "send_email": {"main": [[{"node": "log", "type": "main", "index": 0}]]}
        }

        return self.create_workflow("Outreach Automation", nodes, connections)

    def create_data_sync_workflow(self) -> Optional[Workflow]:
        """Create data sync workflow"""
        nodes = [
            {
                "id": "cron",
                "name": "Daily Sync",
                "type": "n8n-nodes-base.cron",
                "position": [250, 300],
                "parameters": {
                    "rule": {"interval": [{"field": "hours", "expression": "24"}]}
                }
            },
            {
                "id": "backup",
                "name": "Backup Data",
                "type": "n8n-nodes-base.executeCommand",
                "position": [450, 300],
                "parameters": {
                    "command": "python3 /app/backup.py"
                }
            },
            {
                "id": "sync_crm",
                "name": "Sync to CRM",
                "type": "n8n-nodes-base.httpRequest",
                "position": [650, 300],
                "parameters": {
                    "method": "POST",
                    "url": "http://agency-os:8501/api/sync"
                }
            },
            {
                "id": "report",
                "name": "Send Report",
                "type": "n8n-nodes-base.telegram",
                "position": [850, 300],
                "parameters": {
                    "chatId": "{{$env.TELEGRAM_CHAT_ID}}",
                    "text": "✅ Daily sync complete!"
                }
            }
        ]

        connections = {
            "cron": {"main": [[{"node": "backup", "type": "main", "index": 0}]]},
            "backup": {"main": [[{"node": "sync_crm", "type": "main", "index": 0}]]},
            "sync_crm": {"main": [[{"node": "report", "type": "main", "index": 0}]]}
        }

        return self.create_workflow("Daily Data Sync", nodes, connections)

    # ─── AGENCY OS INTEGRATION ───────────────────────────────────────────────────

    def sync_leads_to_n8n(self, leads: List[Dict]) -> bool:
        """Sync leads to n8n for processing"""
        webhook_path = "agency-os/leads"
        return self.trigger_webhook(webhook_path, {"leads": leads}) is not None

    def trigger_proposal_generation(self, lead_id: str) -> bool:
        """Trigger proposal generation via n8n"""
        webhook_path = "agency-os/generate-proposal"
        return self.trigger_webhook(webhook_path, {"lead_id": lead_id}) is not None

    def notify_new_lead(self, lead: Dict) -> bool:
        """Send notification for new lead"""
        webhook_path = "agency-os/new-lead"
        return self.trigger_webhook(webhook_path, {"lead": lead}) is not None

    def notify_revenue(self, amount: float, client: str) -> bool:
        """Send revenue notification"""
        webhook_path = "agency-os/revenue"
        return self.trigger_webhook(webhook_path, {
            "amount": amount,
            "client": client,
            "currency": "INR"
        }) is not None

    # ─── STATUS & ANALYTICS ─────────────────────────────────────────────────────

    def get_health_status(self) -> Dict[str, Any]:
        """Get n8n health status"""
        try:
            response = requests.get(
                f"{self.base_url}/healthz",
                timeout=10
            )
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "code": response.status_code,
                "reachable": True
            }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "reachable": False
            }

    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow statistics"""
        workflows = self.get_workflows()
        executions = self.get_executions(limit=100)

        active_count = sum(1 for w in workflows if w.active)
        total_executions = len(executions)
        successful = sum(1 for e in executions if e.get("finished", False) and not e.get("stopped", False))
        failed = sum(1 for e in executions if e.get("stopped", False))

        return {
            "total_workflows": len(workflows),
            "active_workflows": active_count,
            "inactive_workflows": len(workflows) - active_count,
            "total_executions": total_executions,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": (successful / total_executions * 100) if total_executions > 0 else 0
        }


# Global instance - requires N8N_BASE_URL and N8N_API_KEY env vars
n8n = N8NIntegration()
