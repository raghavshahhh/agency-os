"""
Automated Outreach Sequences - Multi-step email sequences with triggers
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import time

DATA_DIR = Path(__file__).parent.parent / "data"
SEQUENCES_FILE = DATA_DIR / "outreach_sequences.json"
TEMPLATES_FILE = DATA_DIR / "email_templates.json"

class SequenceStepType(Enum):
    EMAIL = "email"
    WAIT = "wait"
    CONDITION = "condition"
    TASK = "task"
    WEBHOOK = "webhook"

class SequenceStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class SequenceStep:
    id: str
    name: str
    step_type: str  # email, wait, condition, task
    config: Dict[str, Any]  # Step-specific config
    order: int
    delay_days: int  # Days after previous step
    condition: Optional[str]  # Condition for conditional steps

@dataclass
class OutreachSequence:
    id: str
    name: str
    description: str
    target_segment: str  # hot/warm/cold/all
    steps: List[SequenceStep]
    status: str
    created_at: str
    updated_at: str
    stats: Dict[str, Any]

@dataclass
class SequenceEnrollment:
    id: str
    sequence_id: str
    lead_id: str
    current_step: int
    status: str
    started_at: str
    completed_at: Optional[str]
    next_step_at: Optional[str]
    step_history: List[Dict[str, Any]]

class AutomatedOutreachEngine:
    """Multi-step automated outreach sequence engine"""

    def __init__(self, email_sender: Optional[Callable] = None):
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.email_sender = email_sender or self._default_email_sender
        self._init_files()

    def _init_files(self):
        """Initialize data files"""
        if not SEQUENCES_FILE.exists():
            self._save_sequences({})

        enrollments_file = self.data_dir / "sequence_enrollments.json"
        if not enrollments_file.exists():
            with open(enrollments_file, 'w') as f:
                json.dump({}, f)

    def _load_sequences(self) -> Dict:
        """Load all sequences"""
        if SEQUENCES_FILE.exists():
            with open(SEQUENCES_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_sequences(self, sequences: Dict):
        """Save sequences"""
        with open(SEQUENCES_FILE, 'w') as f:
            json.dump(sequences, f, indent=2, default=str)

    def _load_enrollments(self) -> Dict:
        """Load enrollments"""
        enrollments_file = self.data_dir / "sequence_enrollments.json"
        if enrollments_file.exists():
            with open(enrollments_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_enrollments(self, enrollments: Dict):
        """Save enrollments"""
        enrollments_file = self.data_dir / "sequence_enrollments.json"
        with open(enrollments_file, 'w') as f:
            json.dump(enrollments, f, indent=2, default=str)

    def _load_leads(self) -> List[Dict]:
        """Load leads"""
        leads_file = self.data_dir / "leads.json"
        if leads_file.exists():
            with open(leads_file, 'r') as f:
                return json.load(f)
        return []

    def _save_leads(self, leads: List[Dict]):
        """Save leads"""
        leads_file = self.data_dir / "leads.json"
        with open(leads_file, 'w') as f:
            json.dump(leads, f, indent=2, default=str)

    # ─── SEQUENCE MANAGEMENT ─────────────────────────────────────────────────────

    def create_sequence(self, name: str, description: str, target_segment: str = "all") -> OutreachSequence:
        """Create new outreach sequence"""
        seq_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        sequence = OutreachSequence(
            id=seq_id,
            name=name,
            description=description,
            target_segment=target_segment,
            steps=[],
            status=SequenceStatus.ACTIVE.value,
            created_at=now,
            updated_at=now,
            stats={"enrolled": 0, "completed": 0, "converted": 0}
        )

        sequences = self._load_sequences()
        sequences[seq_id] = asdict(sequence)
        self._save_sequences(sequences)

        return sequence

    def add_step(self, sequence_id: str, name: str, step_type: str,
                 config: Dict, delay_days: int = 1, condition: Optional[str] = None) -> SequenceStep:
        """Add step to sequence"""
        sequences = self._load_sequences()

        if sequence_id not in sequences:
            raise ValueError(f"Sequence {sequence_id} not found")

        seq = sequences[sequence_id]
        step_id = str(uuid.uuid4())[:8]
        order = len(seq.get("steps", []))

        step = SequenceStep(
            id=step_id,
            name=name,
            step_type=step_type,
            config=config,
            order=order,
            delay_days=delay_days,
            condition=condition
        )

        if "steps" not in seq:
            seq["steps"] = []

        seq["steps"].append(asdict(step))
        seq["updated_at"] = datetime.now().isoformat()

        self._save_sequences(sequences)
        return step

    def get_sequence(self, sequence_id: str) -> Optional[OutreachSequence]:
        """Get sequence by ID"""
        sequences = self._load_sequences()
        if sequence_id in sequences:
            data = sequences[sequence_id]
            return OutreachSequence(**data)
        return None

    def get_sequences(self) -> List[OutreachSequence]:
        """Get all sequences"""
        sequences = self._load_sequences()
        return [OutreachSequence(**data) for data in sequences.values()]

    # ─── ENROLLMENT & EXECUTION ───────────────────────────────────────────────────

    def enroll_lead(self, sequence_id: str, lead_id: str) -> SequenceEnrollment:
        """Enroll a lead in a sequence"""
        enrollment_id = f"{sequence_id}_{lead_id}"
        now = datetime.now().isoformat()

        enrollment = SequenceEnrollment(
            id=enrollment_id,
            sequence_id=sequence_id,
            lead_id=lead_id,
            current_step=0,
            status="active",
            started_at=now,
            completed_at=None,
            next_step_at=now,  # Start immediately
            step_history=[]
        )

        enrollments = self._load_enrollments()
        enrollments[enrollment_id] = asdict(enrollment)
        self._save_enrollments(enrollments)

        # Update sequence stats
        sequences = self._load_sequences()
        if sequence_id in sequences:
            seq = sequences[sequence_id]
            seq["stats"]["enrolled"] = seq["stats"].get("enrolled", 0) + 1
            self._save_sequences(sequences)

        return enrollment

    def enroll_batch(self, sequence_id: str, lead_ids: List[str]) -> List[SequenceEnrollment]:
        """Enroll multiple leads"""
        enrollments = []
        for lead_id in lead_ids:
            try:
                enrollment = self.enroll_lead(sequence_id, lead_id)
                enrollments.append(enrollment)
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Error enrolling {lead_id}: {e}")
        return enrollments

    def process_enrollments(self) -> Dict[str, int]:
        """Process all active enrollments - call this periodically"""
        enrollments = self._load_enrollments()
        sequences = self._load_sequences()
        leads = self._load_leads()

        processed = {"emails_sent": 0, "steps_advanced": 0, "completed": 0}
        now = datetime.now()

        for enrollment_id, enrollment in enrollments.items():
            if enrollment["status"] != "active":
                continue

            # Check if it's time for next step
            next_step_at = enrollment.get("next_step_at")
            if next_step_at:
                next_time = datetime.fromisoformat(next_step_at)
                if now < next_time:
                    continue

            sequence_id = enrollment["sequence_id"]
            if sequence_id not in sequences:
                continue

            sequence = sequences[sequence_id]
            current_step_idx = enrollment["current_step"]
            steps = sequence.get("steps", [])

            if current_step_idx >= len(steps):
                # Sequence completed
                enrollment["status"] = "completed"
                enrollment["completed_at"] = now.isoformat()
                processed["completed"] += 1
                continue

            # Process current step
            step = steps[current_step_idx]
            lead_id = enrollment["lead_id"]

            # Find lead data
            lead = next((l for l in leads if l.get("id") == lead_id), None)
            if not lead:
                enrollment["status"] = "cancelled"
                continue

            # Execute step
            success = self._execute_step(step, lead, enrollment)

            if success:
                processed["steps_advanced"] += 1
                if step.get("step_type") == "email":
                    processed["emails_sent"] += 1

                # Advance to next step
                enrollment["current_step"] = current_step_idx + 1
                enrollment["step_history"].append({
                    "step": step["name"],
                    "executed_at": now.isoformat(),
                    "success": success
                })

                # Schedule next step
                next_step_idx = current_step_idx + 1
                if next_step_idx < len(steps):
                    next_step = steps[next_step_idx]
                    delay_days = next_step.get("delay_days", 1)
                    enrollment["next_step_at"] = (now + timedelta(days=delay_days)).isoformat()
                else:
                    enrollment["next_step_at"] = None

        self._save_enrollments(enrollments)
        return processed

    def _execute_step(self, step: Dict, lead: Dict, enrollment: Dict) -> bool:
        """Execute a single step"""
        step_type = step.get("step_type")
        config = step.get("config", {})

        if step_type == "email":
            return self._send_sequence_email(step, lead, enrollment)
        elif step_type == "wait":
            return True  # Wait steps just pass through
        elif step_type == "webhook":
            return self._trigger_webhook(config, lead)
        elif step_type == "task":
            return self._create_task(config, lead)

        return False

    def _send_sequence_email(self, step: Dict, lead: Dict, enrollment: Dict) -> bool:
        """Send email for sequence step"""
        config = step.get("config", {})
        template = config.get("template", "")
        subject = config.get("subject", "Following up")

        # Get lead email
        email = self._get_email_for_lead(lead)
        if not email:
            return False

        # Personalize template
        personalized = self._personalize_template(template, lead)

        # Send email
        success, error = self.email_sender(email, subject, personalized)

        # Log the outreach
        if "outreach_log" not in lead:
            lead["outreach_log"] = []

        lead["outreach_log"].append({
            "step": step.get("name"),
            "sent_at": datetime.now().isoformat(),
            "status": "sent" if success else "failed",
            "error": error
        })

        # Update lead status based on step
        step_name = step.get("name", "").lower()
        if "initial" in step_name:
            lead["status"] = "CONTACTED"
        elif "follow" in step_name:
            lead["status"] = "FOLLOWED_UP"

        self._save_leads(self._load_leads())

        return success

    def _get_email_for_lead(self, lead: Dict) -> Optional[str]:
        """Extract email from lead"""
        contact = lead.get("contact", {})
        emails = contact.get("emails", [])
        if emails:
            return emails[0]
        return lead.get("email")

    def _personalize_template(self, template: str, lead: Dict) -> str:
        """Personalize email template"""
        contact = lead.get("contact", {})

        # Extract name from various sources
        name = lead.get("name", "")
        if not name and contact.get("reddit_user"):
            name = contact["reddit_user"].replace("u/", "").title()

        # Extract company from title
        company = ""
        title = lead.get("title", "")
        if " at " in title:
            company = title.split(" at ")[-1].split("(")[0].strip()

        # Replace placeholders
        personalized = template
        personalized = personalized.replace("{{name}}", name or "there")
        personalized = personalized.replace("{{company}}", company or "your company")
        personalized = personalized.replace("{{title}}", title or "your project")

        return personalized

    def _trigger_webhook(self, config: Dict, lead: Dict) -> bool:
        """Trigger webhook"""
        import requests

        url = config.get("url", "")
        if not url:
            return False

        try:
            response = requests.post(url, json={"lead": lead}, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Webhook error: {e}")
            return False

    def _create_task(self, config: Dict, lead: Dict) -> bool:
        """Create a task in task manager"""
        # This would integrate with task_manager
        # For now, just log it
        print(f"Would create task: {config.get('title', '')} for lead {lead.get('id')}")
        return True

    def _default_email_sender(self, to: str, subject: str, body: str) -> tuple:
        """Default email sender (mock)"""
        # This would integrate with actual email service
        # For now, just log
        print(f"[MOCK EMAIL] To: {to}\nSubject: {subject}\n{body[:100]}...")
        return True, None

    # ─── SEQUENCE TEMPLATES ─────────────────────────────────────────────────────────

    def create_default_sequences(self):
        """Create default outreach sequences"""

        # Hot leads sequence (fast track)
        hot_seq = self.create_sequence(
            name="🔥 Hot Leads - Fast Track",
            description="Aggressive 5-day sequence for hot leads",
            target_segment="hot"
        )

        self.add_step(
            sequence_id=hot_seq.id,
            name="Initial Outreach",
            step_type="email",
            config={
                "template": """Hi {{name}},

