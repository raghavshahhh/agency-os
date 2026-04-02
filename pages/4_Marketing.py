#!/usr/bin/env python3
"""
RAGSPRO Marketing Command Center
Real integration with Agent System, Content Engine, and existing modules
"""

import streamlit as st
import json
import sys
from pathlib import Path
from datetime import datetime
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))

st.set_page_config(
    page_title="Marketing Command Center",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 RAGSPRO Marketing Command Center")
st.markdown("Real-time agent monitoring + content automation")

# Check agent system
AGENT_LOG_FILE = Path(__file__).parent.parent / "data" / "agent_system_logs.json"
AGENT_STATE_FILE = Path(__file__).parent.parent / "data" / "agent_states.json"

# ─── AGENT STATUS DASHBOARD ─────────────────────────────────────────────────

st.header("🤖 Self-Monitoring Agents")

agent_cols = st.columns(3)

agents = [
    ("LeadGenerationAgent", "🔍", "Scrapes Reddit + Google Maps every 4h"),
    ("ContentCreationAgent", "✍️", "Generates content daily at 6 AM"),
    ("OutreachAutomationAgent", "📧", "Day 0/3/7 email sequences"),
]

for idx, (name, emoji, desc) in enumerate(agents):
    with agent_cols[idx]:
        st.markdown(f"### {emoji} {name}")

        # Get agent status from file
        status = "unknown"
        if AGENT_STATE_FILE.exists():
            try:
                with open(AGENT_STATE_FILE) as f:
                    states = json.load(f)
                    agent_state = states.get(name, {})
                    status = agent_state.get("status", "unknown")
            except:
                pass

        status_colors = {
            "running": "🟢",
            "idle": "⚪",
            "error": "🔴",
            "recovering": "🟡",
            "unknown": "⚫"
        }

        st.markdown(f"{status_colors.get(status, '⚫')} Status: **{status.upper()}**")
        st.caption(desc)

        # Quick actions
        if st.button(f"View {name} Logs", key=f"logs_{name}"):
            st.session_state['viewing_agent'] = name
            st.rerun()

# ─── START AGENTS BUTTON ─────────────────────────────────────────────────────

st.divider()
agent_action_col1, agent_action_col2 = st.columns(2)

with agent_action_col1:
    if st.button("🚀 Start All Agents", use_container_width=True):
        with st.spinner("Starting agents..."):
            try:
                result = subprocess.run(
                    ["python3", str(Path(__file__).parent.parent / "agent_manager.py"), "start"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                st.success("Agents started! Check logs.")
            except Exception as e:
                st.error(f"Failed to start: {e}")

with agent_action_col2:
    if st.button("📊 Check Agent Status", use_container_width=True):
        try:
            result = subprocess.run(
                ["python3", str(Path(__file__).parent.parent / "agent_manager.py"), "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            st.code(result.stdout)
        except Exception as e:
            st.error(f"Failed to get status: {e}")

# ─── AGENT LOGS VIEWER ──────────────────────────────────────────────────────

if 'viewing_agent' in st.session_state:
    st.divider()
    st.subheader(f"📜 Logs: {st.session_state['viewing_agent']}")

    if AGENT_LOG_FILE.exists():
        try:
            with open(AGENT_LOG_FILE) as f:
                logs = json.load(f)

            agent_logs = [l for l in logs if l.get("agent") == st.session_state['viewing_agent']]
            agent_logs = agent_logs[-20:]  # Last 20

            for log in reversed(agent_logs):
                level_colors = {
                    "info": "blue",
                    "success": "green",
                    "warning": "orange",
                    "error": "red",
                    "critical": "red"
                }
                with st.expander(f"{log['timestamp']} - {log['level'].upper()}"):
                    st.write(log['message'])
                    if log.get('data'):
                        st.json(log['data'])
        except Exception as e:
            st.error(f"Error loading logs: {e}")

    if st.button("Close Logs"):
        del st.session_state['viewing_agent']
        st.rerun()

# ─── CONTENT GENERATION ─────────────────────────────────────────────────────

st.divider()
st.header("📝 Content Generation")

content_col1, content_col2 = st.columns(2)

with content_col1:
    st.markdown("### Generate Today's Content")
    st.markdown("Uses NVIDIA NIM + Content Engine")

    if st.button("🚀 Generate Content Now", use_container_width=True):
        with st.spinner("Generating LinkedIn, Twitter, Instagram, Reel scripts..."):
            try:
                result = subprocess.run(
                    ["python3", str(Path(__file__).parent.parent / "engine" / "content_engine.py")],
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode == 0:
                    st.success("✅ Content generated!")
                    st.code(result.stdout[:1000])
                else:
                    st.error(f"Generation failed: {result.stderr[:500]}")
            except Exception as e:
                st.error(f"Error: {e}")

with content_col2:
    st.markdown("### Today's Content Status")

    from config import DATA_DIR
    today_folder = DATA_DIR / "content" / datetime.now().strftime("%Y-%m-%d")

    if today_folder.exists():
        platforms = {
            "linkedin.txt": "LinkedIn Post",
            "twitter.txt": "Twitter/X Post",
            "instagram.txt": "Instagram Caption",
            "reel.txt": "Reel Script"
        }

        for filename, label in platforms.items():
            filepath = today_folder / filename
            if filepath.exists():
                st.success(f"✅ {label}")
            else:
                st.warning(f"⏳ {label} - Not generated")
    else:
        st.info("No content folder for today yet")

# ─── LEAD SCRAPING ────────────────────────────────────────────────────────────

st.divider()
st.header("🔍 Lead Scraping")

scrape_col1, scrape_col2 = st.columns(2)

with scrape_col1:
    st.markdown("### Manual Scrape")

    scrape_source = st.selectbox(
        "Source",
        ["Reddit [HIRING] Posts", "Google Maps (Apify)", "LinkedIn Jobs (Apify)"]
    )

    if st.button("🔄 Start Scraping", use_container_width=True):
        with st.spinner("Scraping... This may take 2-3 minutes"):
            try:
                if "Reddit" in scrape_source:
                    result = subprocess.run(
                        ["python3", str(Path(__file__).parent.parent / "engine" / "lead_scraper.py")],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                else:
                    result = subprocess.run(
                        ["python3", str(Path(__file__).parent.parent / "engine" / "apify_scraper.py")],
                        capture_output=True,
                        text=True,
                        timeout=600
                    )

                if result.returncode == 0:
                    st.success("✅ Scraping complete!")
                    st.code(result.stdout[:1500])
                else:
                    st.error(f"Scraping failed: {result.stderr[:500]}")
            except Exception as e:
                st.error(f"Error: {e}")

with scrape_col2:
    st.markdown("### Scraping Stats")

    try:
        from config import DATA_DIR
        leads_file = DATA_DIR / "leads.json"

        if leads_file.exists():
            with open(leads_file) as f:
                leads = json.load(f)

            total = len(leads)
            new_count = len([l for l in leads if l.get("status") == "NEW"])
            contacted = len([l for l in leads if l.get("status") == "CONTACTED"])
            hot = len([l for l in leads if l.get("status") == "HOT_LEAD"])

            st.metric("Total Leads", total)
            st.metric("New (Uncontacted)", new_count)
            st.metric("Hot Leads", hot)

            if new_count > 50:
                st.warning(f"⚠️ {new_count} leads need outreach!")
        else:
            st.info("No leads database yet")
    except Exception as e:
        st.error(f"Error loading stats: {e}")

# ─── EMAIL AUTOMATION ─────────────────────────────────────────────────────────

st.divider()
st.header("📧 Email Automation")

email_col1, email_col2 = st.columns(2)

with email_col1:
    st.markdown("### Manual Email Actions")

    email_action = st.selectbox(
        "Action",
        ["Send Day 0 (Initial)", "Send Day 3 (Follow-up)", "Send Day 7 (Break-up)"]
    )

    max_emails = st.slider("Max emails to send", 1, 20, 5)

    if st.button("📤 Execute", use_container_width=True):
        st.info("Email automation runs automatically via OutreachAgent")
        st.caption("Check agent logs for daily execution")

with email_col2:
    st.markdown("### Email Stats")

    try:
        from outreach_engine import get_outreach_stats
        stats = get_outreach_stats()

        st.metric("Emails Sent", stats.get("emails_sent", 0))
        st.metric("LinkedIn DMs", stats.get("linkedin_sent", 0))
        st.metric("Replies", stats.get("replied", 0))

        if stats.get("emails_sent", 0) > 0:
            reply_rate = (stats.get("replied", 0) / stats.get("emails_sent", 1)) * 100
            st.metric("Reply Rate", f"{reply_rate:.1f}%")
    except Exception as e:
        st.error(f"Error: {e}")

# ─── TELEGRAM NOTIFICATIONS ───────────────────────────────────────────────────

st.divider()
st.header("📱 Telegram Notifications")

if st.button("📨 Send Test Notification", use_container_width=True):
    try:
        from telegram_brief import send_brief
        send_brief("🧪 Test notification from Marketing Command Center!")
        st.success("Test notification sent!")
    except Exception as e:
        st.error(f"Failed: {e}")

# ─── FOOTER ───────────────────────────────────────────────────────────────────

st.divider()
st.caption("Built by RAGSPRO | Agents run 24/7 in background | Errors auto-reported to Telegram")
