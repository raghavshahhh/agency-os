"""
RAGSPRO Settings — API keys, branding, n8n integration, preferences
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="RAGSPRO - Settings", page_icon="⚙️", layout="wide")

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
ENV_FILE = BASE_DIR / ".env"
SETTINGS_FILE = DATA_DIR / "settings.json"


def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "agency_name": "RAGSPRO",
        "tagline": "AI Chatbots, SaaS & Automation Solutions",
        "website": "https://ragspro.com",
        "calendly": "https://calendly.com/ragspro/discovery",
        "theme": "dark",
        "notifications": {
            "telegram": True,
            "email": False
        },
        "automation": {
            "content_time": "07:00",
            "lead_scrape_time": "07:30",
            "telegram_brief_time": "08:00",
            "proposal_time": "09:00"
        }
    }


def save_settings(settings):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)


def load_env_keys():
    """Load current API keys from .env (show masked)"""
    keys = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip()
                    if value:
                        masked = value[:6] + "..." + value[-4:] if len(value) > 12 else "****"
                    else:
                        masked = "Not set"
                    keys[key] = {"value": value, "masked": masked}
    return keys


# ─── Main ─────────────────────────────────────────────────────────────────────

st.title("⚙️ Settings")

settings = load_settings()

tab1, tab2, tab3, tab4 = st.tabs(["🏢 Agency", "🔑 API Keys", "🤖 Automation", "📊 Data"])

# ─── Agency Settings ──────────────────────────────────────────────────────────
with tab1:
    st.subheader("Agency Branding")

    with st.form("agency_settings"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Agency Name", value=settings.get("agency_name", "RAGSPRO"))
            tagline = st.text_input("Tagline", value=settings.get("tagline", ""))
            website = st.text_input("Website", value=settings.get("website", ""))
        with col2:
            calendly = st.text_input("Calendly URL", value=settings.get("calendly", ""))
            email = st.text_input("Contact Email", value=settings.get("email", "ragsproai@gmail.com"))
            phone = st.text_input("Contact Phone", value=settings.get("phone", ""))

        services = st.text_area("Services (comma separated)",
            value=", ".join(settings.get("services", ["AI Chatbots", "SaaS", "Automation"])))

        submitted = st.form_submit_button("Save Agency Settings", use_container_width=True)
        if submitted:
            settings["agency_name"] = name
            settings["tagline"] = tagline
            settings["website"] = website
            settings["calendly"] = calendly
            settings["email"] = email
            settings["phone"] = phone
            settings["services"] = [s.strip() for s in services.split(",")]
            save_settings(settings)
            st.success("✅ Agency settings saved!")

    st.divider()
    st.subheader("Social Media Links")
    with st.form("social_settings"):
        col1, col2 = st.columns(2)
        socials = settings.get("socials", {})
        with col1:
            linkedin = st.text_input("LinkedIn", value=socials.get("linkedin", ""))
            twitter = st.text_input("Twitter/X", value=socials.get("twitter", ""))
        with col2:
            instagram = st.text_input("Instagram", value=socials.get("instagram", ""))
            github = st.text_input("GitHub", value=socials.get("github", ""))

        if st.form_submit_button("Save Social Links", use_container_width=True):
            settings["socials"] = {
                "linkedin": linkedin, "twitter": twitter,
                "instagram": instagram, "github": github
            }
            save_settings(settings)
            st.success("✅ Social links saved!")


# ─── API Keys ─────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("API Keys Status")
    st.warning("⚠️ Keys are stored in `.env` file. Edit directly for security.")

    keys = load_env_keys()
    key_names = {
        "NVIDIA_API_KEY": "NVIDIA NIM (AI Engine)",
        "TELEGRAM_BOT_TOKEN": "Telegram Bot",
        "TELEGRAM_CHAT_ID": "Telegram Chat ID",
        "GMAIL_USER": "Gmail Address",
        "GMAIL_APP_PASSWORD": "Gmail App Password",
        "SERPAPI_KEY": "SerpAPI (Search)",
        "TAVILY_API_KEY": "Tavily (Search)",
        "N8N_API_KEY": "n8n API",
        "RESEND_API_KEY": "Resend (Email)"
    }

    for key_id, label in key_names.items():
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown(f"**{label}**")
        with col2:
            key_info = keys.get(key_id, {"masked": "Not set"})
            status = "✅" if key_info["masked"] != "Not set" else "❌"
            st.markdown(f"{status} `{key_info['masked']}`")
        with col3:
            st.caption(key_id)

    st.divider()
    st.info("To update keys, edit `.env` file at:\n`" + str(ENV_FILE) + "`")


# ─── Automation Settings ──────────────────────────────────────────────────────
with tab3:
    st.subheader("Automation Schedule")

    auto = settings.get("automation", {})

    with st.form("automation_settings"):
        col1, col2 = st.columns(2)
        with col1:
            content_time = st.text_input("Content Generation", value=auto.get("content_time", "07:00"))
            lead_time = st.text_input("Lead Scraping", value=auto.get("lead_scrape_time", "07:30"))
        with col2:
            brief_time = st.text_input("Telegram Brief", value=auto.get("telegram_brief_time", "08:00"))
            proposal_time = st.text_input("Proposal Generation", value=auto.get("proposal_time", "09:00"))

        st.divider()
        st.markdown("**Notifications**")
        notif = settings.get("notifications", {})
        telegram_notif = st.checkbox("Telegram Notifications", value=notif.get("telegram", True))
        email_notif = st.checkbox("Email Notifications", value=notif.get("email", False))

        if st.form_submit_button("Save Automation Settings", use_container_width=True):
            settings["automation"] = {
                "content_time": content_time,
                "lead_scrape_time": lead_time,
                "telegram_brief_time": brief_time,
                "proposal_time": proposal_time
            }
            settings["notifications"] = {
                "telegram": telegram_notif,
                "email": email_notif
            }
            save_settings(settings)
            st.success("✅ Automation settings saved!")

    st.divider()
    st.subheader("Cron Jobs")
    st.info("Run `python3 engine/scheduler.py` to set up system cron jobs based on above schedule.")

    if st.button("📋 Show Current Cron Jobs"):
        import subprocess
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.stdout:
            ragspro_jobs = [l for l in result.stdout.split("\n") if "RAGSPRO" in l]
            if ragspro_jobs:
                for job in ragspro_jobs:
                    st.code(job)
            else:
                st.info("No RAGSPRO cron jobs found")
        else:
            st.info("No cron jobs configured")


# ─── Data Management ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("Data Overview")

    data_files = {
        "leads.json": "Leads Database",
        "pipeline.json": "Sales Pipeline",
        "revenue.json": "Revenue Data",
        "clients.json": "Client Database",
        "chat_history.json": "AI Chat History",
        "checklist.json": "Daily Checklist",
        "agency_db.json": "Legacy Database",
        "settings.json": "Settings"
    }

    for filename, label in data_files.items():
        filepath = DATA_DIR / filename
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**{label}**")
        with col2:
            if filepath.exists():
                size = filepath.stat().st_size
                st.markdown(f"✅ {size/1024:.1f} KB")
            else:
                st.markdown("❌ Not found")
        with col3:
            st.caption(filename)

    st.divider()
    st.subheader("Content Folders")
    content_dir = DATA_DIR / "content"
    if content_dir.exists():
        folders = sorted([f.name for f in content_dir.iterdir() if f.is_dir()], reverse=True)
        st.markdown(f"**{len(folders)} content days** generated")
        if folders:
            st.caption(f"Latest: {folders[0]} | Oldest: {folders[-1]}")
    else:
        st.info("No content generated yet")

    st.divider()
    st.subheader("⚠️ Danger Zone")
    st.error("These actions cannot be undone!")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🗑 Clear Chat History", use_container_width=True):
            chat_file = DATA_DIR / "chat_history.json"
            if chat_file.exists():
                chat_file.unlink()
            st.success("Chat history cleared!")
            st.rerun()
    with col2:
        if st.button("🗑 Clear Checklist", use_container_width=True):
            checklist_file = DATA_DIR / "checklist.json"
            if checklist_file.exists():
                checklist_file.unlink()
            st.success("Checklist cleared!")
            st.rerun()
