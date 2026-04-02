#!/usr/bin/env python3
"""
RAGSPRO Agent System - Self-Monitoring, Self-Healing AI Agents
Each agent runs in continuous loops, monitors itself, reports errors
Integrates with existing Agency OS modules
"""

import json
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

AGENT_LOG_FILE = DATA_DIR / "agent_system_logs.json"
AGENT_STATE_FILE = DATA_DIR / "agent_states.json"


class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    RECOVERING = "recovering"
    STOPPED = "stopped"


@dataclass
class AgentTask:
    """Single task for an agent"""
    id: str
    name: str
    func: Callable
    interval_minutes: int
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    success_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    status: str = "pending"


class BaseAgent:
    """Base class for all self-monitoring agents"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.tasks: List[AgentTask] = []
        self.logs: List[Dict] = []
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self._ensure_files()

    def _ensure_files(self):
        """Ensure state files exist"""
        AGENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not AGENT_STATE_FILE.exists():
            self._save_state()

    def _load_state(self) -> Dict:
        """Load agent state from file"""
        if AGENT_STATE_FILE.exists():
            with open(AGENT_STATE_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_state(self):
        """Save agent state to file"""
        state = self._load_state()
        state[self.name] = {
            "status": self.status.value,
            "last_update": datetime.now().isoformat(),
            "task_count": len(self.tasks),
            "total_runs": sum(t.success_count for t in self.tasks),
            "total_errors": sum(t.error_count for t in self.tasks)
        }
        with open(AGENT_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)

    def log(self, message: str, level: str = "info", data: Dict = None):
        """Log agent activity"""
        entry = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "data": data or {}
        }
        self.logs.append(entry)

        # Keep only last 1000 logs per agent
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]

        # Save to file
        self._save_log(entry)

        # Print for debugging
        print(f"[{self.name}] {level.upper()}: {message}")

    def _save_log(self, entry: Dict):
        """Save log to file"""
        logs = []
        if AGENT_LOG_FILE.exists():
            try:
                with open(AGENT_LOG_FILE, 'r') as f:
                    logs = json.load(f)
            except:
                pass

        logs.append(entry)

        # Keep only last 5000 logs total
        if len(logs) > 5000:
            logs = logs[-5000:]

        with open(AGENT_LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)

    def send_alert(self, message: str, priority: str = "normal"):
        """Send alert via Telegram"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            self.log("Telegram not configured, can't send alert", "warning")
            return

        try:
            import requests

            emoji = {"critical": "🚨", "high": "⚠️", "normal": "ℹ️"}.get(priority, "ℹ️")

            text = f"""{emoji} <b>Agent Alert: {self.name}</b>

{message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {self.status.value}
"""

            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML"
            }, timeout=10)

        except Exception as e:
            self.log(f"Failed to send Telegram alert: {e}", "error")

    def add_task(self, task_id: str, name: str, func: Callable, interval_minutes: int):
        """Add a task to this agent"""
        task = AgentTask(
            id=task_id,
            name=name,
            func=func,
            interval_minutes=interval_minutes,
            next_run=(datetime.now() + timedelta(minutes=interval_minutes)).isoformat()
        )
        self.tasks.append(task)
        self.log(f"Task added: {name} (every {interval_minutes} min)")

    def _execute_task(self, task: AgentTask):
        """Execute a single task with error handling"""
        try:
            self.log(f"Executing task: {task.name}")
            task.status = "running"

            # Execute the task
            result = task.func()

            # Update task stats
            task.success_count += 1
            task.last_run = datetime.now().isoformat()
            task.next_run = (datetime.now() + timedelta(minutes=task.interval_minutes)).isoformat()
            task.status = "completed"
            task.last_error = None

            self.log(f"Task completed: {task.name}", "success", {"result": str(result)[:100]})

        except Exception as e:
            task.error_count += 1
            task.status = "error"
            task.last_error = str(e)

            error_msg = f"Task {task.name} failed: {str(e)}\n{traceback.format_exc()[:500]}"
            self.log(error_msg, "error")

            # Send alert if multiple consecutive errors
            if task.error_count >= 3:
                self.send_alert(
                    f"Task '{task.name}' failed {task.error_count} times.\nLast error: {str(e)[:200]}",
                    priority="high" if task.error_count >= 5 else "normal"
                )

    def _run_loop(self):
        """Main agent loop"""
        self.running = True
        self.status = AgentStatus.RUNNING
        self.log("Agent loop started")

        while self.running:
            try:
                now = datetime.now()

                for task in self.tasks:
                    # Check if task should run
                    if task.next_run:
                        next_run = datetime.fromisoformat(task.next_run)
                        if now >= next_run:
                            self._execute_task(task)
                    else:
                        # First run
                        self._execute_task(task)

                # Save state periodically
                self._save_state()

                # Sleep for 1 minute
                time.sleep(60)

            except Exception as e:
                self.log(f"Agent loop error: {e}", "critical")
                self.status = AgentStatus.ERROR
                self.send_alert(f"Agent loop crashed: {str(e)[:200]}", priority="critical")
                time.sleep(300)  # Wait 5 minutes before retrying
                self.status = AgentStatus.RECOVERING

        self.status = AgentStatus.STOPPED
        self.log("Agent loop stopped")

    def start(self):
        """Start the agent in a background thread"""
        if self.thread and self.thread.is_alive():
            self.log("Agent already running")
            return

        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.log("Agent started")

    def stop(self):
        """Stop the agent"""
        self.running = False
        self.log("Agent stopping...")

    def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "running": self.running,
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "interval": t.interval_minutes,
                    "last_run": t.last_run,
                    "next_run": t.next_run,
                    "success": t.success_count,
                    "errors": t.error_count,
                    "status": t.status
                }
                for t in self.tasks
            ],
            "recent_logs": self.logs[-10:]
        }


# Import specific agents
from .lead_agent import LeadGenerationAgent
from .content_agent import ContentCreationAgent
from .outreach_agent import OutreachAutomationAgent

__all__ = [
    'BaseAgent',
    'AgentStatus',
    'LeadGenerationAgent',
    'ContentCreationAgent',
    'OutreachAutomationAgent'
]
