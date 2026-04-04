"""
Outreach Sequences - Manage automated email sequences
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

ENGINE_DIR = Path(__file__).parent.parent / "engine"
sys.path.insert(0, str(ENGINE_DIR))

from automated_outreach import AutomatedOutreachEngine, SequenceStepType, SequenceStatus

st.set_page_config(page_title="RAGSPRO - Outreach Sequences", page_icon="📧", layout="wide")

DATA_DIR = Path(__file__).parent.parent / "data"
LEADS_FILE = DATA_DIR / "leads.json"

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
.sequence-card {
    background: white;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.sequence-card.active {
    border-left: 4px solid #10b981;
}

.sequence-card.paused {
    border-left: 4px solid #f59e0b;
}

.step-item {
    background: #f8fafc;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
    border: 1px solid #e2e8f0;
}

.step-item.email { border-left: 3px solid #3b82f6; }
.step-item.wait { border-left: 3px solid #6b7280; }
.step-item.condition { border-left: 3px solid #8b5cf6; }

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.status-active { background: #d1fae5; color: #059669; }
.status-paused { background: #fef3c7; color: #d97706; }
.status-completed { background: #dbeafe; color: #2563eb; }

.enrollment-card {
    background: white;
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border: 1px solid #e5e7eb;
}

.progress-bar {
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    border-radius: 4px;
    transition: width 0.3s;
}
</style>
""", unsafe_allow_html=True)

# ─── Initialize Engine ────────────────────────────────────────────────────────

@st.cache_resource
def get_engine():
    return AutomatedOutreachEngine()

engine = get_engine()

# ─── Load Data ──────────────────────────────────────────────────────────────────

def load_leads():
    if LEADS_FILE.exists():
        with open(LEADS_FILE, 'r') as f:
            return json.load(f)
    return []

# ─── Header ─────────────────────────────────────────────────────────────────────

st.title("📧 Outreach Sequences")
st.caption("Create and manage automated email sequences")

# ─── Main Tabs ────────────────────────────────────────────────────────────────────

tab_sequences, tab_create, tab_enrollments, tab_analytics = st.tabs([
    "📋 Sequences", "➕ Create Sequence", "👥 Enrollments", "📊 Analytics"
])

# ─── SEQUENCES TAB ────────────────────────────────────────────────────────────────

