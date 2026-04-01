"""
RAGSPRO Pipeline — Uses CRMSystem class
"""

import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add engine to path
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
from crm_system import CRMSystem

st.set_page_config(page_title="RAGSPRO - Pipeline", page_icon="💼", layout="wide")

# ─── Init CRM ───
crm = CRMSystem()

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


st.title("💼 Sales Pipeline")

# ─── Load Data ───
deals = crm.deals
clients = crm.clients

# ─── Stats ───
forecast = crm.get_revenue_forecast()

st.markdown("### 📊 Pipeline Overview")
cols = st.columns(5)
with cols[0]:
 st.metric("Total Deals", len(deals))
with cols[1]:
 st.metric("Pipeline Value", format_inr(forecast['total_pipeline']))
with cols[2]:
 st.metric("Weighted Forecast", format_inr(forecast['weighted_forecast']))
with cols[3]:
 won = len([d for d in deals if d.get("status") == "won"])
 st.metric("Won Deals", won)
with cols[4]:
 st.metric("Monthly Target", f"₹{forecast['target']:,}")

# Progress to target
progress_pct = min(forecast['progress'], 100)
st.progress(progress_pct / 100)
st.caption(f"Progress: {progress_pct:.1f}% (₹{forecast['won_revenue']:,} / ₹{forecast['target']:,})")

# ─── Add New Deal ───
st.divider()
with st.expander("➕ Add New Deal"):
 col1, col2, col3 = st.columns([2, 2, 1])

 with col1:
  # Client selector
  client_options = {c.get("id"): f"{c.get('name', 'Unknown')} ({c.get('email', 'N/A')})" for c in clients}
  if client_options:
   client_id = st.selectbox("Select Client", options=list(client_options.keys()), format_func=lambda x: client_options.get(x, x))
  else:
   st.warning("No clients found. Go to Clients page to add clients first.")
   client_id = None

 with col2:
  deal_title = st.text_input("Deal Title", placeholder="e.g. AI Chatbot Project")

 with col3:
  deal_value = st.number_input("Value (₹)", min_value=0, step=5000, value=25000)

 service = st.selectbox("Service Type", ["AI Chatbot", "Automation", "Web Development", "SaaS MVP", "Lead Scraper", "Consulting", "Other"])

 if st.button("Add Deal", use_container_width=True, type="primary"):
  if client_id and deal_title:
   deal = crm.add_deal(client_id, deal_title, deal_value, service)
   st.success(f"✅ Deal '{deal_title}' added!")
   st.rerun()
  else:
   st.error("Please select a client and enter deal title")

# ─── Pipeline Board ───
st.divider()
st.subheader("📋 Pipeline Board")

if deals:
 st.markdown("<div class='pipeline-board'>", unsafe_allow_html=True)

 # Define stages
 stages = [
  ("new", "Lead", "#9ca3af"),
  ("proposal_sent", "Proposal Sent", "#3b82f6"),
  ("negotiating", "Negotiating", "#f59e0b"),
  ("won", "Won", "#10b981"),
  ("lost", "Lost", "#ef4444")
 ]

 cols = st.columns(len(stages))

 for i, (stage_key, stage_label, color) in enumerate(stages):
  stage_deals = [d for d in deals if d.get("status") == stage_key]
  stage_value = sum(d.get("value", 0) for d in stage_deals)

  with cols[i]:
   st.markdown(f"""
   <div class='pipeline-col'>
    <div class='col-header'>
     <span style='color:{color}'>{stage_label}</span>
     <span style='color:#666; font-size:0.75rem; background:#eef2ff; padding:2px 6px; border-radius:10px;'>
     {len(stage_deals)} • {format_inr(stage_value)}
     </span>
    </div>
   """, unsafe_allow_html=True)

   for deal in stage_deals:
    # Get client name
    client = crm.get_client(deal.get("client_id", ""))
    client_name = client.get("name", "Unknown") if client else "Unknown"

    st.markdown(f"""
    <div class='deal-card'>
     <div class='deal-name'>{deal.get('title', '')}</div>
     <div class='deal-value'>{format_inr(deal.get('value', 0))}</div>
     <div style='font-size:0.75rem;color:#666;margin-top:0.25rem'>👤 {client_name}</div>
     <div class='deal-date'>Created: {format_date(deal.get('created_at', ''))}</div>
    </div>
    """, unsafe_allow_html=True)

    # Move deal buttons
    move_cols = st.columns(3)
    if stage_key == "new":
     if move_cols[0].button("→ Proposal", key=f"to_prop_{deal['id']}", use_container_width=True):
      crm.update_deal_status(deal['id'], "proposal_sent")
      st.rerun()
    elif stage_key == "proposal_sent":
     if move_cols[0].button("→ Negotiate", key=f"to_neg_{deal['id']}", use_container_width=True):
      crm.update_deal_status(deal['id'], "negotiating")
      st.rerun()
    elif stage_key == "negotiating":
     if move_cols[0].button("✓ Won", key=f"to_won_{deal['id']}", use_container_width=True, type="primary"):
      crm.update_deal_status(deal['id'], "won")
      st.rerun()
     if move_cols[1].button("✗ Lost", key=f"to_lost_{deal['id']}", use_container_width=True):
      crm.update_deal_status(deal['id'], "lost")
      st.rerun()

   st.markdown("</div>", unsafe_allow_html=True)

 st.markdown("</div>", unsafe_allow_html=True)
else:
 st.info("No deals yet. Add your first deal above!")

# ─── All Deals List ───
st.divider()
st.subheader("📑 All Deals")

if deals:
 # Sort by value descending
 sorted_deals = sorted(deals, key=lambda x: x.get("value", 0), reverse=True)

 for deal in sorted_deals:
  col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])

  client = crm.get_client(deal.get("client_id", ""))
  client_name = client.get("name", "Unknown") if client else "Unknown"

  with col1:
   st.markdown(f"**{deal.get('title', '')}**")
   st.caption(f"👤 {client_name} | 📧 {client.get('email', 'N/A') if client else 'N/A'}")

  with col2:
   st.markdown(f"{format_inr(deal.get('value', 0))}")
   st.caption(f"Service: {deal.get('service', 'General')}")

  with col3:
   status = deal.get("status", "new")
   status_colors = {
    "new": "🔘",
    "proposal_sent": "📧",
    "negotiating": "🤝",
    "won": "✅",
    "lost": "❌"
   }
   st.markdown(f"{status_colors.get(status, '🔘')} {status.replace('_', ' ').title()}")

  with col4:
   prob = deal.get("probability", 20)
   st.markdown(f"🎯 {prob}%")

  with col5:
   if st.button("🗑", key=f"del_{deal['id']}"):
    crm.deals = [d for d in crm.deals if d["id"] != deal["id"]]
    crm.save_deals()
    st.rerun()

  st.markdown("---")
else:
 st.info("No deals found. Add your first deal above! 👆")
