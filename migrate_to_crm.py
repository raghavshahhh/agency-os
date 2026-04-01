#!/usr/bin/env python3
"""
Migration script: Old JSON format → New CRM System
Run once to migrate existing data
"""

import json
from pathlib import Path
from datetime import datetime

# Paths
DATA_DIR = Path(__file__).parent / "data"
OLD_CLIENTS_FILE = DATA_DIR / "clients.json"
OLD_PIPELINE_FILE = DATA_DIR / "pipeline.json"
NEW_CRM_CLIENTS_FILE = DATA_DIR / "crm_clients.json"
NEW_CRM_DEALS_FILE = DATA_DIR / "crm_deals.json"


def migrate_clients():
    """Migrate old clients.json to crm_clients.json"""
    if not OLD_CLIENTS_FILE.exists():
        print("No old clients.json found")
        return []

    with open(OLD_CLIENTS_FILE, 'r') as f:
        old_clients = json.load(f)

    new_clients = []
    for old in old_clients:
        # Map old fields to new CRM format
        client = {
            "id": old.get("id", f"CLI_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "name": old.get("name", ""),
            "email": old.get("email", ""),
            "phone": old.get("phone", ""),
            "company": old.get("company", ""),
            "source": old.get("source", "Unknown"),
            "tags": old.get("tags", []),
            "status": old.get("status", "lead").lower(),
            "created_at": old.get("created_at", datetime.now().isoformat()),
            "last_contact": old.get("last_contact", None),
            "notes": old.get("notes", "")
        }

        # Handle projects from old format
        if "projects" in old:
            for proj in old["projects"]:
                # Will create deals separately
                pass

        new_clients.append(client)
        print(f"  ✓ Migrated client: {client['name']}")

    return new_clients


def migrate_pipeline():
    """Migrate old pipeline.json to crm_deals.json"""
    if not OLD_PIPELINE_FILE.exists():
        print("No old pipeline.json found")
        return []

    with open(OLD_PIPELINE_FILE, 'r') as f:
        old_pipeline = json.load(f)

    new_deals = []
    for old in old_pipeline:
        # Map pipeline stages to deal statuses
        stage_map = {
            "NEW": "new",
            "CONTACTED": "new",
            "REPLIED": "proposal_sent",
            "PROPOSAL_SENT": "proposal_sent",
            "CLOSED": "won"
        }

        deal = {
            "id": old.get("id", f"DEAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "client_id": old.get("client_id", ""),
            "title": old.get("name", old.get("title", "Untitled Deal")),
            "value": old.get("value", 0),
            "service": old.get("service", "general"),
            "status": stage_map.get(old.get("stage", "NEW"), "new"),
            "stage": old.get("stage", "NEW").lower(),
            "probability": 20 if old.get("stage") == "NEW" else 50 if old.get("stage") == "CONTACTED" else 80 if old.get("stage") == "PROPOSAL_SENT" else 100,
            "created_at": old.get("created_at", datetime.now().isoformat()),
            "expected_close": old.get("expected_close", (datetime.now().isoformat())),
            "activities": old.get("activities", [])
        }

        new_deals.append(deal)
        print(f"  ✓ Migrated deal: {deal['title']} (₹{deal['value']:,})")

    return new_deals


def save_new_crm(clients, deals):
    """Save migrated data to new CRM files"""
    # Save clients
    with open(NEW_CRM_CLIENTS_FILE, 'w') as f:
        json.dump(clients, f, indent=2)
    print(f"\n✅ Saved {len(clients)} clients to crm_clients.json")

    # Save deals
    with open(NEW_CRM_DEALS_FILE, 'w') as f:
        json.dump(deals, f, indent=2)
    print(f"✅ Saved {len(deals)} deals to crm_deals.json")


def main():
    print("=" * 50)
    print("🔄 MIGRATING TO NEW CRM SYSTEM")
    print("=" * 50)

    # Migrate clients
    print("\n📋 Migrating clients...")
    clients = migrate_clients()

    # Migrate pipeline
    print("\n💼 Migrating pipeline deals...")
    deals = migrate_pipeline()

    # Save
    save_new_crm(clients, deals)

    print("\n" + "=" * 50)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 50)
    print(f"\n📊 Summary:")
    print(f"  • Clients: {len(clients)}")
    print(f"  • Deals: {len(deals)}")
    print(f"\nNext steps:")
    print(f"  1. Update pages to use CRMSystem class")
    print(f"  2. Test the new pages")
    print(f"  3. Optional: Backup old files")


if __name__ == "__main__":
    main()
