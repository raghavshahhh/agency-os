import streamlit as st
import json
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="RAGSPRO - Pipeline", page_icon="💼", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .main { font-family: 'Inter', sans-serif; }
    
    .pipeline-board {
        display: flex;
        gap: 1rem;
        overflow-x: auto;
        padding-bottom: 1rem;
    }
    
    .pipeline-col {
        flex: 1;
        min-width: 250px;
        background: #f8f9ff;
        border-radius: 8px;
        padding: 0.75rem;
        border: 1px solid #e0e5ff;
    }
    
    .col-header {
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        color: #1a1a2e;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .deal-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-left: 3px solid #667eea;
        border-radius: 6px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        transition: transform 0.1s ease;
    }
    
    .deal-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .deal-name { font-weight: 600; font-size: 0.85rem; margin-bottom: 0.25rem; color: #1a1a2e; }
    .deal-value { color: #10b981; font-weight: 600; font-size: 0.9rem; }
    .deal-date { color: #9ca3af; font-size: 0.7rem; margin-top: 0.4rem; }
</style>
""", unsafe_allow_html=True)

def load_pipeline():
    pipeline_file = Path(__file__).parent.parent / "data" / "pipeline.json"
    if pipeline_file.exists():
        try:
            with open(pipeline_file, 'r') as f:
                data = json.load(f)
                
                # Fix legacy stages if present
                for d in data:
                    stage = d.get("stage", "NEW")
                    if stage == "Proposal":
                        d["stage"] = "PROPOSAL_SENT"
                    elif stage not in ["NEW", "CONTACTED", "REPLIED", "PROPOSAL_SENT", "CLOSED"]:
                        d["stage"] = "NEW"
                
                return data
        except Exception:
            return []
    return []

def save_pipeline(pipeline):
    pipeline_file = Path(__file__).parent.parent / "data" / "pipeline.json"
    pipeline_file.parent.mkdir(parents=True, exist_ok=True)
    with open(pipeline_file, 'w') as f:
        json.dump(pipeline, f, indent=2, default=str)

def format_inr(value):
    if value >= 100000:
        return f"₹{value/100000:.1f}L"
    elif value >= 1000:
        return f"₹{value/1000:.0f}K"
    return f"₹{value}"

def format_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%d %b")
    except:
        return date_str

st.title("Sales Pipeline")

pipeline = load_pipeline()

# Stats
cols = st.columns(5)
stages = ["NEW", "CONTACTED", "REPLIED", "PROPOSAL_SENT", "CLOSED"]
for i, stage in enumerate(stages):
    count = len([d for d in pipeline if d.get("stage") == stage])
    with cols[i]:
        st.metric(stage.replace("_", " "), count)

# Add new deal
st.divider()
st.subheader("Add New Deal")

with st.form("new_deal"):
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        deal_name = st.text_input("Deal Name", placeholder="e.g. Website project for XYZ")
    with col2:
        deal_value = st.number_input("Value (₹)", min_value=0, step=1000, value=0)
    with col3:
        deal_stage = st.selectbox("Stage", stages)

    submitted = st.form_submit_button("Add Deal", use_container_width=True)

    if submitted and deal_name:
        new_deal = {
            "id": f"deal_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": deal_name,
            "value": deal_value,
            "stage": deal_stage,
            "created_at": datetime.now().isoformat()
        }
        pipeline.append(new_deal)
        save_pipeline(pipeline)
        st.success("Deal added!")
        st.rerun()

# Pipeline view
st.divider()
st.subheader("📋 Pipeline Board")

if pipeline:
    st.markdown("<div class='pipeline-board'>", unsafe_allow_html=True)
    cols = st.columns(len(stages))
    for i, stage in enumerate(stages):
        stage_deals = [d for d in pipeline if d.get("stage") == stage]
        stage_val = sum(d.get("value", 0) for d in stage_deals)
        
        with cols[i]:
            st.markdown(f"""
            <div class='pipeline-col'>
                <div class='col-header'>
                    <span>{stage.replace('_', ' ')}</span>
                    <span style='color:#666; font-size:0.75rem; background:#eef2ff; padding:2px 6px; border-radius:10px;'>
                        {len(stage_deals)} • {format_inr(stage_val)}
                    </span>
                </div>
            """, unsafe_allow_html=True)
            
            for deal in stage_deals:
                st.markdown(f"""
                <div class='deal-card'>
                    <div class='deal-name'>{deal.get('name', '')}</div>
                    <div class='deal-value'>{format_inr(deal.get('value', 0))}</div>
                    <div class='deal-date'>Created: {format_date(deal.get('created_at', ''))}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No deals yet. Add your first deal above.")

# Deal list with actions
st.divider()
st.subheader("All Deals")

if pipeline:
    for deal in pipeline:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.markdown(f"**{deal.get('name', '')}**")
            st.caption(f"Created: {format_date(deal.get('created_at', ''))}")
        with col2:
            st.markdown(f"{format_inr(deal.get('value', 0))}")
        with col3:
            new_stage = st.selectbox("Stage", stages, index=stages.index(deal.get("stage", "NEW")), key=f"stage_{deal['id']}", label_visibility="collapsed")
            if new_stage != deal.get("stage"):
                deal["stage"] = new_stage
                save_pipeline(pipeline)
                st.rerun()
        with col4:
            if st.button("Delete", key=f"del_{deal['id']}"):
                pipeline = [d for d in pipeline if d["id"] != deal["id"]]
                save_pipeline(pipeline)
                st.rerun()
        st.markdown("---")
