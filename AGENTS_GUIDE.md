# RAGSPRO Agency OS - Agent System Guide

## 📋 Overview

Agency OS has **2 types of agents**:
1. **Self-Monitoring Agents** (engine/agent_system/) - Run 24/7, self-heal
2. **Expert Agents** (engine/agents/) - AI personas that collaborate

---

## 🤖 Agent Types Explained

### 1. Self-Monitoring Agents (Production Ready)

| Agent | File | Purpose | Frequency |
|-------|------|---------|-----------|
| LeadGenerationAgent | `engine/agent_system/lead_agent.py` | Scrapes Reddit, Google Maps | Every 4h |
| ContentCreationAgent | `engine/agent_system/content_agent.py` | Generates daily content | Daily 6 AM |
| OutreachAutomationAgent | `engine/agent_system/outreach_agent.py` | Sends emails | Hourly |

### 2. Expert Agents (AI Personas)

| Agent | Name | Role | Expertise |
|-------|------|------|-----------|
| MarketingAgent | Sarah | 🎯 Marketing | Strategy, campaigns, coordination |
| ContentCreationAgent | Alex | ✍️ Content | Instagram, LinkedIn, Twitter, YouTube |
| MarketResearchAgent | Maya | 🔬 Research | Trends, competitors, content gaps |
| BusinessIntelligenceAgent | Vikram | 💼 Business | Revenue, opportunities, metrics |
| PostingAutomationAgent | Zara | 📤 Posting | Auto-post, scheduling, queue |

---

## 🚀 How to Run Agents

### Option 1: Agent Manager (Recommended)

```bash
# Start all self-monitoring agents
python3 agent_manager.py start

# Check status
python3 agent_manager.py status

# View logs
python3 agent_manager.py logs --agent LeadGenerationAgent

# Stop all
python3 agent_manager.py stop
```

### Option 2: Individual Agent Testing

```bash
# Test lead agent
python3 engine/agent_system/lead_agent.py

# Test content agent
python3 engine/agent_system/content_agent.py

# Test outreach agent
python3 engine/agent_system/outreach_agent.py
```

### Option 3: Expert Agents (Via Streamlit)

```bash
# Start Streamlit dashboard
streamlit run app.py

# Navigate to:
# - "📊 Marketing Command Center" (pages/4_Marketing.py) - Self-monitoring agents
# - "🤖 Agent Command Center" (pages/5_Agent_Dashboard.py) - Expert agents
```

---

## ⚙️ Configuration

### 1. Create .env file

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### 2. Required API Keys

```env
# Essential
NVIDIA_API_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id

# Email
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
RESEND_API_KEY=your_resend_key

# Optional
SERPAPI_KEY=your_key
TAVILY_API_KEY=your_key
N8N_API_KEY=your_key
HUNTER_API_KEY=your_key
```

---

## 📊 Agent Communication

Agents talk to each other via `AgentCommunicationBus`:

```python
from engine.agents import AgentOrchestrator

orch = AgentOrchestrator()
orth.initialize_agents()

# Marketing agent requests content
marketing = orch.get_agent("marketing_agent")
marketing.request_content_creation("instagram", "carousel")

# Research agent finds trends
research = orch.get_agent("research_agent")
research.run_daily_research()
```

---

## 🔧 Troubleshooting

### Agents Not Starting

```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/engine"

# Install dependencies
pip install -r requirements.txt
```

### API Key Errors

```bash
# Verify .env is loaded
python3 -c "from config import NVIDIA_API_KEY; print(NVIDIA_API_KEY[:10])"
```

### Streamlit Issues

```bash
# Clear cache
rm -rf .streamlit/cache

# Rerun
streamlit run app.py
```

---

## 📁 File Structure

```
engine/
├── agent_system/           # Self-monitoring agents
│   ├── __init__.py        # BaseAgent class
│   ├── lead_agent.py      # LeadGenerationAgent
│   ├── content_agent.py   # ContentCreationAgent
│   └── outreach_agent.py  # OutreachAutomationAgent
├── agents/                # Expert agents
│   ├── __init__.py        # AgentOrchestrator
│   ├── marketing_agent.py # Sarah
│   ├── content_agent.py   # Alex
│   ├── research_agent.py  # Maya
│   ├── business_agent.py  # Vikram
│   └── posting_agent.py   # Zara
└── config.py             # API keys & settings

pages/
├── 4_Marketing.py          # Self-monitoring dashboard
└── 5_Agent_Dashboard.py    # Expert agents dashboard

agent_manager.py           # CLI to manage agents
```

---

## 🔄 Automation Schedule

| Task | Frequency | Agent |
|------|-----------|-------|
| Reddit scraping | Every 4 hours | LeadGenerationAgent |
| Google Maps | Daily | LeadGenerationAgent |
| Content generation | Daily 6 AM | ContentCreationAgent |
| Day 0 emails | Hourly | OutreachAutomationAgent |
| Follow-ups | Every 6 hours | OutreachAutomationAgent |
| Health checks | Hourly | All agents |
| Stats report | Daily 9 AM | OutreachAutomationAgent |

---

## 📱 Telegram Commands

Once agents are running, message your bot:
- `/status` - Check agent status
- `/leads` - Get lead count
- `/content` - Get content status
- `/help` - Show all commands

---

## 💡 Tips

1. **Always start with:** `python3 agent_manager.py status`
2. **Test individual agents first** before running all
3. **Check logs** when errors occur
4. **Ensure .env is configured** before starting
5. **Use Streamlit dashboard** for visual monitoring

---

## 🆘 Support

- **GitHub:** https://github.com/raghavshahhh/agency-os
- **Streamlit Live:** https://agencyy.streamlit.app
- **Contact:** ragsproai@gmail.com
