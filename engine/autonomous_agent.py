#!/usr/bin/env python3
"""
RAGSPRO AUTONOMOUS AGENT v1.0
24/7 Lead Generation & Outreach System
Uses NVIDIA LLM for personalization
"""

import json
import time
import random
import requests
import re
from datetime import datetime, timedelta
from pathlib import Path
import threading

# API Keys from env
import os
from dotenv import load_dotenv
load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

class AutonomousAgent:
    """Self-running agent for lead gen and outreach"""

    def __init__(self):
        self.state_file = DATA_DIR / "agent_state.json"
        self.leads_file = DATA_DIR / "leads.json"
        self.log_file = DATA_DIR / "agent_log.json"
        self.stats_file = DATA_DIR / "agent_stats.json"
        self.running = False
        self.state = self.load_state()
        self.stats = self.load_stats()

    def load_state(self):
        """Load agent state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "last_scrape": None,
            "last_outreach": None,
            "processed_leads": [],
            "pending_followups": [],
            "mode": "active"  # active, passive, aggressive
        }

    def load_stats(self):
        """Load performance stats"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {
            "leads_scraped": 0,
            "emails_sent": 0,
            "responses_received": 0,
            "meetings_booked": 0,
            "revenue_generated": 0,
            "started_at": datetime.now().isoformat()
        }

    def save_state(self):
        """Save agent state"""
        self.state["last_updated"] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def save_stats(self):
        """Save stats"""
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def log(self, action, details, level="INFO"):
        """Log agent activity"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "action": action,
            "details": details
        }

        logs = []
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        logs = json.loads(content)
            except (json.JSONDecodeError, Exception):
                logs = []
        logs.append(entry)

        # Keep last 1000 logs
        logs = logs[-1000:]
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)

        print(f"[{level}] {action}: {details}")

    def send_telegram(self, message):
        """Send notification to Telegram"""
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            }
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            self.log("telegram_error", str(e), "ERROR")

    def call_nvidia_llm(self, prompt, max_tokens=500):
        """Call NVIDIA LLM for personalization"""
        try:
            headers = {
                "Authorization": f"Bearer {NVIDIA_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "meta/llama-3.1-8b-instruct",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9
            }

            response = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                self.log("llm_error", f"Status {response.status_code}", "ERROR")
                return None
        except Exception as e:
            self.log("llm_error", str(e), "ERROR")
            return None

    def scrape_reddit_leads(self):
        """Scrape fresh leads from Reddit"""
        self.log("scrape_start", "Starting Reddit lead scraping")

        sources = [
            {"name": "r/forhire", "url": "https://www.reddit.com/r/forhire/new.json?limit=25"},
            {"name": "r/startups", "url": "https://www.reddit.com/r/startups/new.json?limit=20"},
            {"name": "r/SaaS", "url": "https://www.reddit.com/r/SaaS/new.json?limit=20"},
            {"name": "r/entrepreneur", "url": "https://www.reddit.com/r/entrepreneur/new.json?limit=15"},
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        new_leads = []
        existing_ids = set(self.state.get("processed_leads", []))

        for source in sources:
            try:
                response = requests.get(source["url"], headers=headers, timeout=30)
                if response.status_code != 200:
                    continue

                data = response.json()
                posts = data.get("data", {}).get("children", [])

                for post in posts:
                    post_data = post.get("data", {})
                    post_id = post_data.get("id")

                    if post_id in existing_ids:
                        continue

                    title = post_data.get("title", "")
                    text = post_data.get("selftext", "")
                    full_text = f"{title} {text}"

                    # Extract contact info
                    emails = self.extract_emails(full_text)
                    linkedin = self.extract_linkedin(full_text)

                    # Score the lead
                    score = self.score_lead(full_text)

                    if score >= 60 and (emails or linkedin):
                        lead = {
                            "id": f"reddit_{post_id}",
                            "source": source["name"],
                            "title": title[:150],
                            "text": text[:500],
                            "url": f"https://reddit.com{post_data.get('permalink', '')}",
                            "score": score,
                            "contact": {
                                "emails": emails,
                                "linkedin": linkedin[0] if linkedin else ""
                            },
                            "pain_points": self.detect_pain_points(full_text),
                            "industry": self.detect_industry(full_text),
                            "status": "NEW",
                            "scraped_at": datetime.now().isoformat()
                        }
                        new_leads.append(lead)
                        existing_ids.add(post_id)

                time.sleep(2)  # Rate limiting

            except Exception as e:
                self.log("scrape_error", f"{source['name']}: {e}", "ERROR")

        # Save leads
        if new_leads:
            all_leads = []
            if self.leads_file.exists():
                with open(self.leads_file, 'r') as f:
                    all_leads = json.load(f)
            all_leads.extend(new_leads)

            with open(self.leads_file, 'w') as f:
                json.dump(all_leads, f, indent=2)

            self.state["processed_leads"] = list(existing_ids)
            self.state["last_scrape"] = datetime.now().isoformat()
            self.save_state()

            self.stats["leads_scraped"] += len(new_leads)
            self.save_stats()

            self.send_telegram(f"🎯 *{len(new_leads)} new leads scraped*\nTotal: {len(all_leads)}")
            self.log("scrape_complete", f"Found {len(new_leads)} new leads")

        return new_leads

    def extract_emails(self, text):
        """Extract emails from text"""
        import re
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(pattern, text)
        return list(set([e for e in emails if 'example.com' not in e.lower()]))

    def extract_linkedin(self, text):
        """Extract LinkedIn URLs"""
        import re
        pattern = r'linkedin\.com/in/[\w-]+'
        matches = re.findall(pattern, text)
        return ['https://' + m for m in matches]

    def score_lead(self, text):
        """Score lead quality"""
        score = 0
        text_lower = text.lower()

        # Budget mentions
        if re.search(r'\$[\d,]+', text) or 'budget' in text_lower:
            score += 25

        # Intent keywords
        intent_words = ['hiring', 'looking for', 'need developer', 'need ai', 'automation', 'chatbot']
        score += sum(10 for word in intent_words if word in text_lower)

        # Urgency
        if any(word in text_lower for word in ['urgent', 'asap', 'immediately']):
            score += 15

        # Pain points
        pain_words = ['manual', 'slow', 'overwhelm', 'losing leads', 'expensive']
        score += sum(5 for word in pain_words if word in text_lower)

        return min(score, 100)

    def detect_pain_points(self, text):
        """Detect pain points"""
        text_lower = text.lower()
        pains = []

        pain_map = {
            "slow response": ["slow", "delay", "waiting"],
            "manual work": ["manual", "repetitive", "spreadsheet"],
            "cost too high": ["expensive", "costly", "budget"],
            "no technical team": ["no developer", "hiring", "need developer"],
            "losing leads": ["leads", "customers", "missing"],
        }

        for pain, keywords in pain_map.items():
            if any(kw in text_lower for kw in keywords):
                pains.append(pain)

        return pains[:3]

    def detect_industry(self, text):
        """Detect industry"""
        text_lower = text.lower()
        industries = {
            "SaaS": ["saas", "software", "app", "platform"],
            "E-commerce": ["ecommerce", "shopify", "store"],
            "Agency": ["agency", "marketing", "client"],
            "Real Estate": ["real estate", "property"],
            "Healthcare": ["health", "medical"],
        }

        for industry, keywords in industries.items():
            if any(kw in text_lower for kw in keywords):
                return industry
        return "General"

    def generate_ai_email(self, lead):
        """Generate personalized email using NVIDIA LLM"""
        prompt = f"""Write a short, punchy cold email from Raghav (22yo founder) to a potential client.

