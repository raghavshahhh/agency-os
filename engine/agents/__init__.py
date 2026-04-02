#!/usr/bin/env python3
"""
RAGSPRO Expert Agent System
Multi-agent orchestration with specialized roles
Agents communicate, share ideas, and collaborate
"""

import json
import sys
import time
import traceback
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import queue

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import config with fallback
try:
    from config import DATA_DIR, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
except ImportError:
    # Fallback if dotenv not available
    BASE_DIR = Path(__file__).parent.parent.absolute()
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TELEGRAM_BOT_TOKEN = ""
    TELEGRAM_CHAT_ID = ""

AGENT_DATA_DIR = DATA_DIR / "agent_data"
AGENT_DATA_DIR.mkdir(parents=True, exist_ok=True)


class AgentRole(Enum):
    MARKETING = "marketing"
    CONTENT = "content"
    RESEARCH = "research"
    BUSINESS = "business"
    POSTING = "posting"
    SALES = "sales"


@dataclass
class AgentProfile:
    """Expert agent profile"""
    id: str
    name: str
    role: AgentRole
    avatar: str
    expertise: List[str]
    personality: str
    goals: List[str]
    status: str = "idle"
    last_activity: Optional[str] = None
    ideas_generated: int = 0
    tasks_completed: int = 0
    success_rate: float = 100.0


@dataclass
class Message:
    """Inter-agent message"""
    from_agent: str
    to_agent: str  # "broadcast" for all
    message_type: str  # "idea", "request", "response", "alert"
    content: str
    data: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ContentPiece:
    """Content for social media"""
    id: str
    platform: str  # instagram, linkedin, twitter, youtube
    content_type: str  # post, reel, carousel, story, video
    title: str
    caption: str
    hashtags: List[str]
    image_prompt: str
    scheduled_time: Optional[str] = None
    status: str = "draft"  # draft, approved, scheduled, posted, failed
    posted_url: Optional[str] = None
    metrics: Dict = field(default_factory=dict)


class AgentCommunicationBus:
    """Central communication system for agents"""

    def __init__(self):
        self.messages: List[Message] = []
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_file = AGENT_DATA_DIR / "agent_messages.json"

    def subscribe(self, agent_id: str, callback: Callable):
        """Subscribe to messages"""
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(callback)

    def send(self, message: Message):
        """Send message to agent(s)"""
        self.messages.append(message)
        self._save_message(message)

        # Notify subscribers
        if message.to_agent == "broadcast":
            for agent_id, callbacks in self.subscribers.items():
                if agent_id != message.from_agent:
                    for callback in callbacks:
                        try:
                            callback(message)
                        except Exception as e:
                            print(f"Error notifying {agent_id}: {e}")
        else:
            if message.to_agent in self.subscribers:
                for callback in self.subscribers[message.to_agent]:
                    try:
                        callback(message)
                    except Exception as e:
                        print(f"Error notifying {message.to_agent}: {e}")

    def _save_message(self, message: Message):
        """Save message to file"""
        messages = []
        if self.message_file.exists():
            with open(self.message_file) as f:
                messages = json.load(f)

        messages.append(asdict(message))

        # Keep last 1000 messages
        if len(messages) > 1000:
            messages = messages[-1000:]

        with open(self.message_file, 'w') as f:
            json.dump(messages, f, indent=2)

    def get_conversation(self, agent1: str, agent2: str, limit: int = 50) -> List[Message]:
        """Get conversation between two agents"""
        if not self.message_file.exists():
            return []

        with open(self.message_file) as f:
            messages = json.load(f)

        conversation = [
            m for m in messages
            if (m['from_agent'] == agent1 and m['to_agent'] == agent2) or
               (m['from_agent'] == agent2 and m['to_agent'] == agent1) or
               (m['from_agent'] in [agent1, agent2] and m['to_agent'] == 'broadcast')
        ]

        return conversation[-limit:]


