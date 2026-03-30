import streamlit as st
import json
import sys
from datetime import datetime
from pathlib import Path

# Add engine to path
engine_path = Path(__file__).parent.parent / "engine"
sys.path.insert(0, str(engine_path))

from config import (
    DATA_DIR, AGENCY_NAME, get_today_folder,
    get_today_proposals_folder, format_inr
)

st.set_page_config(page_title=f"{AGENCY_NAME} - Daily Ops", layout="wide")

# Custom CSS for minimalistic design
custom_css = """
<style>
    .main { padding: 1rem; }
    .stButton > button {
        width: 100%;
        border-radius: 6px;
        font-weight: 500;
    }
    .post-box {
        background: #fafafa;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .post-content {
        font-size: 0.9rem;
        line-height: 1.6;
        white-space: pre-wrap;
        font-family: system-ui, -apple-system, sans-serif;
    }
    .metric-card {
        background: #fff;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        padding: 0.75rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1a1a1a;
    }
    .metric-label {
        font-size: 0.7rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .checklist-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0;
        border-bottom: 1px solid #eee;
    }
    h1 { font-size: 1.3rem !important; font-weight: 600 !important; margin-bottom: 1rem !important; }
    h2 { font-size: 0.9rem !important; font-weight: 600 !important; color: #333 !important; margin-bottom: 0.75rem !important; }
    h3 { font-size: 0.8rem !important; font-weight: 600 !important; color: #666 !important; margin: 0.5rem 0 !important; }
    .lead-row {
        border-bottom: 1px solid #eee;
        padding: 0.75rem 0;
    }
    .platform-tag {
        display: inline-block;
        font-size: 0.65rem;
        padding: 0.15rem 0.4rem;
        border-radius: 3px;
        background: #f0f0f0;
        color: #666;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Load data
def load_leads():
    leads_file = DATA_DIR / "leads.json"
    if leads_file.exists():
        with open(leads_file, 'r') as f:
            return json.load(f)
    return []

def load_pipeline():
    pipeline_file = DATA_DIR / "pipeline.json"
    if pipeline_file.exists():
        with open(pipeline_file, 'r') as f:
            return json.load(f)
    return []

def load_checklist():
    checklist_file = DATA_DIR / "checklist.json"
    if checklist_file.exists():
        with open(checklist_file, 'r') as f:
            return json.load(f)
    return {}

def save_checklist(checklist):
    checklist_file = DATA_DIR / "checklist.json"
    checklist_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checklist_file, 'w') as f:
        json.dump(checklist, f)

leads = load_leads()
pipeline = load_pipeline()
today = datetime.now().strftime("%Y-%m-%d")
today_folder = get_today_folder()

# Today's date header
st.markdown(f"<h1>{AGENCY_NAME} Daily Ops</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color: #666; font-size: 0.85rem; margin-bottom: 1.5rem;'>📅 {datetime.now().strftime('%A, %B %d, %Y')}</p>", unsafe_allow_html=True)

# Generate Content Button
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
with col_btn1:
    if st.button("📝 Generate Today's Content", use_container_width=True):
        import subprocess
        subprocess.run(["python3", str(engine_path / "content_engine.py")])
        st.rerun()
with col_btn2:
    if st.button("🔍 Refresh Leads", use_container_width=True):
        import subprocess
        subprocess.run(["python3", str(engine_path / "lead_scraper.py")])
        st.rerun()

st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)

# Two columns layout with proper heights
col_left, col_right = st.columns([1, 1])

# LEFT COLUMN - Today's Content
with col_left:
    st.markdown("<h2>Today's Content</h2>", unsafe_allow_html=True)

    if today_folder.exists():
        files = {
            "linkedin.txt": "LinkedIn",
            "twitter.txt": "Twitter",
            "instagram.txt": "Instagram",
            "reel.txt": "Reel Script"
        }

        for filename, label in files.items():
            filepath = today_folder / filename
            if filepath.exists():
                content = filepath.read_text()

                st.markdown(f"<h3>{label}</h3>", unsafe_allow_html=True)

                with st.container():
                    st.markdown(f"<div class='post-content'>{content}</div>", unsafe_allow_html=True)

                    if st.button(f"📋 Copy", key=f"copy_{label}", type="secondary"):
                        st.toast(f"{label} copied to clipboard!", icon="✓")

                st.markdown("<div style='margin: 0.75rem 0;'></div>", unsafe_allow_html=True)
    else:
        st.info("No content generated yet. Click 'Generate Today's Content' above.")

# RIGHT COLUMN - Today's Leads + Pipeline
with col_right:
    # Stats row
    new_leads = len([l for l in leads if l.get("status") == "NEW"])
    pipeline_value = sum([p.get("value", 0) for p in pipeline if isinstance(p.get("value"), (int, float))])

    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{new_leads}</div>
                <div class='metric-label'>New Leads</div>
            </div>
        """, unsafe_allow_html=True)
    with stat2:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{len(leads)}</div>
                <div class='metric-label'>Total</div>
            </div>
        """, unsafe_allow_html=True)
    with stat3:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{format_inr(pipeline_value)}</div>
                <div class='metric-label'>Pipeline</div>
            </div>
        """, unsafe_allow_html=True)
    with stat4:
        closed = len([p for p in pipeline if p.get("stage") == "CLOSED"])
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{closed}</div>
                <div class='metric-label'>Closed</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)

    # Today's Leads Section
    st.markdown("<h2>Top Leads Today</h2>", unsafe_allow_html=True)

    # Sort by score and show top 5
    top_leads = sorted(leads, key=lambda x: x.get("score", 0), reverse=True)[:5]

    if top_leads:
        for lead in top_leads:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    title = lead.get("title", "No title")[:60]
                    st.markdown(f"**{title}...**")
                    st.markdown(f"<span class='platform-tag'>{lead.get('platform', 'Unknown')}</span> Score: {lead.get('score', 0)}", unsafe_allow_html=True)
                with col2:
                    if st.button("Copy 📝", key=f"copy_{lead['id']}", use_container_width=True):
                        st.toast("Proposal copied!", icon="✓")
                    if st.button("Contact ✉️", key=f"contact_{lead['id']}", use_container_width=True):
                        with open(DATA_DIR / "leads.json", 'r') as f:
                            all_leads = json.load(f)
                            for l in all_leads:
                                if l["id"] == lead["id"]:
                                    l["status"] = "CONTACTED"
                                    l["contacted_at"] = datetime.now().isoformat()
                                    break
                        with open(DATA_DIR / "leads.json", 'w') as f:
                            json.dump(all_leads, f, indent=2)
                        st.toast("Marked as contacted!", icon="✓")
                        st.rerun()
            st.markdown("---")
    else:
        st.info("No leads yet. Run 'Refresh Leads' to scrape Reddit.")

    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

    # Daily Checklist
    st.markdown("<h2>Daily Checklist</h2>", unsafe_allow_html=True)

    checklist = load_checklist()
    today_check = checklist.get(today, {})

    items = [
        ("post_linkedin", "Post LinkedIn"),
        ("post_twitter", "Post Twitter"),
        ("proposals_fiverr", "Send 5 Fiverr proposals"),
        ("proposals_upwork", "Send 5 Upwork proposals"),
    ]

    for key, label in items:
        checked = today_check.get(key, False)
        new_val = st.checkbox(label, value=checked, key=f"check_{key}")
        if new_val != checked:
            today_check[key] = new_val
            checklist[today] = today_check
            save_checklist(checklist)