Lead Info:
- Title: {lead['title']}
- Pain Points: {', '.join(lead.get('pain_points', ['general']))}
- Industry: {lead.get('industry', 'General')}

Rules:
- Keep it under 150 words
- Gen-Z energy, direct, no corporate fluff
- Mention specific pain point
- Include one social proof line
- Clear CTA at end
- Subject line that gets opened

Format:
Subject: [subject]
[body]
"""

        response = self.call_nvidia_llm(prompt, max_tokens=400)

        if response:
            # Parse subject and body
            lines = response.split('\n')
            subject = ""
            body = response

            for i, line in enumerate(lines):
                if line.lower().startswith('subject:'):
                    subject = line.split(':', 1)[1].strip()
                    body = '\n'.join(lines[i+1:]).strip()
                    break

            return {"subject": subject or "AI Automation | RAGS Pro", "body": body}

        # Fallback template
        return self.fallback_email(lead)

    def fallback_email(self, lead):
        """Fallback email template"""
        pain = lead.get('pain_points', ['manual work'])[0] if lead.get('pain_points') else 'manual work'

        return {
            "subject": f"Fix your {pain} | AI automation in 1 week",
            "body": f"""Hi there,

Saw your post about {lead['title'][:50]}...

I build AI systems that eliminate {pain} completely.

**What I do:**
- AI chatbots (24/7 lead qualification)
- Workflow automation (save 10+ hours/week)
- Lead scrapers (find clients on autopilot)
- SaaS MVPs (2-3 weeks delivery)

**Recent win:** Built system that found 200+ qualified leads in 48 hours.

I'm Raghav, 22yo solo founder. Not an agency - you talk to the builder directly.

Worth a 10-min call? Reply with your availability.

