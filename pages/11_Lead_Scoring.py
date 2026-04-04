"""
AI Lead Scoring - Score and prioritize leads with AI
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import sys

ENGINE_DIR = Path(__file__).parent.parent / "engine"
sys.path.insert(0, str(ENGINE_DIR))

from ai_lead_scoring import AILeadScorer, RuleBasedLeadScorer

st.set_page_config(page_title="RAGSPRO - AI Lead Scoring", page_icon="🎯", layout="wide")

DATA_DIR = Path(__file__).parent.parent / "data"
LEADS_FILE = DATA_DIR / "leads.json"

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
.score-hot { background: linear-gradient(135deg, #ff6b6b, #ee5a5a); color: white; }
.score-warm { background: linear-gradient(135deg, #feca57, #ff9f43); color: white; }
.score-cold { background: linear-gradient(135deg, #74b9ff, #0984e3); color: white; }

.score-badge {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.9rem;
}

.lead-card {
    background: white;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    border-left: 4px solid;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.lead-card.hot { border-left-color: #ff6b6b; }
.lead-card.warm { border-left-color: #feca57; }
.lead-card.cold { border-left-color: #74b9ff; }

.metric-box {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.metric-box .value {
    font-size: 2rem;
    font-weight: 800;
}

.metric-box .label {
    font-size: 0.8rem;
    color: #6b7280;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ─── Load Data ────────────────────────────────────────────────────────────────

def load_leads():
    if LEADS_FILE.exists():
        with open(LEADS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_leads(leads):
    with open(LEADS_FILE, 'w') as f:
        json.dump(leads, f, indent=2)

# ─── Header ───────────────────────────────────────────────────────────────────

st.title("🎯 AI Lead Scoring")
st.caption("Score and prioritize leads with AI-powered analysis")

# ─── Initialize Scorer ────────────────────────────────────────────────────────

@st.cache_resource
def get_scorer():
    try:
        return AILeadScorer()
    except:
        return RuleBasedLeadScorer()

scorer = get_scorer()

# ─── Load & Score Leads ─────────────────────────────────────────────────────────

leads = load_leads()

# Score unscored leads
scored_count = 0
for lead in leads:
    if "ai_score" not in lead:
        try:
            if isinstance(scorer, AILeadScorer):
                score_result = scorer.score_lead(lead)
                lead["ai_score"] = {
                    "overall": score_result.overall_score,
                    "priority": score_result.priority,
                    "reasoning": score_result.reasoning,
                    "estimated_value": score_result.estimated_deal_value,
                    "scored_at": datetime.now().isoformat()
                }
            else:
                score = scorer.score_lead(lead)
                lead["ai_score"] = score
            scored_count += 1
        except Exception as e:
            lead["ai_score"] = {"overall": 50, "priority": "cold", "error": str(e)}

if scored_count > 0:
    save_leads(leads)
    st.success(f"✅ Scored {scored_count} new leads!")

# Sort by score
leads.sort(key=lambda x: x.get("ai_score", {}).get("overall", 0), reverse=True)

# ─── Dashboard Metrics ──────────────────────────────────────────────────────────

st.subheader("📊 Scoring Overview")

hot_leads = [l for l in leads if l.get("ai_score", {}).get("priority") == "hot"]
warm_leads = [l for l in leads if l.get("ai_score", {}).get("priority") == "warm"]
cold_leads = [l for l in leads if l.get("ai_score", {}).get("priority") == "cold"]

pipeline_value = sum(l.get("ai_score", {}).get("estimated_value", 0) for l in hot_leads + warm_leads)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class='metric-box'>
        <div class='value'>{len(leads)}</div>
        <div class='label'>Total Leads</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='metric-box'>
        <div class='value' style='color: #ff6b6b;'>{len(hot_leads)}</div>
        <div class='label'>🔥 Hot Leads</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='metric-box'>
        <div class='value' style='color: #feca57;'>{len(warm_leads)}</div>
        <div class='label'>🌤️ Warm Leads</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='metric-box'>
        <div class='value' style='color: #74b9ff;'>{len(cold_leads)}</div>
        <div class='label'>❄️ Cold Leads</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class='metric-box'>
        <div class='value' style='color: #10b981;'>₹{pipeline_value:,}</div>
        <div class='label'>Pipeline Value</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─── Lead Scoring Interface ─────────────────────────────────────────────────────

tab_hot, tab_warm, tab_cold, tab_all = st.tabs(["🔥 Hot Leads", "🌤️ Warm Leads", "❄️ Cold Leads", "📋 All Leads"])

def display_leads(leads_to_show, priority_filter):
    if not leads_to_show:
        st.info(f"No {priority_filter} leads found")
        return

    for lead in leads_to_show:
        score = lead.get("ai_score", {})
        overall = score.get("overall", 0)
        priority = score.get("priority", "cold")
        reasoning = score.get("reasoning", "")

        # Determine card class
        card_class = priority

        # Score color
        if overall >= 75:
            score_class = "score-hot"
        elif overall >= 50:
            score_class = "score-warm"
        else:
            score_class = "score-cold"

        with st.container():
            st.markdown(f"""
            <div class='lead-card {card_class}'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <strong>{lead.get('title', 'Untitled')[:60]}</strong>
                        <span class='score-badge {score_class}'>{overall}/100</span>
                    </div>
                    <span style='color: #6b7280; font-size: 0.85rem;'>{lead.get('platform', 'Unknown')}</span>
                </div>
                <div style='color: #6b7280; font-size: 0.85rem; margin-top: 0.5rem;'>
                    💰 Est. Value: ₹{score.get('estimated_value', 0):,} | 📅 {lead.get('posted_at', 'Unknown')[:10]}
                </div>
                {f"<div style='margin-top: 0.5rem; color: #4b5563; font-size: 0.9rem;'><em>🤖 {reasoning}</em></div>" if reasoning else ""}
            </div>
            """, unsafe_allow_html=True)

            # Actions
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("📧 Outreach", key=f"outreach_{lead.get('id')}"):
                    st.session_state["selected_lead"] = lead
                    st.switch_page("pages/2_Leads.py")
            with col2:
                if st.button("📝 Proposal", key=f"proposal_{lead.get('id')}"):
                    st.session_state["proposal_lead"] = lead
                    st.switch_page("pages/12_Proposals.py")

with tab_hot:
    display_leads(hot_leads, "hot")

with tab_warm:
    display_leads(warm_leads, "warm")

with tab_cold:
    display_leads(cold_leads, "cold")

with tab_all:
    # Filter controls
    filter_col1, filter_col2 = st.columns([1, 3])
    with filter_col1:
        min_score = st.slider("Min Score", 0, 100, 0)
    with filter_col2:
        search = st.text_input("🔍 Search leads", placeholder="Search by title...")

    filtered = [l for l in leads if l.get("ai_score", {}).get("overall", 0) >= min_score]
    if search:
        filtered = [l for l in filtered if search.lower() in l.get("title", "").lower()]

    display_leads(filtered, "")

st.divider()

# ─── Batch Scoring ──────────────────────────────────────────────────────────────

st.subheader("🔄 Batch Operations")

batch_col1, batch_col2 = st.columns(2)

with batch_col1:
    if st.button("🎯 Rescore All Leads", use_container_width=True, type="primary"):
        with st.spinner("Scoring leads..."):
            for lead in leads:
                try:
                    if isinstance(scorer, AILeadScorer):
                        score_result = scorer.score_lead(lead)
                        lead["ai_score"] = {
                            "overall": score_result.overall_score,
                            "priority": score_result.priority,
                            "reasoning": score_result.reasoning,
                            "estimated_value": score_result.estimated_deal_value,
                            "scored_at": datetime.now().isoformat()
                        }
                    else:
                        score = scorer.score_lead(lead)
                        lead["ai_score"] = score
                except Exception as e:
                    st.error(f"Error scoring {lead.get('id')}: {e}")

            save_leads(leads)
            st.success("✅ All leads rescored!")
            st.rerun()

with batch_col2:
    if st.button("📊 Generate Scoring Report", use_container_width=True):
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_leads": len(leads),
            "hot_leads": len(hot_leads),
            "warm_leads": len(warm_leads),
            "cold_leads": len(cold_leads),
            "pipeline_value": pipeline_value,
            "average_score": sum(l.get("ai_score", {}).get("overall", 0) for l in leads) / len(leads) if leads else 0,
            "top_leads": [
                {
                    "id": l.get("id"),
                    "title": l.get("title", "")[:50],
                    "score": l.get("ai_score", {}).get("overall", 0),
                    "priority": l.get("ai_score", {}).get("priority", "cold")
                }
                for l in leads[:10]
            ]
        }

        st.download_button(
            label="📥 Download Report",
            data=json.dumps(report, indent=2),
            file_name=f"lead_scoring_report_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

st.divider()

# ─── Scoring Guide ─────────────────────────────────────────────────────────────

with st.expander("📖 Scoring Guide"):
    st.markdown("""
    ### How Lead Scoring Works

    **AI Scoring (when API key available):**
    - Analyzes lead requirements using LLM
    - Scores on 5 dimensions: Fit, Intent, Engagement, Budget, Timeline
    - Provides reasoning and recommended actions

    **Rule-Based Scoring (fallback):**
    - Keywords analysis for intent detection
    - Budget indicators from requirements
    - Contact availability scoring

    **Priority Levels:**
    - 🔥 **Hot (75-100)**: High intent, good fit - Contact immediately
    - 🌤️ **Warm (50-74)**: Moderate interest - Nurture with content
    - ❄️ **Cold (0-49)**: Low intent - Add to long-term nurture

    **Recommended Actions:**
    - Hot leads: Personal outreach within 24 hours
    - Warm leads: Send case studies and resources
    - Cold leads: Add to email sequences
    """)
