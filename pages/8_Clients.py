"""
RAGSPRO Client Management — Uses CRMSystem class
Enhanced with YC Leads, Source Filters, and Smart Actions
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# Add engine to path
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
from crm_system import CRMSystem

st.set_page_config(page_title="RAGSPRO - Clients & CRM", page_icon="👥", layout="wide")

# ─── Init CRM ───
crm = CRMSystem()

# ─── Custom CSS ───
st.markdown("""
<style>
 @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
 .main { font-family: 'Inter', sans-serif; }

 .client-card {
 background: #fff;
 border: 1px solid #e5e7eb;
 border-radius: 12px;
 padding: 1.25rem;
 margin-bottom: 1rem;
 transition: all 0.2s;
 box-shadow: 0 1px 3px rgba(0,0,0,0.04);
 }
 .client-card:hover {
 box-shadow: 0 4px 12px rgba(0,0,0,0.08);
 transform: translateY(-1px);
 }

 .status-lead { color: #f59e0b; font-weight: 600; }
 .status-prospect { color: #3b82f6; font-weight: 600; }
 .status-client { color: #10b981; font-weight: 600; }
 .status-churned { color: #ef4444; font-weight: 600; }

 .source-badge {
 display: inline-block;
 padding: 2px 8px;
 border-radius: 12px;
 font-size: 0.7rem;
 font-weight: 500;
 }
 .source-yc { background: #fef3c7; color: #92400e; }
 .source-reddit { background: #fee2e2; color: #991b1b; }
 .source-linkedin { background: #dbeafe; color: #1e40af; }
 .source-website { background: #d1fae5; color: #065f46; }
 .source-other { background: #f3f4f6; color: #374151; }

 .batch-badge {
 display: inline-block;
 background: linear-gradient(135deg, #f59e0b, #d97706);
 color: white;
 padding: 2px 8px;
 border-radius: 10px;
 font-size: 0.7rem;
 font-weight: 600;
 margin-left: 8px;
 }

 .hiring-badge {
 display: inline-block;
 background: #10b981;
 color: white;
 padding: 2px 8px;
 border-radius: 10px;
 font-size: 0.7rem;
 font-weight: 600;
 margin-left: 8px;
 }

 .contact-link {
 color: #667eea;
 text-decoration: none;
 font-size: 0.85rem;
 }
 .contact-link:hover {
 text-decoration: underline;
 }

 .company-desc {
 color: #4b5563;
 font-size: 0.9rem;
 line-height: 1.5;
 margin: 0.5rem 0;
 }

 .tag-pill {
 display: inline-block;
 background: #eef2ff;
 color: #667eea;
 padding: 3px 10px;
 border-radius: 20px;
 font-size: 0.75rem;
 margin: 2px;
 }
</style>
""", unsafe_allow_html=True)

# ─── Load Data ───
clients = crm.clients
deals = crm.deals

# ─── Helper Functions ───
def get_source_badge(source):
    """Get styled source badge"""
    if not source:
        return '<span class="source-badge source-other">Unknown</span>'

    source_lower = source.lower()
    if 'yc' in source_lower or 'ycombinator' in source_lower:
        batch = source.split('_')[-1] if '_' in source else ''
        return f'<span class="source-badge source-yc">🚀 YC {batch}</span>'
    elif 'reddit' in source_lower:
        return '<span class="source-badge source-reddit">Reddit</span>'
    elif 'linkedin' in source_lower:
        return '<span class="source-badge source-linkedin">LinkedIn</span>'
    elif 'website' in source_lower:
        return '<span class="source-badge source-website">Website</span>'
    else:
        return f'<span class="source-badge source-other">{source}</span>'


def get_status_badge(status):
    """Get styled status badge"""
    status_class = f"status-{status}" if status else "status-lead"
    return f'<span class="{status_class}">{status.title() if status else "Lead"}</span>'


# ─── Main ───
st.title("👥 CRM - Clients & Deals")
st.caption(f"Total contacts: {len(clients)} | Last updated: {datetime.now().strftime('%H:%M')}")

# ─── Stats ───
col1, col2, col3, col4, col5, col6 = st.columns(6)

leads = len([c for c in clients if c.get("status") == "lead"])
prospects = len([c for c in clients if c.get("status") == "prospect"])
active = len([c for c in clients if c.get("status") == "client"])
yc_leads = len([c for c in clients if 'yc' in str(c.get("source", "")).lower()])
hiring = len([c for c in clients if c.get("is_hiring")])
total_deals = len(deals)

forecast = crm.get_revenue_forecast()

with col1:
    st.metric("🎯 Leads", leads, help=f"{yc_leads} from YC")
with col2:
    st.metric("👀 Prospects", prospects)
with col3:
    st.metric("✅ Active", active)
with col4:
    st.metric("💼 Deals", total_deals)
with col5:
    st.metric("💰 Pipeline", f"₹{forecast['total_pipeline']/1000:.0f}K")
with col6:
    st.metric("🔥 Hiring", hiring, delta="YC Only")

st.divider()

# ─── Filters ───
st.subheader("🔍 Filter & Search")

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 1, 1, 1])

with filter_col1:
    search = st.text_input("Search by name, company, or email...", placeholder="e.g. Egress Health", label_visibility="collapsed")

with filter_col2:
    status_filter = st.selectbox("Status", ["All", "lead", "prospect", "client", "churned"], label_visibility="collapsed")

with filter_col3:
    sources = list(set([c.get("source", "Unknown") for c in clients]))
    source_options = ["All Sources"] + sorted([s for s in sources if s])[:10]
    source_filter = st.selectbox("Source", source_options, label_visibility="collapsed")

with filter_col4:
    sort_by = st.selectbox("Sort", ["Newest First", "Oldest First", "Name A-Z", "Score High-Low"], label_visibility="collapsed")

# ─── Apply Filters ───
filtered_clients = clients

if search:
    search_lower = search.lower()
    filtered_clients = [c for c in filtered_clients if
        search_lower in c.get("name", "").lower() or
        search_lower in c.get("company", "").lower() or
        search_lower in c.get("email", "").lower() or
        search_lower in c.get("notes", "").lower()]

if status_filter != "All":
    filtered_clients = [c for c in filtered_clients if c.get("status") == status_filter]

if source_filter != "All Sources":
    filtered_clients = [c for c in filtered_clients if source_filter in str(c.get("source", ""))]

# Sort
if sort_by == "Newest First":
    filtered_clients = sorted(filtered_clients, key=lambda x: x.get("created_at", ""), reverse=True)
elif sort_by == "Oldest First":
    filtered_clients = sorted(filtered_clients, key=lambda x: x.get("created_at", ""))
elif sort_by == "Name A-Z":
    filtered_clients = sorted(filtered_clients, key=lambda x: x.get("name", "").lower())
elif sort_by == "Score High-Low":
    filtered_clients = sorted(filtered_clients, key=lambda x: x.get("yc_score", 0), reverse=True)

st.markdown(f"**{len(filtered_clients)}** contacts found")

# ─── Clients List ───
if filtered_clients:
    for client in filtered_clients:
        client_id = client.get("id", "")
        status = client.get("status", "lead")
        source = client.get("source", "")
        is_hiring = client.get("is_hiring", False)
        batch = client.get("batch", "")

        with st.container():
            # Header row
            col1, col2 = st.columns([4, 1])

            with col1:
                # Name with badges
                header = f"### {client.get('name', 'Unknown')}"
                if batch:
                    header += f' <span class="batch-badge">{batch}</span>'
                if is_hiring:
                    header += ' <span class="hiring-badge">🔥 Hiring</span>'
                st.markdown(header, unsafe_allow_html=True)

                # Source badge
                st.markdown(get_source_badge(source), unsafe_allow_html=True)

                # Company + Status
                st.markdown(f"🏢 **{client.get('company', 'N/A')}** | {get_status_badge(status)}")

                # Contact Links
                contact_cols = st.columns([1, 1, 1, 1])

                with contact_cols[0]:
                    email = client.get('email') or (client.get('all_emails', {}).get('from_description', [])[0] if client.get('all_emails') else None)
                    if email:
                        st.markdown(f"📧 [{email}](mailto:{email})", unsafe_allow_html=True)
                    else:
                        st.caption("📧 No email")

                with contact_cols[1]:
                    website = client.get('company_website') or client.get('website')
                    if website:
                        st.markdown(f"🌐 [Website]({website})", unsafe_allow_html=True)

                with contact_cols[2]:
                    linkedin = client.get('company_linkedin') or client.get('linkedin_company')
                    if linkedin:
                        st.markdown(f"💼 [LinkedIn]({linkedin})", unsafe_allow_html=True)

                with contact_cols[3]:
                    domain = client.get('company_domain') or client.get('domain')
                    if domain:
                        st.markdown(f"🔗 {domain}")

                # Description
                desc = client.get("company_description") or client.get("notes", "")[:200]
                if desc:
                    st.markdown(f"<div class='company-desc'>{desc}</div>", unsafe_allow_html=True)

                # Tags
                tags = client.get("tags", []) or client.get("industry", [])
                if tags:
                    st.markdown(" ".join([f'<span class="tag-pill">{t}</span>' for t in tags[:5]]), unsafe_allow_html=True)

            with col2:
                # Status changer
                new_status = st.selectbox(
                    "Update",
                    ["lead", "prospect", "client", "churned"],
                    index=["lead", "prospect", "client", "churned"].index(status) if status in ["lead", "prospect", "client", "churned"] else 0,
                    key=f"status_{client_id}",
                    label_visibility="collapsed"
                )
                if new_status != status:
                    client["status"] = new_status
                    crm.save_clients()
                    st.rerun()

                # Deals count
                client_deals = [d for d in deals if d.get("client_id") == client_id]
                if client_deals:
                    st.markdown(f"💼 **{len(client_deals)}** deals")
                    total_val = sum(d.get('value', 0) for d in client_deals)
                    st.caption(f"₹{total_val:,}")

                # Quick add deal
                with st.expander("➕ Add Deal"):
                    deal_title = st.text_input("Title", key=f"dt_{client_id}", placeholder="AI Chatbot project")
                    deal_value = st.number_input("Value (₹)", min_value=0, step=5000, value=25000, key=f"dv_{client_id}")
                    if st.button("Add Deal", key=f"ad_{client_id}", use_container_width=True, type="primary"):
                        if deal_title:
                            crm.add_deal(client_id, deal_title, deal_value, "general")
                            st.success("✅ Deal added!")
                            st.rerun()

            st.markdown("---")
else:
    st.info("No contacts found. Try adjusting filters or add new clients! 👆")

# ─── Add New Client ───
st.divider()
with st.expander("➕ Add New Client"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name *", placeholder="e.g. Rahul Sharma")
        email = st.text_input("Email *", placeholder="rahul@company.com")
        phone = st.text_input("Phone", placeholder="+91 98765 43210")
    with col2:
        company = st.text_input("Company", placeholder="Company name")
        source = st.selectbox("Source", ["Website", "Reddit", "LinkedIn", "YC", "Referral", "Cold Email", "Other"])
        tags = st.text_input("Tags (comma separated)", placeholder="saas, ai, urgent")

    if st.button("Add Client", use_container_width=True, type="primary"):
        if name and email:
            client = crm.add_client(
                name=name,
                email=email,
                phone=phone,
                company=company,
                source=source,
                tags=[t.strip() for t in tags.split(",") if t.strip()]
            )
            st.success(f"✅ Client '{name}' added!")
            st.rerun()
        else:
            st.error("Name and email are required")

# ─── Pipeline Section ───
st.divider()
st.subheader("💼 Pipeline View")

pipeline = crm.get_deals_pipeline()

cols = st.columns(5)
stage_names = ["lead", "proposal_sent", "negotiating", "won", "lost"]
stage_labels = ["🆕 Lead", "📧 Proposal", "🤝 Negotiating", "✅ Won", "❌ Lost"]
stage_colors = ["#9ca3af", "#3b82f6", "#f59e0b", "#10b981", "#ef4444"]

for i, (stage, label, color) in enumerate(zip(stage_names, stage_labels, stage_colors)):
    with cols[i]:
        stage_deals = [d for d in deals if d.get("status") == stage]
        stage_value = sum(d.get("value", 0) for d in stage_deals)

        st.markdown(f"""
        <div style='background:{color}15; border:1px solid {color}40; border-radius:8px; padding:0.75rem;'>
            <div style='font-weight:600; color:{color}; font-size:0.9rem;'>{label}</div>
            <div style='font-size:1.5rem; font-weight:700; color:#1a1a2e;'>{len(stage_deals)}</div>
            <div style='font-size:0.75rem; color:#666;'>₹{stage_value/1000:.0f}K</div>
        </div>
        """, unsafe_allow_html=True)

        for deal in sorted(stage_deals, key=lambda x: x.get("value", 0), reverse=True)[:3]:
            client = crm.get_client(deal.get("client_id", ""))
            client_name = client.get("name", "Unknown")[:15] if client else "Unknown"
            st.markdown(f"""
            <div style='background:white; border-left:3px solid {color}; padding:0.5rem; margin:0.25rem 0; border-radius:4px;'>
                <div style='font-size:0.75rem; font-weight:500;'>{deal.get('title', '')[:25]}...</div>
                <div style='font-size:0.7rem; color:#666;'>👤 {client_name} | ₹{deal.get('value', 0):,}</div>
            </div>
            """, unsafe_allow_html=True)

# ─── Revenue Forecast ───
st.divider()
st.subheader("💰 Revenue Forecast")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Won Revenue", f"₹{forecast['won_revenue']:,}")
with col2:
    st.metric("Pipeline Value", f"₹{forecast['total_pipeline']:,}")
with col3:
    st.metric("Weighted Forecast", f"₹{forecast['weighted_forecast']:,}")
with col4:
    st.metric("Monthly Target", f"₹{forecast['target']:,}")

st.progress(min(forecast['progress'] / 100, 1.0))

# ─── Quick Actions ───
st.divider()
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🚀 Import YC Leads", use_container_width=True, type="primary"):
        st.info("Run: `python engine/yc_lead_scraper_v4.py`")

with col2:
    if st.button("🔍 Enrich Emails", use_container_width=True):
        st.info("Add HUNTER_API_KEY to .env for email enrichment")

with col3:
    if st.button("📊 Generate Report", use_container_width=True):
        report = crm.generate_report()
        st.text_area("CRM Report", report, height=200)

with col4:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