Best,
Raghav
ragspro.com
+91 98765 43210"""
        }

    def send_email(self, to_email, subject, body):
        """Send email via Resend"""
        try:
            response = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                json={
                    "from": "Raghav@ragspro.com",
                    "to": [to_email],
                    "subject": subject,
                    "text": body
                },
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            self.log("email_error", str(e), "ERROR")
            return False

    def run_outreach(self, limit=5):
        """Send outreach to high-value leads"""
        self.log("outreach_start", f"Starting outreach (limit: {limit})")

        if not self.leads_file.exists():
            self.log("outreach_skip", "No leads file found")
            return

        with open(self.leads_file, 'r') as f:
            leads = json.load(f)

        # Get unsent high-value leads
        unsent = [l for l in leads if l.get('status') == 'NEW' and l.get('score', 0) >= 70]
        unsent = sorted(unsent, key=lambda x: x.get('score', 0), reverse=True)[:limit]

        sent_count = 0
        for lead in unsent:
            emails = lead.get('contact', {}).get('emails', [])
            if not emails:
                continue

            # Generate personalized email
            email_content = self.generate_ai_email(lead)

            # Send
            if self.send_email(emails[0], email_content['subject'], email_content['body']):
                lead['status'] = 'CONTACTED'
                lead['contacted_at'] = datetime.now().isoformat()
                lead['email_subject'] = email_content['subject']
                sent_count += 1

                self.log("email_sent", f"{emails[0]} - {email_content['subject'][:50]}")
                time.sleep(random.uniform(30, 60))  # Avoid rate limits

        # Save updated leads
        with open(self.leads_file, 'w') as f:
            json.dump(leads, f, indent=2)

        # Update stats
        self.stats["emails_sent"] += sent_count
        self.save_stats()

        self.state["last_outreach"] = datetime.now().isoformat()
        self.save_state()

        if sent_count > 0:
            self.send_telegram(f"📧 *{sent_count} emails sent*\nTotal sent: {self.stats['emails_sent']}")

        self.log("outreach_complete", f"Sent {sent_count} emails")
        return sent_count

    def check_responses(self):
        """Check for email responses (placeholder for now)"""
        # This would integrate with email API to check replies
        self.log("check_responses", "Checking for responses...")
        return 0

    def generate_daily_report(self):
        """Generate daily report"""
        report = f"""
🤖 *RAGSPRO AGENT DAILY REPORT*

📊 *Stats:*
- Leads scraped: {self.stats['leads_scraped']}
- Emails sent: {self.stats['emails_sent']}
- Responses: {self.stats['responses_received']}
- Meetings: {self.stats['meetings_booked']}

🔧 *Status:*
- Mode: {self.state.get('mode', 'active').upper()}
- Last scrape: {self.state.get('last_scrape', 'Never')[:10]}
- Last outreach: {self.state.get('last_outreach', 'Never')[:10]}

💰 *Revenue Goal:* ₹50k/month
Current: ₹{self.stats['revenue_generated']}

_Agent running since {self.stats['started_at'][:10]}_
        """
        self.send_telegram(report)
        self.log("daily_report", "Report sent")

    def job_scrape(self):
        """Scheduled: Scrape leads"""
        self.scrape_reddit_leads()

    def job_outreach(self):
        """Scheduled: Send outreach"""
        self.run_outreach(limit=3)

    def job_report(self):
        """Scheduled: Daily report"""
        self.generate_daily_report()

    def run_scheduler(self):
        """Run the scheduler loop - custom implementation without schedule module"""
        self.log("scheduler_start", "Agent scheduler started")

        self.send_telegram("🚀 *RAGSPRO Autonomous Agent Started*\n\n📅 Schedule:\n- Scrape: Every 2 hours\n- Outreach: Every 4 hours\n- Report: Daily 9 AM\n\n_Mode: ACTIVE_")

        last_scrape = datetime.now()
        last_outreach = datetime.now()
        last_report = datetime.now().replace(hour=0, minute=0)  # Force report today

        while self.running:
            now = datetime.now()

            # Scrape every 2 hours
            if (now - last_scrape).total_seconds() >= 7200:  # 2 hours
                self.job_scrape()
                last_scrape = now

            # Outreach every 4 hours
            if (now - last_outreach).total_seconds() >= 14400:  # 4 hours
                self.job_outreach()
                last_outreach = now

            # Daily report at 9 AM
            if now.hour == 9 and (now - last_report).total_seconds() >= 86400:
                self.job_report()
                last_report = now

            time.sleep(60)  # Check every minute

    def stop(self):
        """Stop the agent"""
        self.running = False
        self.log("agent_stop", "Agent stopped")
        self.send_telegram("🛑 *Agent stopped*")

    def get_telegram_updates(self, offset=None):
        """Get updates from Telegram"""
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"offset": offset, "limit": 10} if offset else {"limit": 10}
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return {"ok": False, "result": []}
        except Exception as e:
            self.log("telegram_poll_error", str(e), "ERROR")
            return {"ok": False, "result": []}

    def handle_telegram_command(self, message):
        """Handle Telegram commands"""
        text = message.get("text", "").strip().lower()
        chat_id = message.get("chat", {}).get("id")
        user = message.get("from", {}).get("first_name", "Unknown")

        if not text.startswith("/"):
            return

        command = text.split()[0]
        self.log("telegram_command", f"{user}: {command}")

        # Get fresh stats
        with open(self.leads_file, 'r') as f:
            leads = json.load(f)
        total = len(leads)
        high_value = len([l for l in leads if l.get('score', 0) >= 70])
        new_leads = len([l for l in leads if l.get('status') == 'NEW'])

        responses = {
            "/status": f"""🤖 *AGENT STATUS*

