"""
Proposal Management - Generate and track proposals
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import sys

ENGINE_DIR = Path(__file__).parent.parent / "engine"
sys.path.insert(0, str(ENGINE_DIR))

from proposal_generator import ProposalGeneratorV2, SERVICES

st.set_page_config(page_title="RAGSPRO - Proposals", page_icon="📄", layout="wide")

DATA_DIR = Path(__file__).parent.parent / "data"
LEADS_FILE = DATA_DIR / "leads.json"

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
.proposal-card {
    background: white;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.proposal-card.draft { border-left: 4px solid #6b7280; }
.proposal-card.sent { border-left: 4px solid #3b82f6; }
.proposal-card.accepted { border-left: 4px solid #10b981; }
.proposal-card.rejected { border-left: 4px solid #ef4444; }

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.status-draft { background: #f3f4f6; color: #6b7280; }
.status-sent { background: #dbeafe; color: #2563eb; }
.status-accepted { background: #d1fae5; color: #059669; }
.status-rejected { background: #fee2e2; color: #dc2626; }

.service-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 0.75rem;
    cursor: pointer;
    transition: transform 0.2s;
}

.service-card:hover {
    transform: translateY(-2px);
}

.service-card h4 {
    margin: 0 0 0.25rem 0;
    font-size: 1.1rem;
}

.service-card p {
    margin: 0;
    opacity: 0.9;
    font-size: 0.85rem;
}

.price-tag {
    background: rgba(255,255,255,0.2);
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.9rem;
}

.section-preview {
    background: #f8fafc;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    border: 1px solid #e2e8f0;
}

.section-preview h5 {
    margin: 0 0 0.5rem 0;
    color: #374151;
    text-transform: uppercase;
    font-size: 0.8rem;
    letter-spacing: 0.05em;
}

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

# ─── Initialize Generator ─────────────────────────────────────────────────────

@st.cache_resource
def get_generator():
    return ProposalGeneratorV2()

generator = get_generator()

# ─── Load Data ──────────────────────────────────────────────────────────────────

def load_leads():
    if LEADS_FILE.exists():
        with open(LEADS_FILE, 'r') as f:
            return json.load(f)
    return []

# ─── Header ─────────────────────────────────────────────────────────────────────

st.title("📄 Proposal Management")
st.caption("Generate AI-powered proposals and track their status")

# ─── Dashboard Stats ────────────────────────────────────────────────────────────

st.subheader("📊 Overview")

stats = generator.get_proposal_stats()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class='metric-box'>
        <div class='value'>{stats['total']}</div>
        <div class='label'>Total Proposals</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='metric-box'>
        <div class='value' style='color: #6b7280;'>{stats['draft']}</div>
        <div class='label'>Drafts</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='metric-box'>
        <div class='value' style='color: #3b82f6;'>{stats['sent']}</div>
        <div class='label'>Sent</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='metric-box'>
        <div class='value' style='color: #10b981;'>{stats['accepted']}</div>
        <div class='label'>Accepted</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    potential = stats.get('potential_value', 0)
    st.markdown(f"""
    <div class='metric-box'>
        <div class='value' style='color: #8b5cf6;'>₹{potential:,.0f}</div>
        <div class='label'>Pipeline Value</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─── Main Tabs ───────────────────────────────────────────────────────────────────

tab_create, tab_proposals, tab_services = st.tabs(["➕ Create Proposal", "📋 My Proposals", "🛠️ Services"])

# ─── CREATE PROPOSAL TAB ───────────────────────────────────────────────────────────