I saw your post about {{title}} and I'm excited about what you're building!

I'm Raghav from RAGSPRO - we specialize in AI-powered development and have helped similar companies launch faster.

Quick question: Are you open to a 15-min chat this week to see if we can help?

Best,
Raghav
RAGSPRO - AI Development Agency""",
                "subject": "Quick question about {{title}}"
            },
            delay_days=0
        )

        self.add_step(
            sequence_id=hot_seq.id,
            name="Follow-up #1",
            step_type="email",
            config={
                "template": """Hi {{name}},

Just following up on my previous email about helping with {{title}}.

We've recently helped a similar company reduce development time by 60% using AI automation.

Worth a quick conversation?

Raghav""",
                "subject": "Re: Quick question about {{title}}"
            },
            delay_days=2
        )

        self.add_step(
            sequence_id=hot_seq.id,
            name="Final Follow-up",
            step_type="email",
            config={
                "template": """Hi {{name}},

Last follow-up from me!

If {{title}} is still a priority, I'd love to show you how we can help. If not, no worries - I'll stop following up.

Either way, best of luck!

Raghav""",
                "subject": "Last follow-up: {{title}}"
            },
            delay_days=3
        )

        # Warm leads sequence
        warm_seq = self.create_sequence(
            name="🌤️ Warm Leads - Nurture",
            description="Gentle 14-day nurture sequence",
            target_segment="warm"
        )

        self.add_step(
            sequence_id=warm_seq.id,
            name="Value-First Email",
            step_type="email",
            config={
                "template": """Hi {{name}},

