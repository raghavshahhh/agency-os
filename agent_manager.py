#!/usr/bin/env python3
"""
RAGSPRO Agent Manager
Start/stop/monitor all self-monitoring agents
"""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "engine"))

from agent_system import LeadGenerationAgent, ContentCreationAgent, OutreachAutomationAgent


class AgentManager:
    """Manages all agents"""

    def __init__(self):
        self.agents = {
            "leads": LeadGenerationAgent(),
            "content": ContentCreationAgent(),
            "outreach": OutreachAutomationAgent()
        }

    def start_all(self):
        """Start all agents"""
        print("=" * 60)
        print("🚀 RAGSPRO Agent Manager - Starting All Agents")
        print("=" * 60)

        for name, agent in self.agents.items():
            print(f"\n▶️  Starting {name} agent...")
            agent.start()
            time.sleep(1)  # Stagger starts

        print("\n✅ All agents started!")
        print("\nAgents running:")
        print("  • LeadGenerationAgent - Scrapes Reddit/GMaps every 4h")
        print("  • ContentCreationAgent - Generates content daily")
        print("  • OutreachAutomationAgent - Email sequences automated")
        print("\nPress Ctrl+C to stop all agents")

        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping all agents...")
            self.stop_all()

    def stop_all(self):
        """Stop all agents"""
        for name, agent in self.agents.items():
            print(f"  Stopping {name}...")
            agent.stop()
        print("✅ All agents stopped")

    def status(self):
        """Get status of all agents"""
        print("=" * 60)
        print("📊 Agent Status")
        print("=" * 60)

        for name, agent in self.agents.items():
            status = agent.get_status()
            print(f"\n🔹 {status['name']}")
            print(f"   Status: {status['status'].upper()}")
            print(f"   Running: {status['running']}")
            print(f"   Tasks: {len(status['tasks'])}")

            for task in status['tasks']:
                print(f"   • {task['name']}: {task['status']} (success: {task['success']}, errors: {task['errors']})")

    def logs(self, agent_name: str = None, lines: int = 50):
        """View agent logs"""
        from agent_system import AGENT_LOG_FILE
        import json

        if not AGENT_LOG_FILE.exists():
            print("No logs found")
            return

        with open(AGENT_LOG_FILE) as f:
            logs = json.load(f)

        if agent_name:
            logs = [l for l in logs if l.get("agent") == agent_name]

        logs = logs[-lines:]

        print("=" * 60)
        print(f"📜 Last {len(logs)} Log Entries")
        if agent_name:
            print(f"   Filtered by: {agent_name}")
        print("=" * 60)

        for log in logs:
            print(f"\n[{log['timestamp']}] {log['agent']} - {log['level'].upper()}")
            print(f"  {log['message']}")


def main():
    parser = argparse.ArgumentParser(description="RAGSPRO Agent Manager")
    parser.add_argument("command", choices=["start", "stop", "status", "logs"],
                       help="Command to run")
    parser.add_argument("--agent", help="Specific agent for logs command")

    args = parser.parse_args()

    manager = AgentManager()

    if args.command == "start":
        manager.start_all()
    elif args.command == "stop":
        manager.stop_all()
    elif args.command == "status":
        manager.status()
    elif args.command == "logs":
        manager.logs(args.agent)


if __name__ == "__main__":
    main()