with tab_sequences:
    sequences = engine.get_sequences()

    if not sequences:
        st.info("No sequences yet. Create your first sequence!")

        # Create default sequences
        if st.button("✨ Create Default Sequences", type="primary"):
            with st.spinner("Creating sequences..."):
                engine.create_default_sequences()
                st.success("✅ Default sequences created!")
                st.rerun()
    else:
        st.subheader(f"Your Sequences ({len(sequences)})")

        for seq in sequences:
            status_class = seq.status

            with st.container():
                st.markdown(f"""
                <div class='sequence-card {status_class}'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <strong style='font-size: 1.1rem;'>{seq.name}</strong>
                            <span class='status-badge status-{seq.status}'>{seq.status}</span>
                        </div>
                        <span style='color: #6b7280; font-size: 0.85rem;'>🎯 {seq.target_segment}</span>
                    </div>
                    <div style='color: #6b7280; font-size: 0.9rem; margin-top: 0.5rem;'>
                        {seq.description}
                    </div>
                    <div style='margin-top: 0.75rem; color: #6b7280; font-size: 0.85rem;'>
                        📧 {len(seq.steps)} steps | 📊 {seq.stats.get('enrolled', 0)} enrolled | ✅ {seq.stats.get('completed', 0)} completed
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Actions
                col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

                with col1:
                    if seq.status == "active":
                        if st.button("⏸️ Pause", key=f"pause_{seq.id}"):
                            # Update sequence status
                            sequences_data = engine._load_sequences()
                            if seq.id in sequences_data:
                                sequences_data[seq.id]["status"] = "paused"
                                engine._save_sequences(sequences_data)
                                st.rerun()
                    else:
                        if st.button("▶️ Activate", key=f"activate_{seq.id}"):
                            sequences_data = engine._load_sequences()
                            if seq.id in sequences_data:
                                sequences_data[seq.id]["status"] = "active"
                                engine._save_sequences(sequences_data)
                                st.rerun()

                with col2:
                    if st.button("👁️ View", key=f"view_{seq.id}"):
                        st.session_state["view_sequence"] = seq.id

                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{seq.id}"):
                        engine.delete_workflow(seq.id)
                        st.rerun()

                # Show steps if viewing
                if st.session_state.get("view_sequence") == seq.id:
                    st.divider()
                    st.subheader("Sequence Steps")

                    for i, step in enumerate(seq.steps):
                        step_type = step.get("step_type", "email")
                        step_name = step.get("name", f"Step {i+1}")

                        st.markdown(f"""
                        <div class='step-item {step_type}'>
                            <div style='display: flex; justify-content: space-between;'>
                                <strong>Step {i+1}: {step_name}</strong>
                                <span style='color: #6b7280;'>⏱️ +{step.get('delay_days', 0)} days</span>
                            </div>
                            <div style='color: #6b7280; font-size: 0.85rem; margin-top: 0.25rem;'>
                                Type: {step_type.upper()}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if step_type == "email":
                            config = step.get("config", {})
                            with st.expander("View Email Template"):
                                st.text_input("Subject", value=config.get("subject", ""), disabled=True, key=f"sub_{seq.id}_{i}")
                                st.text_area("Template", value=config.get("template", ""), disabled=True, height=200, key=f"tpl_{seq.id}_{i}")

# ─── CREATE SEQUENCE TAB ─────────────────────────────────────────────────────────

with tab_create:
    st.subheader("➕ Create New Sequence")

    with st.form("create_sequence"):
        seq_name = st.text_input("Sequence Name", placeholder="e.g., Hot Leads - Fast Track")
        seq_desc = st.text_area("Description", placeholder="What this sequence is for...")
        seq_target = st.selectbox("Target Segment", ["hot", "warm", "cold", "all"])

        st.divider()
        st.write("### Step 1: Initial Email")

        step1_delay = st.number_input("Delay (days)", min_value=0, value=0, key="step1_delay")
        step1_subject = st.text_input("Email Subject", placeholder="e.g., Quick question about {{title}}", key="step1_subject")
        step1_template = st.text_area("Email Template", placeholder="""Hi {{name}},

I saw your post about {{title}} and wanted to reach out...

[Your message here]

Best,
Raghav""", height=200, key="step1_template")

        st.divider()
        st.write("### Step 2: Follow-up")

        step2_delay = st.number_input("Delay after Step 1 (days)", min_value=1, value=2, key="step2_delay")
        step2_subject = st.text_input("Follow-up Subject", placeholder="e.g., Following up: {{title}}", key="step2_subject")
        step2_template = st.text_area("Follow-up Template", placeholder="""Hi {{name}},

Just following up on my previous email...

[Your follow-up message]

Raghav""", height=200, key="step2_template")

        submitted = st.form_submit_button("✅ Create Sequence", type="primary", use_container_width=True)

        if submitted and seq_name:
            try:
                # Create sequence
                sequence = engine.create_sequence(seq_name, seq_desc, seq_target)

                # Add steps
                engine.add_step(
                    sequence_id=sequence.id,
                    name="Initial Outreach",
                    step_type="email",
                    config={"subject": step1_subject, "template": step1_template},
                    delay_days=step1_delay
                )

                engine.add_step(
                    sequence_id=sequence.id,
                    name="Follow-up",
                    step_type="email",
                    config={"subject": step2_subject, "template": step2_template},
                    delay_days=step2_delay
                )

                st.success(f"✅ Sequence '{seq_name}' created with 2 steps!")
                st.rerun()
            except Exception as e:
                st.error(f"Error creating sequence: {e}")

# ─── ENROLLMENTS TAB ─────────────────────────────────────────────────────────────

with tab_enrollments:
    st.subheader("👥 Manage Enrollments")

    leads = load_leads()
    sequences = engine.get_sequences()

    if not sequences:
        st.warning("Create a sequence first!")
    elif not leads:
        st.warning("No leads available. Scrape some leads first!")
    else:
        # Enrollment form
        with st.form("enroll_leads"):
            st.write("### Enroll Leads in Sequence")

            col1, col2 = st.columns(2)

            with col1:
                selected_sequence = st.selectbox(
                    "Select Sequence",
                    options=[s.name for s in sequences],
                    key="enroll_seq"
                )

            with col2:
                # Filter leads by status
                lead_status = st.selectbox(
                    "Filter Leads",
                    ["All", "NEW", "CONTACTED"],
                    key="enroll_filter"
                )

            # Filter leads
            filtered_leads = leads
            if lead_status != "All":
                filtered_leads = [l for l in leads if l.get("status") == lead_status]

            # Multi-select leads
            lead_options = {f"{l.get('title', 'Untitled')[:50]}... ({l.get('id', 'unknown')})": l.get('id')
                           for l in filtered_leads[:20]}

            selected_leads = st.multiselect(
                "Select Leads to Enroll",
                options=list(lead_options.keys()),
                key="enroll_leads_select"
            )

            if st.form_submit_button("🚀 Enroll Selected Leads", type="primary", use_container_width=True):
                if selected_leads:
                    sequence = next((s for s in sequences if s.name == selected_sequence), None)
                    if sequence:
                        lead_ids = [lead_options[name] for name in selected_leads]
                        enrollments = engine.enroll_batch(sequence.id, lead_ids)
                        st.success(f"✅ Enrolled {len(enrollments)} leads in '{selected_sequence}'!")
                        st.rerun()

        st.divider()

        # Show active enrollments
        st.subheader("Active Enrollments")

        enrollments = engine._load_enrollments()
        active = [e for e in enrollments.values() if e["status"] == "active"]

        if active:
            for enrollment in active[:20]:  # Show first 20
                lead_id = enrollment["lead_id"]
                lead = next((l for l in leads if l.get("id") == lead_id), None)
                seq = next((s for s in sequences if s.id == enrollment["sequence_id"]), None)

                if lead and seq:
                    progress = (enrollment["current_step"] / len(seq.steps)) * 100 if seq.steps else 0

                    st.markdown(f"""
                    <div class='enrollment-card'>
                        <div style='display: flex; justify-content: space-between;'>
                            <strong>{lead.get('title', 'Untitled')[:40]}...</strong>
                            <span style='color: #6b7280;'>Step {enrollment["current_step"] + 1}/{len(seq.steps)}</span>
                        </div>
                        <div style='color: #6b7280; font-size: 0.85rem; margin: 0.25rem 0;'>
                            Sequence: {seq.name}
                        </div>
                        <div class='progress-bar'>
                            <div class='progress-fill' style='width: {progress}%;'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No active enrollments")

        # Process button
        if st.button("🔄 Process Enrollments (Run Sequence)", use_container_width=True):
            with st.spinner("Processing..."):
                results = engine.process_enrollments()
                st.success(f"✅ Processed: {results['emails_sent']} emails sent, {results['steps_advanced']} steps advanced")

# ─── ANALYTICS TAB ───────────────────────────────────────────────────────────────

with tab_analytics:
    st.subheader("📊 Sequence Analytics")

    stats = engine.get_overall_stats()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Sequences", stats["total_sequences"])

    with col2:
        st.metric("Total Enrollments", stats["total_enrollments"])

    with col3:
        # Calculate conversion
        enrollments = engine._load_enrollments()
        completed = len([e for e in enrollments.values() if e["status"] == "completed"])
        total = len(enrollments)
        rate = (completed / total * 100) if total > 0 else 0
        st.metric("Completion Rate", f"{rate:.1f}%")

    st.divider()

    # Per-sequence stats
    st.subheader("Per-Sequence Performance")

    for seq in sequences:
        seq_stats = engine.get_sequence_stats(seq.id)

        with st.expander(f"📧 {seq.name}"):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Enrolled", seq_stats["total_enrolled"])
            with col2:
                st.metric("Active", seq_stats["active"])
            with col3:
                st.metric("Completed", seq_stats["completed"])
            with col4:
                st.metric("Completion Rate", f"{seq_stats['completion_rate']:.1f}%")

st.divider()

# ─── Quick Tips ─────────────────────────────────────────────────────────────────

with st.expander("💡 Tips for Effective Sequences"):
    st.markdown("""
    ### Best Practices

    **Hot Leads Sequence:**
    - Day 0: Initial outreach (personalized)
    - Day 2: Follow-up with value
    - Day 5: Final follow-up
    - Keep it short and aggressive

    **Warm Leads Sequence:**
    - Day 0: Value-first email (resource/guide)
    - Day 5: Soft pitch
    - Day 12: Final follow-up
    - Focus on education

    **Email Tips:**
    - Use {{name}}, {{title}}, {{company}} for personalization
    - Keep subject lines under 50 characters
    - One clear CTA per email
    - Mobile-friendly formatting

    **Timing:**
    - Tuesday-Thursday get best open rates
    - 9-11 AM and 2-4 PM are optimal
    - Space follow-ups 2-3 days apart
    """)