Mode: {self.state.get('mode', 'ACTIVE').upper()}
Running: {'✅ YES' if self.running else '❌ NO'}

📊 Leads:
• Total: {total}
• High Value: {high_value}
• New: {new_leads}

📧 Emails: {self.stats['emails_sent']}
📨 Responses: {self.stats['responses_received']}

Last Scrape: {self.state.get('last_scrape', 'Never')[:16] if self.state.get('last_scrape') else 'Never'}
Last Outreach: {self.state.get('last_outreach', 'Never')[:16] if self.state.get('last_outreach') else 'Never'}""",

            "/stats": f"""📊 *AGENT STATS*

Leads Scraped: {self.stats['leads_scraped']}
Emails Sent: {self.stats['emails_sent']}
Responses: {self.stats['responses_received']}
Meetings: {self.stats['meetings_booked']}
Revenue: ₹{self.stats['revenue_generated']}

Started: {self.stats['started_at'][:10]}
Uptime: Running since {self.stats['started_at'][:16]}""",

            "/help": """🤖 *AVAILABLE COMMANDS*

/status - Agent status & leads
/stats - Performance stats
/scrape - Run lead scraper now
/outreach - Send outreach emails now
/report - Generate daily report
/help - Show this message

Auto Schedule:
• Scrape: Every 2 hours
• Outreach: Every 4 hours
• Report: Daily 9 AM""",

            "/report": None  # Handled separately
        }

        if command == "/scrape":
            self.send_telegram("🔍 *Starting scrape...*")
            threading.Thread(target=self.scrape_reddit_leads).start()

        elif command == "/outreach":
            self.send_telegram("📧 *Starting outreach...*")
            threading.Thread(target=self.run_outreach, args=(3,)).start()

        elif command == "/report":
            self.generate_daily_report()

        elif command in responses:
            self.send_telegram(responses[command])

        else:
            self.send_telegram("❓ Unknown command. Use /help for commands.")

    def run_telegram_listener(self):
        """Listen for Telegram commands"""
        self.log("telegram_listener", "Starting Telegram command listener")
        offset = None

        while self.running:
            try:
                updates = self.get_telegram_updates(offset)

                if updates.get("ok") and updates.get("result"):
                    for update in updates["result"]:
                        # Update offset
                        offset = update.get("update_id", 0) + 1

                        # Handle message
                        if "message" in update:
                            message = update["message"]
                            # Only respond to allowed chat
                            if str(message.get("chat", {}).get("id")) == TELEGRAM_CHAT_ID:
                                self.handle_telegram_command(message)

                time.sleep(5)  # Poll every 5 seconds

            except Exception as e:
                self.log("telegram_listener_error", str(e), "ERROR")
                time.sleep(10)

    def start(self):
        """Start the autonomous agent"""
        self.running = True
        self.log("agent_start", "RAGSPRO Autonomous Agent v1.0 starting")

        # Run initial tasks
        self.log("initial_run", "Running initial scrape and outreach")
        self.scrape_reddit_leads()
        time.sleep(5)
        self.run_outreach(limit=3)

        # Start scheduler in background
        self.scheduler_thread = threading.Thread(target=self.run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()

        # Start Telegram listener in background
        self.telegram_thread = threading.Thread(target=self.run_telegram_listener)
        self.telegram_thread.daemon = True
        self.telegram_thread.start()

        self.log("agent_ready", "Agent is running autonomously")
        self.send_telegram("🚀 *Agent started!*\n\nUse /help for commands\nChat ID: " + TELEGRAM_CHAT_ID)


if __name__ == "__main__":
    agent = AutonomousAgent()
    try:
        agent.start()
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()
        print("\nAgent stopped by user")
