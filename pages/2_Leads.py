"""
RAGSPRO Leads Management — Full CRM with Outreach, Email Sending, Communication Tracking
"""

import streamlit as st
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ENGINE_DIR = Path(__file__).parent.parent / "engine"
sys.path.insert(0, str(ENGINE_DIR))

from config import DATA_DIR, RESEND_API_KEY, AGENCY_NAME
from outreach_engine import (
    generate_cold_email, generate_cold_email_followup,
    generate_call_script, generate_linkedin_dm,
    send_email_resend, log_outreach,
    get_lead_outreach_history, get_outreach_stats,
    validate_email_format, validate_email_domain, validate_phone,
    parse_email_content
)
from enrichment import enrich_single_lead, get_enrichment_stats

st.set_page_config(page_title=f"{AGENCY_NAME} - Leads CRM", page_icon="👥", layout="wide")

LEADS_FILE = DATA_DIR / "leads.json"

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .main { font-family: 'Inter', sans-serif; }

    .lead-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .score-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        color: white;
    }
    .score-high { background: #10b981; }
    .score-mid { background: #f59e0b; }
    .score-low { background: #ef4444; }

    .status-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.72rem;
        font-weight: 500;
    }
    .status-NEW { background: #dbeafe; color: #1e40af; }
    .status-CONTACTED { background: #fef3c7; color: #92400e; }
    .status-REPLIED { background: #d1fae5; color: #065f46; }
    .status-HOT_LEAD { background: #fee2e2; color: #991b1b; }
    .status-PROPOSAL_SENT { background: #e0e7ff; color: #3730a3; }
    .status-CLOSED { background: #f3f4f6; color: #374151; }

    .contact-verified { color: #10b981; font-weight: 600; }
    .contact-unverified { color: #ef4444; }

    .outreach-timeline {
        border-left: 2px solid #e5e7eb;
        padding-left: 1rem;
        margin-left: 0.5rem;
    }
    .timeline-item {
        position: relative;
        padding-bottom: 0.75rem;
        font-size: 0.82rem;
    }
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -1.25rem;
        top: 0.3rem;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #667eea;
    }
    .timeline-date { color: #9ca3af; font-size: 0.72rem; }

    .kpi-row {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }
    .kpi-card {
        flex: 1;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 0.75rem;
        text-align: center;
    }
    .kpi-value { font-size: 1.5rem; font-weight: 700; color: #1a1a2e; }
    .kpi-label { font-size: 0.7rem; color: #9ca3af; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)


# ─── Data Functions ───────────────────────────────────────────────────────────

def load_leads():
    if LEADS_FILE.exists():
        try:
            with open(LEADS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_leads(leads):
    LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEADS_FILE, 'w') as f:
        json.dump(leads, f, indent=2, default=str)


def get_score_class(score):
    if score >= 70:
        return "score-high"
    elif score >= 40:
        return "score-mid"
    return "score-low"


# ─── Main Page ────────────────────────────────────────────────────────────────

st.title("👥 Leads CRM")

leads = load_leads()
outreach_stats = get_outreach_stats()

# ─── KPI Row ──────────────────────────────────────────────────────────────────

col1, col2, col3, col4, col5, col6 = st.columns(6)
statuses = {"NEW": 0, "CONTACTED": 0, "REPLIED": 0, "HOT_LEAD": 0, "PROPOSAL_SENT": 0, "CLOSED": 0}
for l in leads:
    s = l.get("status", "NEW")
    if s in statuses:
        statuses[s] += 1

# Enrichment stats
enrich_stats = get_enrichment_stats()

with col1:
    st.metric("Total", len(leads))
    st.caption(f"📧 {enrich_stats['leads_with_emails']} with emails")
with col2:
    st.metric("New", statuses["NEW"])
    st.caption(f"✨ {enrich_stats['enriched_leads']} enriched")
with col3:
    st.metric("Contacted", statuses["CONTACTED"])
with col4:
    st.metric("Hot 🔥", statuses["HOT_LEAD"])
with col5:
    st.metric("Emails Sent", outreach_stats["emails_sent"])
with col6:
    st.metric("Replied", outreach_stats["replied"])

st.divider()

# ─── Source Filter Buttons ──────────────────────────────────────────────────────

# Get unique platforms from leads
platforms = sorted(set(l.get("platform", "Unknown") for l in leads))
platform_counts = {p: len([l for l in leads if l.get("platform") == p]) for p in platforms}

st.markdown("##### 📍 Filter by Source")

# Source buttons in columns
source_cols = st.columns(min(len(platforms) + 1, 6))  # Max 6 columns

with source_cols[0]:
    if st.button(f"📊 All ({len(leads)})", use_container_width=True,
                 type="primary" if st.session_state.get("source_filter") == "All" else "secondary"):
        st.session_state.source_filter = "All"
        st.rerun()

for idx, platform in enumerate(platforms[:5], 1):  # Show max 5 platforms
    with source_cols[idx]:
        icon = {"r/forhire": "🔴", "LinkedIn Jobs": "💼", "Manual": "✏️",
                "r/slavelabour": "🔴", "r/startups": "🚀", "r/entrepreneur": "💡"}.get(platform, "📍")
        label = platform if len(platform) < 15 else platform[:12] + "..."
        if st.button(f"{icon} {label} ({platform_counts[platform]})", use_container_width=True,
                     type="primary" if st.session_state.get("source_filter") == platform else "secondary"):
            st.session_state.source_filter = platform
            st.rerun()

if "source_filter" not in st.session_state:
    st.session_state.source_filter = "All"

st.divider()

# ─── Filters & Actions ───────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
with col1:
    status_filter = st.selectbox("Status", ["All", "NEW", "CONTACTED", "REPLIED", "HOT_LEAD", "PROPOSAL_SENT", "CLOSED"])
    contact_filter = st.checkbox("📧 Only with email/phone", value=False)
with col2:
    search = st.text_input("🔍 Search", placeholder="Title, company, platform...")
with col3:
    sort_by = st.selectbox("Sort", ["Score ↓", "Newest", "Oldest"])
with col4:
    if st.button("🔄 Scrape Leads", use_container_width=True):
        with st.spinner("Scraping Reddit for [HIRING] posts..."):
            subprocess.run(["python3", str(ENGINE_DIR / "lead_scraper.py")], capture_output=True)
        st.rerun()

# Filter
filtered = leads
if status_filter != "All":
    filtered = [l for l in filtered if l.get("status") == status_filter]
if contact_filter:
    filtered = [l for l in filtered if l.get("contact", {}).get("email") or l.get("contact", {}).get("phone")]
if search:
    search_lower = search.lower()
    filtered = [l for l in filtered if
        search_lower in l.get("title", "").lower() or
        search_lower in l.get("requirement", "").lower() or
        search_lower in l.get("platform", "").lower() or
        search_lower in l.get("name", "").lower()
    ]

# Sort
if sort_by == "Score ↓":
    filtered = sorted(filtered, key=lambda x: x.get("score", 0), reverse=True)
elif sort_by == "Newest":
    filtered = sorted(filtered, key=lambda x: x.get("extracted_at", ""), reverse=True)
elif sort_by == "Oldest":
    filtered = sorted(filtered, key=lambda x: x.get("extracted_at", ""))

st.caption(f"Showing {len(filtered)} of {len(leads)} leads")

# ─── Pagination ───────────────────────────────────────────────────────────────

# Pagination settings
ITEMS_PER_PAGE_OPTIONS = [10, 25, 50, 100]
if "leads_per_page" not in st.session_state:
    st.session_state.leads_per_page = 25
if "leads_page" not in st.session_state:
    st.session_state.leads_page = 0

# Pagination controls
col_p1, col_p2, col_p3, col_p4 = st.columns([1, 2, 2, 1])

with col_p1:
    st.session_state.leads_per_page = st.selectbox(
        "Per page", ITEMS_PER_PAGE_OPTIONS,
        index=ITEMS_PER_PAGE_OPTIONS.index(st.session_state.leads_per_page),
        key="per_page_select", label_visibility="collapsed"
    )

total_pages = max(1, (len(filtered) + st.session_state.leads_per_page - 1) // st.session_state.leads_per_page)

# Reset page if out of bounds
if st.session_state.leads_page >= total_pages:
    st.session_state.leads_page = 0

start_idx = st.session_state.leads_page * st.session_state.leads_per_page
end_idx = min(start_idx + st.session_state.leads_per_page, len(filtered))

with col_p2:
    st.markdown(f"**Page {st.session_state.leads_page + 1} of {total_pages}** ({start_idx + 1}-{end_idx} of {len(filtered)})")

with col_p3:
    prev_col, next_col = st.columns(2)
    with prev_col:
        if st.button("⬅️ Previous", disabled=st.session_state.leads_page == 0, use_container_width=True):
            st.session_state.leads_page -= 1
            st.rerun()
    with next_col:
        if st.button("Next ➡️", disabled=st.session_state.leads_page >= total_pages - 1, use_container_width=True):
            st.session_state.leads_page += 1
            st.rerun()

with col_p4:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.leads_page = 0
        st.rerun()

# Get paginated leads
paginated_leads = filtered[start_idx:end_idx]

# ─── Lead Cards ───────────────────────────────────────────────────────────────

if not paginated_leads:
    st.info("No leads found. Click 'Scrape Leads' to find new [HIRING] posts from Reddit!")
    st.stop()

for lead in paginated_leads:
    lead_id = lead.get("id", "")
    score = lead.get("score", 0)
    status = lead.get("status", "NEW")
    title = lead.get("title", "No Title")
    name = lead.get("name", "Unknown")
    platform = lead.get("platform", "")
    url = lead.get("url", "")

    # Contact info
    contact = lead.get("contact", {})
    email = contact.get("email", "") or contact.get("emails", [""])[0] if isinstance(contact.get("emails"), list) and contact.get("emails") else contact.get("email", "")
    linkedin = contact.get("linkedin", "")
    phone = contact.get("phone", "") or (contact.get("phones", [""])[0] if isinstance(contact.get("phones"), list) and contact.get("phones") else "")

    # Lead header row
    col1, col2, col3 = st.columns([4, 1.5, 1.5])

    with col1:
        st.markdown(f"**{title[:90]}**")
        score_cls = get_score_class(score)
        st.markdown(
            f"<span class='score-badge {score_cls}'>{score}</span> "
            f"<span class='status-badge status-{status}'>{status}</span> "
            f"| 📍 {platform} | 👤 u/{name}",
            unsafe_allow_html=True
        )

    with col2:
        new_status = st.selectbox("Status", ["NEW", "CONTACTED", "REPLIED", "HOT_LEAD", "PROPOSAL_SENT", "CLOSED"],
            index=["NEW", "CONTACTED", "REPLIED", "HOT_LEAD", "PROPOSAL_SENT", "CLOSED"].index(status),
            key=f"status_{lead_id}", label_visibility="collapsed")
        if new_status != status:
            lead["status"] = new_status
            if new_status == "CONTACTED":
                lead["contacted_at"] = datetime.now().isoformat()
            save_leads(leads)
            st.rerun()

    with col3:
        col_a, col_b = st.columns(2)
        with col_a:
            if url:
                st.link_button("🔗 Open", url, use_container_width=True)
        with col_b:
            if st.button("🗑", key=f"del_{lead_id}", use_container_width=True):
                leads = [l for l in leads if l.get("id") != lead_id]
                save_leads(leads)
                st.rerun()

    # ─── Expandable Detail Panel ──────────────────────────────────────────────
    with st.expander("📋 Details • Outreach • Communication", expanded=False):

        detail_col1, detail_col2 = st.columns([1, 1])

        # LEFT — Contact & Requirement
        with detail_col1:
            with st.container(border=True):
                st.markdown("##### 📇 Contact Info & Enrichment")

                # Email Setup
                if email:
                    verification = validate_email_domain(email)
                    icon = "✅" if verification["valid"] else "⚠️"
                    st.markdown(f"📧 **Email:** {email} {icon}")
                    st.caption(f"Verification: {verification['reason']}")
                else:
                    st.markdown("📧 **Email:** <span class='contact-unverified'>Not found</span>", unsafe_allow_html=True)
                    
                # Enrichment Section
                st.markdown("---")
                st.markdown("##### 🧬 Lead Enrichment (Get Verified Emails)")
                enrich_col1, enrich_col2 = st.columns(2)
            with enrich_col1:
                if st.button("🚀 Enrich Lead", key=f"enrich_{lead_id}", use_container_width=True, help="Uses Apollo.io + Hunter.io + Email Permutation to find contact info"):
                    with st.spinner("🔍 Finding contact info..."):
                        result = enrich_single_lead(lead_id)
                        if result.get("success"):
                            emails = result.get("emails_found", 0)
                            phones = result.get("phones_found", 0)
                            score_up = result.get("score_increase", 0)
                            sources = result.get("sources", [])
                            if emails > 0 or phones > 0:
                                st.success(f"🎉 Found {emails} emails, {phones} phones! +{score_up} points")
                                st.caption(f"Sources: {', '.join(sources)}")
                            else:
                                st.warning("No new contact info found. Try manual search.")
                        else:
                            st.error(f"❌ {result.get('error', 'Enrichment failed')}")
                    time.sleep(1)
                    st.rerun()
            with enrich_col2:
                if st.button("📊 Stats", key=f"enrich_stats_{lead_id}", use_container_width=True):
                    st.json(get_enrichment_stats())
                st.markdown("---")
            if linkedin:
                st.markdown(f"🔗 **LinkedIn:** [{linkedin}]({linkedin})")
            else:
                st.markdown("🔗 **LinkedIn:** Not found")

            # Phone
            if phone:
                phone_info = validate_phone(phone)
                icon = "✅" if phone_info["valid"] else "❌"
                st.markdown(f"📞 **Phone:** {phone_info.get('formatted', phone)} {icon}")
            else:
                st.markdown("📞 **Phone:** Not found")

            # Reddit user
            reddit_user = contact.get("reddit_user", f"u/{name}")
            st.markdown(f"👤 **Reddit:** [{reddit_user}](https://reddit.com/{reddit_user})")

            st.markdown("---")
            st.markdown("##### 📝 Requirement")
            requirement = lead.get("requirement", "No details")
            st.text_area("", value=requirement[:500], height=120, disabled=True, key=f"req_{lead_id}", label_visibility="collapsed")

            # Pain points
            pain_points = lead.get("pain_points", [])
            if pain_points:
                st.markdown(f"💢 **Pain Points:** {', '.join(pain_points)}")

        # RIGHT — Outreach Actions
        with detail_col2:
            with st.container(border=True):
                st.markdown("##### ⚡ Outreach Actions")

            # Tab for different outreach types
            tab_email, tab_call, tab_linkedin = st.tabs(["✉️ Cold Email", "📞 Call Script", "💬 LinkedIn DM"])

            with tab_email:
                if st.button("🤖 Generate Cold Email", key=f"gen_email_{lead_id}", use_container_width=True):
                    with st.spinner("AI writing personalized email..."):
                        raw = generate_cold_email(lead)
                        if raw:
                            st.session_state[f"email_draft_{lead_id}"] = raw

                # Show generated email draft
                draft_key = f"email_draft_{lead_id}"
                if draft_key in st.session_state:
                    parsed = parse_email_content(st.session_state[draft_key])

                    st.text_input("Subject", value=parsed["subject"], key=f"subj_{lead_id}")
                    email_body = st.text_area("Email Body", value=parsed["body"], height=180, key=f"body_{lead_id}")

                    send_col1, send_col2 = st.columns(2)
                    with send_col1:
                        if email and st.button(f"📤 Send via Resend to {email[:20]}...", key=f"send_email_{lead_id}", use_container_width=True):
                            subject = st.session_state.get(f"subj_{lead_id}", parsed["subject"])
                            body = st.session_state.get(f"body_{lead_id}", parsed["body"])

                            with st.spinner("Sending email via Resend..."):
                                result = send_email_resend(email, subject, body)

                            if result["success"]:
                                log_outreach(lead_id, "email", f"Subject: {subject}\n\n{body}",
                                           sent_via="resend", to_email=email, resend_id=result.get("resend_id", ""))
                                lead["status"] = "CONTACTED"
                                lead["contacted_at"] = datetime.now().isoformat()
                                save_leads(leads)
                                st.success(f"✅ Email sent to {email}!")
                                del st.session_state[draft_key]
                                st.rerun()
                            else:
                                st.error(f"❌ {result['error']}")

                    with send_col2:
                        if st.button("📋 Copy Email", key=f"copy_email_{lead_id}", use_container_width=True):
                            log_outreach(lead_id, "email", st.session_state[draft_key], sent_via="manual")
                            st.toast("Email copied! Log entry created.")

                    # Follow-up option
                    history = get_lead_outreach_history(lead_id)
                    email_history = [h for h in history if h.get("type") == "email"]
                    if email_history:
                        if st.button("🔄 Generate Follow-up Email", key=f"followup_{lead_id}", use_container_width=True):
                            with st.spinner("Generating follow-up..."):
                                followup = generate_cold_email_followup(lead, email_history)
                                if followup:
                                    st.session_state[draft_key] = followup
                                    st.rerun()

            with tab_call:
                if st.button("🤖 Generate Call Script", key=f"gen_call_{lead_id}", use_container_width=True):
                    with st.spinner("AI writing call script..."):
                        script = generate_call_script(lead)
                        if script:
                            st.session_state[f"call_script_{lead_id}"] = script

                call_key = f"call_script_{lead_id}"
                if call_key in st.session_state:
                    st.text_area("Call Script", value=st.session_state[call_key], height=250, key=f"cs_display_{lead_id}")

                    if st.button("📋 Copy & Log Call", key=f"log_call_{lead_id}", use_container_width=True):
                        log_outreach(lead_id, "call", st.session_state[call_key], sent_via="manual")
                        st.toast("Call script copied! Log entry created.")

            with tab_linkedin:
                if st.button("🤖 Generate LinkedIn DM", key=f"gen_li_{lead_id}", use_container_width=True):
                    with st.spinner("AI writing connection message..."):
                        dm = generate_linkedin_dm(lead)
                        if dm:
                            st.session_state[f"li_dm_{lead_id}"] = dm

                dm_key = f"li_dm_{lead_id}"
                if dm_key in st.session_state:
                    st.text_area("LinkedIn Message", value=st.session_state[dm_key], height=100, key=f"li_display_{lead_id}")
                    char_count = len(st.session_state[dm_key])
                    st.caption(f"{char_count}/280 characters")

                    if st.button("📋 Copy & Log DM", key=f"log_li_{lead_id}", use_container_width=True):
                        log_outreach(lead_id, "linkedin_dm", st.session_state[dm_key], sent_via="manual")
                        st.toast("LinkedIn DM copied! Log entry created.")

            # ─── Communication Timeline ───────────────────────────────────────
            st.markdown("---")
            st.markdown("##### 📜 Communication History")

            history = get_lead_outreach_history(lead_id)
            if history:
                st.markdown("<div class='outreach-timeline'>", unsafe_allow_html=True)
                for entry in sorted(history, key=lambda x: x.get("sent_at", ""), reverse=True):
                    type_icon = {"email": "✉️", "linkedin_dm": "💬", "call": "📞"}.get(entry.get("type"), "📌")
                    via = f" via {entry.get('sent_via', 'manual')}" if entry.get("sent_via") else ""
                    content_preview = entry.get("content", "")[:80]
                    date = entry.get("sent_at", "")[:16].replace("T", " ")

                    st.markdown(f"""
                    <div class='timeline-item'>
                        <strong>{type_icon} {entry.get('type', '').replace('_', ' ').title()}</strong>{via}
                        <div>{content_preview}...</div>
                        <div class='timeline-date'>{date}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Mark as replied button
                    if entry.get("status") != "replied":
                        if st.button(f"✅ Mark as Replied", key=f"replied_{entry.get('id', '')}"):
                            from outreach_engine import load_outreach_log, save_outreach_log
                            log = load_outreach_log()
                            for e in log:
                                if e.get("id") == entry.get("id"):
                                    e["status"] = "replied"
                                    break
                            save_outreach_log(log)
                            lead["status"] = "REPLIED"
                            save_leads(leads)
                            st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.caption("No outreach yet. Generate an email, call script, or LinkedIn DM above!")

    st.markdown("<br>", unsafe_allow_html=True)

# ─── Bulk Actions ─────────────────────────────────────────────────────────────

st.divider()
with st.expander("📤 Bulk Email Actions"):
    st.markdown("##### Send emails to multiple leads at once")

    # Get leads with emails
    leads_with_emails = [l for l in leads if l.get("contact", {}).get("email")]
    new_leads_with_emails = [l for l in leads_with_emails if l.get("status") == "NEW"]

    col_bulk1, col_bulk2, col_bulk3 = st.columns(3)

    with col_bulk1:
        st.metric("Leads with Email", len(leads_with_emails))
    with col_bulk2:
        st.metric("New (Not Contacted)", len(new_leads_with_emails))
    with col_bulk3:
        bulk_limit = st.number_input("Max emails to send", min_value=1, max_value=50, value=10)

    if new_leads_with_emails:
        if st.button(f"🚀 Generate & Send to {min(bulk_limit, len(new_leads_with_emails))} Leads", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()

            sent_count = 0
            failed_count = 0

            for idx, lead in enumerate(new_leads_with_emails[:bulk_limit]):
                progress = (idx + 1) / min(bulk_limit, len(new_leads_with_emails))
                progress_bar.progress(progress)

                email = lead.get("contact", {}).get("email")
                if not email:
                    continue

                status_text.text(f"Processing {idx + 1}/{min(bulk_limit, len(new_leads_with_emails))}: {email[:30]}...")

                # Generate email
                try:
                    raw = generate_cold_email(lead)
                    if raw and not raw.startswith("Error"):
                        parsed = parse_email_content(raw)

                        # Send email
                        result = send_email_resend(email, parsed["subject"], parsed["body"])

                        if result.get("success"):
                            log_outreach(lead.get("id"), "email", f"Subject: {parsed['subject']}\n\n{parsed['body']}",
                                       sent_via="resend", to_email=email, resend_id=result.get("resend_id", ""))
                            lead["status"] = "CONTACTED"
                            lead["contacted_at"] = datetime.now().isoformat()
                            sent_count += 1
                        else:
                            failed_count += 1
                except Exception as e:
                    failed_count += 1

            save_leads(leads)
            progress_bar.empty()
            status_text.empty()

            if sent_count > 0:
                st.success(f"✅ Sent {sent_count} emails! Failed: {failed_count}")

                # Telegram notification
                try:
                    from telegram_brief import send_brief
                    send_brief(f"📧 Bulk email sent to {sent_count} leads!")
                except:
                    pass
            else:
                st.error(f"❌ No emails sent. Failed: {failed_count}")

            st.rerun()
    else:
        st.info("No new leads with emails found. Scrape leads first!")

# ─── Bulk Enrichment ───────────────────────────────────────────────────────────

st.divider()
with st.expander("🧬 Bulk Enrichment"):
    st.markdown("##### Enrich multiple leads at once with Apollo.io + Hunter.io")

    # Get leads without emails
    leads_without_emails = [l for l in leads if not l.get("contact", {}).get("email") and l.get("status") == "NEW"]
    leads_with_emails = [l for l in leads if l.get("contact", {}).get("email")]

    col_bulk1, col_bulk2, col_bulk3 = st.columns(3)
    with col_bulk1:
        st.metric("Without Emails", len(leads_without_emails))
    with col_bulk2:
        st.metric("With Emails", len(leads_with_emails))
    with col_bulk3:
        enrich_limit = st.number_input("Max to enrich", min_value=1, max_value=50, value=10)

    if leads_without_emails:
        if st.button(f"🚀 Enrich {min(enrich_limit, len(leads_without_emails))} Leads", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()

            enriched_count = 0
            found_emails = 0

            for idx, lead in enumerate(leads_without_emails[:enrich_limit]):
                progress = (idx + 1) / min(enrich_limit, len(leads_without_emails))
                progress_bar.progress(progress)
                status_text.text(f"Processing {idx + 1}/{min(enrich_limit, len(leads_without_emails))}: {lead.get('title', '')[:40]}...")

                try:
                    result = enrich_single_lead(lead.get("id"))
                    if result.get("success") and result.get("emails_found", 0) > 0:
                        enriched_count += 1
                        found_emails += result.get("emails_found", 0)
                except Exception as e:
                    st.error(f"Error enriching {lead.get('id')}: {e}")

                time.sleep(1.5)  # Rate limiting

            save_leads(leads)
            progress_bar.empty()
            status_text.empty()

            if enriched_count > 0:
                st.success(f"✅ Enriched {enriched_count} leads! Found {found_emails} emails")
            else:
                st.warning("No emails found. Check API keys in Settings.")

            st.rerun()
    else:
        st.info("No leads without emails found!")

# ─── Export Leads ──────────────────────────────────────────────────────────────

st.divider()
with st.expander("📤 Export Leads"):
    st.markdown("##### Export leads with contact info")

    export_col1, export_col2 = st.columns(2)
    with export_col1:
        export_with_email = st.checkbox("Only with emails", value=True)
    with export_col2:
        export_format = st.selectbox("Format", ["CSV", "JSON"])

    if export_with_email:
        export_leads = [l for l in leads if l.get("contact", {}).get("email")]
    else:
        export_leads = leads

    st.caption(f"Will export {len(export_leads)} leads")

    if st.button("📥 Download Export", use_container_width=True):
        if export_format == "JSON":
            export_data = json.dumps(export_leads, indent=2, default=str)
            st.download_button(
                label="Download JSON",
                data=export_data,
                file_name=f"leads_export_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        else:
            import csv
            import io
            output = io.StringIO()
            if export_leads:
                writer = csv.DictWriter(output, fieldnames=["id", "name", "title", "email", "phone", "platform", "score", "status", "url"])
                writer.writeheader()
                for l in export_leads:
                    writer.writerow({
                        "id": l.get("id"),
                        "name": l.get("name"),
                        "title": l.get("title", ""),
                        "email": l.get("contact", {}).get("email", ""),
                        "phone": l.get("contact", {}).get("phone", ""),
                        "platform": l.get("platform", ""),
                        "score": l.get("score", 0),
                        "status": l.get("status", "NEW"),
                        "url": l.get("url", "")
                    })
            st.download_button(
                label="Download CSV",
                data=output.getvalue(),
                file_name=f"leads_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# ─── Add Manual Lead ──────────────────────────────────────────────────────────

st.divider()
with st.expander("➕ Add Lead Manually"):
    with st.form("add_manual_lead"):
        col1, col2, col3 = st.columns(3)
        with col1:
            m_name = st.text_input("Name *", placeholder="John Doe")
            m_email = st.text_input("Email", placeholder="john@company.com")
        with col2:
            m_title = st.text_input("Project/Need *", placeholder="Need AI chatbot for website")
            m_phone = st.text_input("Phone", placeholder="+91 98765 43210")
        with col3:
            m_company = st.text_input("Company", placeholder="TechStart Inc")
            m_linkedin = st.text_input("LinkedIn URL", placeholder="linkedin.com/in/...")

        m_notes = st.text_area("Notes / Requirement", placeholder="Details about their project need...")

        if st.form_submit_button("Add Lead", use_container_width=True):
            if m_name and m_title:
                new_lead = {
                    "id": f"manual_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "name": m_name,
                    "title": m_title,
                    "requirement": m_notes,
                    "company": m_company,
                    "url": "",
                    "platform": "Manual",
                    "score": 80,
                    "status": "NEW",
                    "extracted_at": datetime.now().isoformat(),
                    "posted_at": datetime.now().isoformat(),
                    "contact": {
                        "email": m_email,
                        "emails": [m_email] if m_email else [],
                        "linkedin": m_linkedin,
                        "phone": m_phone,
                        "phones": [m_phone] if m_phone else [],
                        "reddit_user": ""
                    },
                    "pain_points": [],
                    "tags": []
                }
                leads.append(new_lead)
                save_leads(leads)
                st.success(f"✅ Lead '{m_name}' added!")
                st.rerun()
            else:
                st.error("Name and Project/Need are required!")
