"""
RAGSPRO Command Center — Main Dashboard Home
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path

# ─── Simple Password Auth ───────────────────────────────────────────────────────
import os
from dotenv import load_dotenv
load_dotenv()
AUTH_PASSWORD = os.getenv("APP_PASSWORD", "ragspro2025")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.set_page_config(page_title="RAGSPRO - Login", page_icon="🔒")
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 2rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        text-align: center;
    }
    .login-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='login-container'>
        <div class='login-title'>🚀 RAGSPRO</div>
        <p style='color:#666;'>Command Center</p>
    </div>
    """, unsafe_allow_html=True)

    password = st.text_input("Enter Password", type="password", key="login_password")
    if st.button("Login", use_container_width=True):
        if password == AUTH_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password")
    st.stop()

st.set_page_config(
    page_title="RAGSPRO Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = Path(__file__).parent / "data"
CONTENT_DIR = DATA_DIR / "content"

# ─── Modern CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .main { font-family: 'Inter', sans-serif; }

    .hero-section {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }

    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(102,126,234,0.3), transparent);
        border-radius: 50%;
    }

    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
        background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.7);
        margin-bottom: 1rem;
    }

    .hero-date {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.5);
    }

    .stat-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a2e;
        line-height: 1;
    }

    .stat-label {
        font-size: 0.72rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.25rem;
    }

    .stat-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }

    .quick-nav-card {
        background: #f8f9ff;
        border: 1px solid #e0e5ff;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
    }

    .quick-nav-card:hover {
        background: #667eea;
        color: white;
        border-color: #667eea;
    }

    .quick-nav-card .icon { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .quick-nav-card .title { font-size: 0.85rem; font-weight: 600; }
    .quick-nav-card .desc { font-size: 0.7rem; color: #888; }

    .activity-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.6rem 0;
        border-bottom: 1px solid #f0f0f5;
    }

    .activity-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── Load Data ────────────────────────────────────────────────────────────────

def load_json(filename, default=None):
    filepath = DATA_DIR / filename
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return default if default is not None else []


leads = load_json("leads.json", [])
pipeline = load_json("pipeline.json", [])
clients = load_json("clients.json", [])
revenue_data = load_json("revenue.json", {"entries": []})

new_leads = len([l for l in leads if l.get("status") == "NEW"])
hot_leads = len([l for l in leads if l.get("status") == "HOT_LEAD"])
pipeline_value = sum(d.get("value", 0) for d in pipeline)
active_clients = len([c for c in clients if c.get("status") == "Active"])

# Revenue
rev_entries = revenue_data.get("entries", []) if isinstance(revenue_data, dict) else []
current_month = datetime.now().strftime("%Y-%m")
month_income = sum(e["amount"] for e in rev_entries if e.get("type") == "income" and e.get("date", "").startswith(current_month))

today_folder = CONTENT_DIR / datetime.now().strftime("%Y-%m-%d")
content_ready = today_folder.exists() and len(list(today_folder.glob("*.txt"))) > 0


# ─── Hero Section ─────────────────────────────────────────────────────────────

st.markdown(f"""
<div class='hero-section'>
    <div class='hero-title'>🚀 RAGSPRO Command Center</div>
    <div class='hero-subtitle'>AI Chatbots, SaaS & Automation Solutions</div>
    <div class='hero-date'>📅 {datetime.now().strftime('%A, %B %d, %Y')} | ⏰ {datetime.now().strftime('%I:%M %p')}</div>
</div>
""", unsafe_allow_html=True)


# ─── KPI Cards ────────────────────────────────────────────────────────────────

col1, col2, col3, col4, col5, col6 = st.columns(6)

kpis = [
    ("📊", str(len(leads)), "Total Leads"),
    ("🔥", str(hot_leads), "Hot Leads"),
    ("💼", str(len(pipeline)), "Pipeline Deals"),
    ("💰", f"₹{pipeline_value/1000:.0f}K" if pipeline_value >= 1000 else f"₹{pipeline_value}", "Pipeline Value"),
    ("👥", str(active_clients), "Active Clients"),
    ("📝", "✅" if content_ready else "❌", "Content Today"),
]

for col, (icon, value, label) in zip([col1, col2, col3, col4, col5, col6], kpis):
    with col:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-icon'>{icon}</div>
            <div class='stat-value'>{value}</div>
            <div class='stat-label'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─── Quick Navigation ────────────────────────────────────────────────────────

st.markdown("<div class='section-title'>⚡ Quick Navigation</div>", unsafe_allow_html=True)

pages = [
    ("📅", "Daily Ops", "Content & leads overview"),
    ("👥", "Leads", "Lead management"),
    ("📝", "Content", "Content library"),
    ("📊", "Pipeline", "Sales pipeline"),
    ("📈", "Analytics", "Performance metrics"),
    ("🤖", "AI Assistant", "Chat with AI"),
    ("💰", "Revenue", "Track finances"),
    ("👤", "Clients", "Client management"),
    ("⚙️", "Settings", "Configuration"),
]

cols = st.columns(len(pages))
for col, (icon, title, desc) in zip(cols, pages):
    with col:
        st.markdown(f"""
        <div class='quick-nav-card'>
            <div class='icon'>{icon}</div>
            <div class='title'>{title}</div>
            <div class='desc'>{desc}</div>
        </div>
        """, unsafe_allow_html=True)


st.markdown("<br>", unsafe_allow_html=True)


# ─── Two Columns: Activity + Top Leads ───────────────────────────────────────

col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("<div class='section-title'>🔔 Recent Activity</div>", unsafe_allow_html=True)

    # Build activity feed from various sources
    activities = []

    # Recent leads
    for lead in sorted(leads, key=lambda x: x.get("extracted_at", ""), reverse=True)[:3]:
        activities.append({
            "icon": "🟢",
            "text": f"New lead: {lead.get('title', '')[:50]}...",
            "time": lead.get("extracted_at", "")[:16].replace("T", " "),
            "color": "#10b981"
        })

    # Recent pipeline deals
    for deal in sorted(pipeline, key=lambda x: x.get("created_at", ""), reverse=True)[:2]:
        activities.append({
            "icon": "🔵",
            "text": f"Deal: {deal.get('name', '')[:50]}",
            "time": deal.get("created_at", "")[:16].replace("T", " "),
            "color": "#667eea"
        })

    # Content status
    if content_ready:
        activities.append({
            "icon": "🟣",
            "text": "Today's content generated ✅",
            "time": datetime.now().strftime("%Y-%m-%d"),
            "color": "#764ba2"
        })

    if activities:
        for act in activities[:6]:
            st.markdown(f"""
            <div class='activity-item'>
                <div class='activity-dot' style='background: {act["color"]};'></div>
                <div>
                    <div style='font-size:0.85rem;'>{act["text"]}</div>
                    <div style='font-size:0.7rem;color:#999;'>{act["time"]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent activity. Start by scraping leads or generating content!")


with col_right:
    st.markdown("<div class='section-title'>🏆 Top Leads</div>", unsafe_allow_html=True)

    top_leads = sorted(leads, key=lambda x: x.get("score", 0), reverse=True)[:5]
    if top_leads:
        for lead in top_leads:
            score = lead.get("score", 0)
            color = "#10b981" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;align-items:center;padding:0.5rem 0;border-bottom:1px solid #f0f0f5;'>
                <div>
                    <div style='font-size:0.85rem;font-weight:500;'>{lead.get('title','')[:55]}...</div>
                    <div style='font-size:0.7rem;color:#999;'>{lead.get('platform','')} | {lead.get('status','')}</div>
                </div>
                <div style='background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:0.75rem;font-weight:600;'>
                    {score}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No leads yet. Go to Leads page to scrape Reddit!")


# ─── Footer ───────────────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#999;font-size:0.75rem;'>"
    "Built with ❤️ by RAGSPRO | <a href='https://ragspro.com' style='color:#667eea;'>ragspro.com</a>"
    "</div>",
    unsafe_allow_html=True
)