I noticed you're working on {{title}} - interesting space!

I wrote a quick guide on "5 AI Tools That Cut Development Time in Half" that might be useful:

[Link to resource]

Hope it helps!

Raghav""",
                "subject": "Resource: 5 AI tools for {{title}}"
            },
            delay_days=0
        )

        self.add_step(
            sequence_id=warm_seq.id,
            name="Soft Pitch",
            step_type="email",
            config={
                "template": """Hi {{name}},

Hope you found the guide useful!

If you're looking for help implementing any of those tools for {{title}}, my team at RAGSPRO specializes in exactly this.

We offer a free 30-min consultation - interested?

Raghav""",
                "subject": "Quick question about {{title}}"
            },
            delay_days=5
        )

        self.add_step(
            sequence_id=warm_seq.id,
            name="Final Follow-up",
            step_type="email",
            config={
                "template": """Hi {{name}},

Last email from me - I promise!

If you're not ready to chat now, totally fine. Feel free to reach out whenever {{title}} becomes a priority.

Good luck with the project!

Raghav""",
                "subject": "Last email: {{title}}"
            },
            delay_days=7
        )

        return [hot_seq, warm_seq]

    # ─── ANALYTICS ───────────────────────────────────────────────────────────────

    def get_sequence_stats(self, sequence_id: str) -> Dict[str, Any]:
        """Get sequence performance stats"""
        enrollments = self._load_enrollments()

        seq_enrollments = [
            e for e in enrollments.values()
            if e["sequence_id"] == sequence_id
        ]

        total = len(seq_enrollments)
        active = len([e for e in seq_enrollments if e["status"] == "active"])
        completed = len([e for e in seq_enrollments if e["status"] == "completed"])
        cancelled = len([e for e in seq_enrollments if e["status"] == "cancelled"])

        # Calculate completion rate
        completion_rate = (completed / total * 100) if total > 0 else 0

        return {
            "total_enrolled": total,
            "active": active,
            "completed": completed,
            "cancelled": cancelled,
            "completion_rate": round(completion_rate, 1)
        }

    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall outreach stats"""
        sequences = self._load_sequences()
        enrollments = self._load_enrollments()

        return {
            "total_sequences": len(sequences),
            "total_enrollments": len(enrollments),
            "sequences_by_segment": {
                seq["target_segment"]: len([e for e in enrollments.values() if e["sequence_id"] == seq_id])
                for seq_id, seq in sequences.items()
            }
        }


# Global instance
outreach_engine = AutomatedOutreachEngine()
