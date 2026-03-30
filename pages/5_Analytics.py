import streamlit as st
import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
import pandas as pd
import sys
import csv
import io

st.set_page_config(page_title="RAGSPRO - Analytics", layout="wide")

DATA_DIR = Path(__file__).parent.parent / "data"
CONTENT_DIR = DATA_DIR / "content"

st.title("📊 Analytics Dashboard")

def load_data():
    leads_file = DATA_DIR / "leads.json"
    pipeline_file = DATA_DIR / "pipeline.json"

    leads = []
    pipeline = []

    if leads_file.exists():
        with open(leads_file, 'r') as f:
            leads = json.load(f)

    if pipeline_file.exists():
        with open(pipeline_file, 'r') as f:
            pipeline = json.load(f)

    return leads, pipeline

def get_content_days():
    if CONTENT_DIR.exists():
        return len([d for d in CONTENT_DIR.iterdir() if d.is_dir()])
    return 0

def get_outreach_stats():
    sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
    try:
        from outreach_engine import get_outreach_stats as get_stats
        return get_stats()
    except:
        return {"total_sent": 0, "emails_sent": 0, "linkedin_dms": 0, "replied": 0}

leads, pipeline = load_data()
outreach_stats = get_outreach_stats()

# KPI Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    new_leads_7d = len([l for l in leads if (datetime.now() - datetime.fromisoformat(l.get("extracted_at", "2020-01-01"))).days <= 7])
    st.metric("Leads (7 days)", new_leads_7d)

with col2:
    total_leads = len(leads)
    st.metric("Total Leads", total_leads)

with col3:
    content_days = get_content_days()
    st.metric("Content Days", content_days)

with col4:
    pipeline_value = sum(p.get("value", 0) for p in pipeline)
    st.metric("Pipeline Value", f"₹{pipeline_value:,}")

st.divider()

# ─── Conversion Funnel ───────────────────────────────────────────────────────────

st.subheader("📈 Conversion Funnel")

funnel_cols = st.columns(5)
status_order = ["NEW", "CONTACTED", "REPLIED", "PROPOSAL_SENT", "CLOSED"]
funnel_icons = ["👀", "📧", "💬", "📄", "✅"]

for idx, (status, icon) in enumerate(zip(status_order, funnel_icons)):
    count = len([l for l in leads if l.get("status") == status])
    with funnel_cols[idx]:
        st.markdown(f"""
        <div style="text-align:center;padding:1rem;background:#f8f9ff;border-radius:8px;">
            <div style="font-size:2rem;">{icon}</div>
            <div style="font-size:1.5rem;font-weight:700;">{count}</div>
            <div style="font-size:0.8rem;color:#666;">{status}</div>
        </div>
        """, unsafe_allow_html=True)

# Conversion rates
if leads:
    total = len(leads)
    contacted = len([l for l in leads if l.get("status") in ["CONTACTED", "REPLIED", "PROPOSAL_SENT", "CLOSED"]])
    replied = len([l for l in leads if l.get("status") in ["REPLIED", "PROPOSAL_SENT", "CLOSED"]])
    closed = len([l for l in leads if l.get("status") == "CLOSED"])

    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        rate = (contacted / total * 100) if total > 0 else 0
        st.metric("Contact → Reply Rate", f"{rate:.1f}%")
    with col_c2:
        rate = (replied / contacted * 100) if contacted > 0 else 0
        st.metric("Reply → Close Rate", f"{rate:.1f}%")
    with col_c3:
        rate = (closed / total * 100) if total > 0 else 0
        st.metric("Overall Conversion", f"{rate:.1f}%")

st.divider()

# ─── Outreach Performance ─────────────────────────────────────────────────────

st.subheader("📧 Outreach Performance")

out_cols = st.columns(4)
with out_cols[0]:
    st.metric("Total Sent", outreach_stats.get("total_sent", 0))
with out_cols[1]:
    st.metric("Emails", outreach_stats.get("emails_sent", 0))
with out_cols[2]:
    st.metric("LinkedIn DMs", outreach_stats.get("linkedin_dms", 0))
