# RAGSPRO Agency OS - Meta Configuration

## 🎯 For Meta/Claude Code Integration

### Skill Files Location
```
~/.claude/skills/
├── agency-os-guide.md       # This file
├── agency-os-debug.md       # Debug guide
└── agency-os-deploy.md      # Deployment guide
```

---

## 🤖 Agent Commands Reference

### Quick Commands

```bash
# Run everything
python3 agent_manager.py start

# Check what's running
python3 agent_manager.py status

# Generate content now
python3 engine/content_engine.py

# Scrape leads now
python3 engine/lead_scraper.py
```

### Streamlit Shortcuts

```bash
# Main dashboard
srun="streamlit run app.py"

# Specific page
srun marketing    # pages/4_Marketing.py
srun agents        # pages/5_Agent_Dashboard.py
```

---

## 🔍 Common Issues & Fixes

### 1. "Module not found" Error

**Fix:**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
```

### 2. "API key not set" Error

**Fix:**
```bash
# Check if .env exists
ls -la .env

# Load it
source .env

# Or in Python:
from dotenv import load_dotenv
load_dotenv()
```

### 3. "IndentationError" in Pages

**Fix:** Already fixed in commit 25e0640. If occurs:
```bash
# Run syntax check
python3 -m py_compile pages/*.py
```

### 4. Agent Not Responding

**Fix:**
```bash
# Check if running
pgrep -f "agent_manager"

# Kill and restart
pkill -f "agent_manager"
python3 agent_manager.py start
```

---

## 📊 Dashboard Access

### Live URLs

| Dashboard | Local | Streamlit Cloud |
|-----------|-------|------------------|
| Main | http://localhost:8501 | https://agencyy.streamlit.app |
| Marketing | /4_Marketing | https://agencyy.streamlit.app/~/+/Marketing |
| Agents | /5_Agent_Dashboard | https://agencyy.streamlit.app/~/+/Agent_Dashboard |

---

## 🔧 Development Mode

### Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Mode

```bash
# Run with test data
TEST_MODE=1 python3 app.py
```

### Hot Reload

```bash
# Auto-restart on changes
streamlit run app.py --server.runOnSave true
```

---

## 🚀 Deployment Checklist

- [ ] .env configured with real API keys
- [ ] GitHub secrets set (if using Actions)
- [ ] requirements.txt up to date
- [ ] No syntax errors (`python3 -m py_compile`)
- [ ] Tested locally (`streamlit run app.py`)
- [ ] Agents tested (`python3 agent_manager.py status`)
- [ ] Telegram bot responding
- [ ] Database files created (data/leads.json)

---

## 📝 File Templates

### New Agent Template

```python
#!/usr/bin/env python3
"""New Agent for Agency OS"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import BaseExpertAgent, AgentProfile, AgentRole

class NewAgent(BaseExpertAgent):
    def __init__(self, comm_bus):
        profile = AgentProfile(
            id="new_agent",
            name="AgentName",
            role=AgentRole.MARKETING,  # or appropriate role
            avatar="🎯",
            expertise=["Skill 1", "Skill 2"],
            personality="Description",
            goals=["Goal 1", "Goal 2"]
        )
        super().__init__(profile, comm_bus)

    def _handle_message(self, message):
        """Handle incoming messages"""
        pass

if __name__ == "__main__":
    from agents import AgentCommunicationBus
    bus = AgentCommunicationBus()
    agent = NewAgent(bus)
    print(f"Agent {agent.profile.name} ready!")
```

### New Page Template

```python
#!/usr/bin/env python3
"""New Streamlit Page"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))

st.set_page_config(
    page_title="Page Title",
    page_icon="🎯",
    layout="wide"
)

st.title("Page Title")
```

---

## 🔐 Security Notes

### API Keys
- Never commit `.env` to git
- Rotate keys if exposed
- Use environment variables in production

### File Permissions
```bash
# Sensitive files
chmod 600 .env
chmod 644 *.py
```

---

## 📈 Performance Tips

1. **Cache expensive operations:**
```python
@st.cache_data(ttl=3600)
def expensive_function():
    pass
```

2. **Lazy load modules:**
```python
if "module" not in sys.modules:
    import heavy_module
```

3. **Database connection pooling:**
```python
# Use existing connections
from config import DATA_DIR
```

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Start all | `python3 agent_manager.py start` |
| Status | `python3 agent_manager.py status` |
| Logs | `python3 agent_manager.py logs` |
| Dashboard | `streamlit run app.py` |
| Test agents | `python3 quick_test.py` |
| Git push | `git push origin main` |

---

## 💬 Claude Code Commands

When working with Agency OS, use these shortcuts:

```
/run agents        - Start all agents
/status            - Check agent status
/deploy            - Push to GitHub
/test              - Run syntax checks
/fix               - Fix common issues
```

---

**Maintained by:** RAGSPRO Team
**Last Updated:** 2026-04-03
