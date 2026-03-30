#!/usr/bin/env python3
"""
RAGSPRO n8n Connector — Trigger workflows for automation
"""

import json
import requests
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config import N8N_API_KEY, N8N_URL, DATA_DIR

N8N_WORKFLOWS_FILE = DATA_DIR / "n8n_workflows.json"


def trigger_workflow(webhook_url, payload):
    """Trigger an n8n workflow via webhook"""
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        return {
            "success": response.status_code in [200, 201, 202],
            "status_code": response.status_code,
            "response": response.json() if response.content else {}
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def trigger_lead_gen_workflow(lead_data):
    """Trigger lead generation workflow"""
    webhook_url = f"{N8N_URL}/webhook/lead-gen"
    return trigger_workflow(webhook_url, {
        "lead": lead_data,
        "timestamp": datetime.now().isoformat(),
        "source": "agency_os"
    })


def trigger_content_workflow(content_data):
    """Trigger content creation workflow"""
    webhook_url = f"{N8N_URL}/webhook/content"
    return trigger_workflow(webhook_url, {
        "content": content_data,
        "timestamp": datetime.now().isoformat(),
        "source": "agency_os"
    })


def trigger_outreach_workflow(lead_id, outreach_type, content):
    """Trigger outreach workflow"""
    webhook_url = f"{N8N_URL}/webhook/outreach"
    return trigger_workflow(webhook_url, {
        "lead_id": lead_id,
        "type": outreach_type,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })


def test_connection():
    """Test n8n connection"""
    print("🔌 Testing n8n connection...")
    print(f"   URL: {N8N_URL}")
    print(f"   API Key: {'✅ Set' if N8N_API_KEY else '❌ Missing'}")

    try:
        response = requests.get(
            f"{N8N_URL}/healthz",
            timeout=5
        )
        if response.status_code == 200:
            print("✅ n8n is reachable")
            return True
        else:
            print(f"⚠️ n8n returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to n8n: {e}")
        print("\n💡 Make sure n8n is running:")
        print("   npx n8n start")
        print("   or")
        print("   docker run -it --rm -p 5678:5678 n8nio/n8n")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("🔗 RAGSPRO n8n Connector")
    print("=" * 50)

    test_connection()

    print("\n📋 Available workflows:")
    print("   1. Lead Generation — /webhook/lead-gen")
    print("   2. Content Creation — /webhook/content")
    print("   3. Outreach Automation — /webhook/outreach")

    print("\n💡 To enable:")
    print("   1. Start n8n: npx n8n start")
    print("   2. Import workflows from workflows/ folder")
    print("   3. Activate webhooks in n8n")
    print("   4. Update webhook URLs in this file")