with out_cols[3]:
    total = outreach_stats.get("total_sent", 1)
    replied = outreach_stats.get("replied", 0)
    st.metric("Response Rate", f"{(replied / total * 100):.1f}%")

st.divider()

# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Leads by Platform")
    if leads:
        platforms = defaultdict(int)
        for lead in leads:
            platforms[lead.get("platform", "Unknown")] += 1

        df = pd.DataFrame([(k, v) for k, v in platforms.items()], columns=["Platform", "Count"])
        st.bar_chart(df.set_index("Platform"))
    else:
        st.info("No lead data yet")

with col2:
    st.subheader("Leads by Score")
    if leads:
        score_ranges = {"90-100": 0, "70-89": 0, "50-69": 0, "Below 50": 0}
        for lead in leads:
            s = lead.get("score", 0)
            if s >= 90:
                score_ranges["90-100"] += 1
            elif s >= 70:
                score_ranges["70-89"] += 1
            elif s >= 50:
                score_ranges["50-69"] += 1
            else:
                score_ranges["Below 50"] += 1

        df = pd.DataFrame([(k, v) for k, v in score_ranges.items()], columns=["Score Range", "Count"])
        st.bar_chart(df.set_index("Score Range"))
    else:
        st.info("No lead data yet")

st.divider()

# Pipeline stages
st.subheader("Pipeline by Stage")
if pipeline:
    stages = defaultdict(lambda: {"count": 0, "value": 0})
    for deal in pipeline:
        stage = deal.get("stage", "NEW")
        stages[stage]["count"] += 1
        stages[stage]["value"] += deal.get("value", 0)

    cols = st.columns(len(stages))
    for i, (stage, data) in enumerate(stages.items()):
        with cols[i]:
            st.markdown(f"**{stage}**")
            st.metric("Deals", data["count"])
            st.metric("Value", f"₹{data['value']:,}")
else:
    st.info("No pipeline data yet")

st.divider()

# ─── Export Reports ───────────────────────────────────────────────────────────

st.subheader("📥 Export Reports")

col_e1, col_e2, col_e3 = st.columns(3)

with col_e1:
    if st.button("📊 Export Leads (CSV)", use_container_width=True):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Name", "Title", "Platform", "Score", "Status", "Email", "URL", "Extracted At"])

        for lead in leads:
            writer.writerow([
                lead.get("id"),
                lead.get("name"),
                lead.get("title", "")[:100],
                lead.get("platform"),
                lead.get("score"),
                lead.get("status"),
                lead.get("contact", {}).get("email", ""),
                lead.get("url"),
                lead.get("extracted_at", "")[:10]
            ])

        st.download_button(
            label="Download leads.csv",
            data=output.getvalue(),
            file_name=f"ragspro_leads_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

with col_e2:
    if st.button("💰 Export Revenue (CSV)", use_container_width=True):
        revenue_file = DATA_DIR / "revenue.json"
        if revenue_file.exists():
            with open(revenue_file) as f:
                rev_data = json.load(f)

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Date", "Type", "Amount", "Category", "Client", "Description"])

            for entry in rev_data.get("entries", []):
                writer.writerow([
                    entry.get("date"),
                    entry.get("type"),
                    entry.get("amount"),
                    entry.get("category"),
                    entry.get("client"),
                    entry.get("description", "")[:100]
                ])

            st.download_button(
                label="Download revenue.csv",
                data=output.getvalue(),
                file_name=f"ragspro_revenue_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

with col_e3:
    if st.button("📄 Full Report (JSON)", use_container_width=True):
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_leads": len(leads),
                "new_leads_7d": new_leads_7d,
                "pipeline_value": pipeline_value,
                "content_days": content_days
            },
            "leads": leads,
            "pipeline": pipeline
        }

        st.download_button(
            label="Download report.json",
            data=json.dumps(report, indent=2, default=str),
            file_name=f"ragspro_report_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )

st.divider()

# ─── Raw Data ─────────────────────────────────────────────────────────────────

with st.expander("🔍 View Raw Data"):
    tab1, tab2 = st.tabs(["Leads", "Pipeline"])
    with tab1:
        st.json(leads[:5] if leads else [])
    with tab2:
        st.json(pipeline[:5] if pipeline else [])