class BaseExpertAgent:
    """Base class for all expert agents"""

    def __init__(self, profile: AgentProfile, comm_bus: AgentCommunicationBus):
        self.profile = profile
        self.comm_bus = comm_bus
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.task_queue: queue.Queue = queue.Queue()
        self.knowledge_base: Dict = {}
        self.ideas: List[Dict] = []

        # Subscribe to messages
        self.comm_bus.subscribe(profile.id, self._handle_message)

        # Load knowledge base
        self._load_knowledge()

    def _load_knowledge(self):
        """Load agent's knowledge base"""
        kb_file = AGENT_DATA_DIR / f"{self.profile.id}_knowledge.json"
        if kb_file.exists():
            with open(kb_file) as f:
                self.knowledge_base = json.load(f)

    def _save_knowledge(self):
        """Save agent's knowledge base"""
        kb_file = AGENT_DATA_DIR / f"{self.profile.id}_knowledge.json"
        with open(kb_file, 'w') as f:
            json.dump(self.knowledge_base, f, indent=2)

    def _handle_message(self, message: Message):
        """Handle incoming messages - override in subclasses"""
        pass

    def send_message(self, to_agent: str, content: str, msg_type: str = "message", data: Dict = None):
        """Send message to another agent"""
        msg = Message(
            from_agent=self.profile.id,
            to_agent=to_agent,
            message_type=msg_type,
            content=content,
            data=data or {}
        )
        self.comm_bus.send(msg)

    def broadcast_idea(self, idea: str, data: Dict = None):
        """Broadcast idea to all agents"""
        self.ideas.append({
            "idea": idea,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        })
        self.send_message("broadcast", idea, "idea", data)
        self.profile.ideas_generated += 1

    def log_activity(self, activity: str, data: Dict = None):
        """Log agent activity"""
        self.profile.last_activity = datetime.now().isoformat()

        activity_file = AGENT_DATA_DIR / f"{self.profile.id}_activities.json"
        activities = []
        if activity_file.exists():
            with open(activity_file) as f:
                activities = json.load(f)

        activities.append({
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
            "data": data or {}
        })

        # Keep last 500 activities
        if len(activities) > 500:
            activities = activities[-500:]

        with open(activity_file, 'w') as f:
            json.dump(activities, f, indent=2)

    def get_status(self) -> Dict:
        """Get agent status"""
        return {
            "profile": asdict(self.profile),
            "knowledge_keys": list(self.knowledge_base.keys()),
            "ideas_count": len(self.ideas),
            "running": self.running
        }

    def run_task(self, task_func: Callable, *args, **kwargs):
        """Run a task with error handling"""
        try:
            result = task_func(*args, **kwargs)
            self.profile.tasks_completed += 1
            return result
        except Exception as e:
            self.send_message(
                "business_agent",
                f"Error in {self.profile.name}: {str(e)}",
                "alert",
                {"error": str(e), "traceback": traceback.format_exc()}
            )
            raise


# Import specific agents
from .marketing_agent import MarketingAgent
from .content_agent import ContentCreationAgent
from .research_agent import MarketResearchAgent
from .business_agent import BusinessIntelligenceAgent
from .posting_agent import PostingAutomationAgent


class AgentOrchestrator:
    """
    Orchestrates all expert agents
    - Manages agent lifecycle
    - Coordinates inter-agent communication
    - Provides unified dashboard interface
    """

    def __init__(self):
        self.comm_bus = AgentCommunicationBus()
        self.agents: Dict[str, BaseExpertAgent] = {}
        self.running = False

    def initialize_agents(self):
        """Create and register all agents"""
        self.agents = {
            "marketing_agent": MarketingAgent(self.comm_bus),
            "content_agent": ContentCreationAgent(self.comm_bus),
            "research_agent": MarketResearchAgent(self.comm_bus),
            "business_agent": BusinessIntelligenceAgent(self.comm_bus),
            "posting_agent": PostingAutomationAgent(self.comm_bus),
        }

        # Initialize knowledge sharing
        self._broadcast_welcome()

    def _broadcast_welcome(self):
        """Welcome message to all agents"""
        welcome_msg = Message(
            from_agent="orchestrator",
            to_agent="broadcast",
            message_type="alert",
            content="🚀 Agent System Online! All agents connected. Let's grow RAGSPRO!",
            data={"event": "system_start", "agents": list(self.agents.keys())}
        )
        self.comm_bus.send(welcome_msg)

    def start(self):
        """Start the agent system"""
        self.running = True
        for agent_id, agent in self.agents.items():
            agent.profile.status = "active"
            print(f"✅ {agent_id} activated")

    def stop(self):
        """Stop all agents"""
        self.running = False
        for agent_id, agent in self.agents.items():
            agent.profile.status = "idle"

    def get_all_status(self) -> Dict:
        """Get status of all agents"""
        return {
            agent_id: {
                "name": agent.profile.name,
                "avatar": agent.profile.avatar,
                "role": agent.profile.role.value,
                "status": agent.profile.status,
                "ideas_generated": agent.profile.ideas_generated,
                "tasks_completed": agent.profile.tasks_completed,
                "expertise": agent.profile.expertise[:3]
            }
            for agent_id, agent in self.agents.items()
        }

    def get_dashboard_data(self) -> Dict:
        """Get unified dashboard data"""
        return {
            "agents": {
                agent_id: agent.get_dashboard_data()
                for agent_id, agent in self.agents.items()
            },
            "system_status": {
                "running": self.running,
                "total_agents": len(self.agents),
                "active_agents": len([a for a in self.agents.values() if a.profile.status == "active"])
            },
            "recent_messages": self.comm_bus.messages[-10:] if self.comm_bus.messages else []
        }

    def get_agent(self, agent_id: str) -> Optional[BaseExpertAgent]:
        """Get specific agent"""
        return self.agents.get(agent_id)

    def broadcast_task(self, task: str, data: Dict = None):
        """Broadcast task to all agents"""
        msg = Message(
            from_agent="orchestrator",
            to_agent="broadcast",
            message_type="request",
            content=task,
            data=data or {}
        )
        self.comm_bus.send(msg)


__all__ = [
    'AgentRole',
    'AgentProfile',
    'Message',
    'ContentPiece',
    'AgentCommunicationBus',
    'BaseExpertAgent',
    'MarketingAgent',
    'ContentCreationAgent',
    'MarketResearchAgent',
    'BusinessIntelligenceAgent',
    'PostingAutomationAgent',
    'AgentOrchestrator'
]