with tab_create:
    st.subheader("➕ Generate New Proposal")

    leads = load_leads()

    if not leads:
        st.warning("No leads available. Scrape some leads first!")
    else:
        # Lead selection
        lead_options = {f"{l.get('title', 'Untitled')[:50]}... ({l.get('id', 'unknown')[:8]})": l
                       for l in leads[:50]}

        selected_lead_name = st.selectbox(
            "Select Lead",
            options=[""] + list(lead_options.keys()),
            key="proposal_lead_select"
        )

        if selected_lead_name:
            selected_lead = lead_options[selected_lead_name]

            st.divider()

            # Service selection
            st.write("### Select Service")

            # Auto-suggest service based on lead
            suggested_service = generator.suggest_service(selected_lead)

            service_col1, service_col2, service_col3 = st.columns(3)

            selected_service = None
            selected_tier = "standard"

            with service_col1:
                for key, service in list(SERVICES.items())[:2]:
                    is_suggested = key == suggested_service
                    border = "2px solid #10b981" if is_suggested else "none"

                    st.markdown(f"""
                    <div style='border: {border}; border-radius: 12px;'>
                        <div class='service-card'>
                            <h4>{'✨ ' if is_suggested else ''}{service['name']}</h4>
                            <p>{service['description']}</p>
                            <div class='price-tag'>₹{service['price']:,}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"Select {service['name']}", key=f"svc_{key}"):
                        st.session_state["selected_service"] = key

            with service_col2:
                for key, service in list(SERVICES.items())[2:4]:
                    is_suggested = key == suggested_service
                    border = "2px solid #10b981" if is_suggested else "none"

                    st.markdown(f"""
                    <div style='border: {border}; border-radius: 12px;'>
                        <div class='service-card'>
                            <h4>{'✨ ' if is_suggested else ''}{service['name']}</h4>
                            <p>{service['description']}</p>
                            <div class='price-tag'>₹{service['price']:,}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"Select {service['name']}", key=f"svc_{key}"):
                        st.session_state["selected_service"] = key

            with service_col3:
                for key, service in list(SERVICES.items())[4:]:
                    is_suggested = key == suggested_service
                    border = "2px solid #10b981" if is_suggested else "none"

                    st.markdown(f"""
                    <div style='border: {border}; border-radius: 12px;'>
                        <div class='service-card'>
                            <h4>{'✨ ' if is_suggested else ''}{service['name']}</h4>
                            <p>{service['description']}</p>
                            <div class='price-tag'>₹{service['price']:,}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"Select {service['name']}", key=f"svc_{key}"):
                        st.session_state["selected_service"] = key

            # Service selection from session
            selected_service = st.session_state.get("selected_service", suggested_service)

            if selected_service:
                st.success(f"✅ Selected: {SERVICES[selected_service]['name']}")

                # Tier selection
                service = SERVICES[selected_service]
                price_range = service['price_range']

                st.write("### Select Tier")

                tier_col1, tier_col2, tier_col3 = st.columns(3)

                with tier_col1:
                    if st.button(f"Basic\n₹{price_range['min']:,}", use_container_width=True):
                        st.session_state["selected_tier"] = "basic"

                with tier_col2:
                    if st.button(f"Standard\n₹{service['price']:,}", use_container_width=True, type="primary"):
                        st.session_state["selected_tier"] = "standard"

                with tier_col3:
                    if st.button(f"Premium\n₹{price_range['max']:,}", use_container_width=True):
                        st.session_state["selected_tier"] = "premium"

                selected_tier = st.session_state.get("selected_tier", "standard")

                st.divider()

                # Generate button
                if st.button("🚀 Generate AI Proposal", type="primary", use_container_width=True):
                    with st.spinner("AI is crafting your proposal..."):
                        try:
                            proposal = generator.generate_proposal(
                                lead=selected_lead,
                                service_type=selected_service,
                                tier=selected_tier
                            )

                            st.success(f"✅ Proposal generated for {proposal.client_name}!")
                            st.session_state["view_proposal_id"] = proposal.id
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error generating proposal: {e}")

# ─── PROPOSALS TAB ───────────────────────────────────────────────────────────────

with tab_proposals:
    st.subheader("📋 All Proposals")

    proposals = generator.get_all_proposals()

    if not proposals:
        st.info("No proposals yet. Create your first proposal!")
    else:
        # Filter
        filter_col1, filter_col2 = st.columns([1, 3])
        with filter_col1:
            status_filter = st.selectbox("Filter by Status", ["All", "draft", "sent", "accepted", "rejected"])

        filtered = proposals
        if status_filter != "All":
            filtered = [p for p in proposals if p.status == status_filter]

        for proposal in filtered:
            status_class = proposal.status

            with st.container():
                st.markdown(f"""
                <div class='proposal-card {status_class}'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <strong style='font-size: 1.1rem;'>{proposal.project_title[:50]}</strong>
                            <span class='status-badge status-{proposal.status}'>{proposal.status}</span>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 1.2rem; font-weight: 700; color: #1f2937;'>
                                ₹{proposal.pricing.get('price', 0):,}
                            </div>
                            <div style='color: #6b7280; font-size: 0.8rem;'>
                                {proposal.timeline}
                            </div>
                        </div>
                    </div>
                    <div style='color: #6b7280; font-size: 0.9rem; margin-top: 0.5rem;'>
                        👤 {proposal.client_name} | 📅 {proposal.created_at[:10]}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Actions
                action_col1, action_col2, action_col3, action_col4 = st.columns([1, 1, 1, 2])

                with action_col1:
                    if st.button("👁️ View", key=f"view_{proposal.id}"):
                        st.session_state["view_proposal_id"] = proposal.id

                with action_col2:
                    if proposal.status == "draft":
                        if st.button("📧 Send", key=f"send_{proposal.id}"):
                            generator.update_proposal_status(proposal.id, "sent")
                            st.success("✅ Marked as sent!")
                            st.rerun()
                    elif proposal.status == "sent":
                        if st.button("✅ Won", key=f"won_{proposal.id}"):
                            generator.update_proposal_status(proposal.id, "accepted")
                            st.success("🎉 Proposal accepted!")
                            st.rerun()

                with action_col3:
                    if proposal.status in ["draft", "sent"]:
                        if st.button("❌ Lost", key=f"lost_{proposal.id}"):
                            generator.update_proposal_status(proposal.id, "rejected")
                            st.rerun()

                with action_col4:
                    if st.button("📥 Export", key=f"export_{proposal.id}"):
                        text = generator.export_proposal_text(proposal)
                        st.download_button(
                            label="Download",
                            data=text,
                            file_name=f"proposal_{proposal.client_name.replace(' ', '_')}.txt",
                            mime="text/plain",
                            key=f"dl_{proposal.id}"
                        )

        # View proposal details
        if st.session_state.get("view_proposal_id"):
            proposal = generator.get_proposal(st.session_state["view_proposal_id"])
            if proposal:
                st.divider()
                st.subheader("📄 Proposal Preview")

                st.markdown(f"""
                ### {proposal.project_title}
                **Client:** {proposal.client_name}
                **Status:** {proposal.status.upper()}
                **Value:** ₹{proposal.pricing.get('price', 0):,} | **Timeline:** {proposal.timeline}
                """)

                for section in sorted(proposal.sections, key=lambda s: s.order):
                    with st.container():
                        st.markdown(f"""
                        <div class='section-preview'>
                            <h5>{section.title}</h5>
                            <div>{section.content}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.divider()

                # Terms
                st.markdown(f"""
                **Terms:** {proposal.terms}

                **Payment:** {proposal.pricing.get('payment_terms', '50% upfront, 50% on completion')}
                """)

                if st.button("🔙 Close Preview"):
                    del st.session_state["view_proposal_id"]
                    st.rerun()

# ─── SERVICES TAB ─────────────────────────────────────────────────────────────────

with tab_services:
    st.subheader("🛠️ Available Services")

    for key, service in SERVICES.items():
        with st.expander(f"{service['name']} - ₹{service['price']:,}"):
            st.markdown(f"""
            ### {service['name']}
            {service['description']}

            **Timeline:** {service['duration']}

            **Deliverables:**
            """)

            for deliverable in service['deliverables']:
                st.markdown(f"- {deliverable}")

            st.markdown(f"""
            **Pricing:**
            - Basic: ₹{service['price_range']['min']:,}
            - Standard: ₹{service['price']:,}
            - Premium: ₹{service['price_range']['max']:,}
            """)

st.divider()

# ─── Tips ─────────────────────────────────────────────────────────────────────────

with st.expander("💡 Proposal Tips"):
    st.markdown("""
    ### Writing Winning Proposals

    **1. Personalize**
    - Use lead's specific requirements
    - Reference their project title
    - Show you understand their needs

    **2. Be Clear**
    - One-page proposals perform best
    - Use bullet points for deliverables
    - Include exact timeline

    **3. Pricing Strategy**
    - Start with Standard tier
    - Offer 3 options (Basic/Standard/Premium)
    - Include payment terms upfront

    **4. Follow-up**
    - Send proposal within 24 hours
    - Follow up after 3 days
    - Track acceptance rates

    **Conversion Tips:**
    - Hot leads: ₹25K-50K range
    - Warm leads: ₹15K-35K range
    - Always include next steps
    """)
