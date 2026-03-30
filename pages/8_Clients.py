"""
RAGSPRO Client Management — Track clients, projects, and communication
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="RAGSPRO - Clients", page_icon="👥", layout="wide")

DATA_DIR = Path(__file__).parent.parent / "data"
CLIENTS_FILE = DATA_DIR / "clients.json"

# ─── Custom CSS ───
st.markdown("""
<style>
    .client-card {
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: box-shadow 0.2s;
    }
    .client-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .status-active { color: #10b981; font-weight: 600; }
    .status-completed { color: #6b7280; }
    .status-paused { color: #f59e0b; }
    .project-tag {
        display: inline-block;
        background: #eef2ff;
        color: #667eea;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.72rem;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)


def load_clients():
    if CLIENTS_FILE.exists():
        try:
            with open(CLIENTS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_clients(clients):
    CLIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CLIENTS_FILE, 'w') as f:
        json.dump(clients, f, indent=2, default=str)


# ─── Main ─────────────────────────────────────────────────────────────────────

st.title("👥 Client Management")

clients = load_clients()

# ─── Stats ────────────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)
active = len([c for c in clients if c.get("status") == "Active"])
completed = len([c for c in clients if c.get("status") == "Completed"])
total_revenue = sum(c.get("total_paid", 0) for c in clients)

col1.metric("Total Clients", len(clients))
col2.metric("Active", active)
col3.metric("Completed", completed)
col4.metric("Revenue", f"₹{total_revenue:,}")

st.divider()

# ─── Add New Client ──────────────────────────────────────────────────────────

with st.expander("➕ Add New Client", expanded=len(clients) == 0):
    with st.form("new_client"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Client Name *", placeholder="e.g. TechStart Inc")
            email = st.text_input("Email", placeholder="client@company.com")
            phone = st.text_input("Phone", placeholder="+91 98765 43210")
            company = st.text_input("Company", placeholder="Company name")
        with col2:
            industry = st.selectbox("Industry", [
                "SaaS", "E-commerce", "Agency", "Real Estate",
                "Healthcare", "Education", "Finance", "Technology", "Other"
            ])
            source = st.selectbox("Source", [
                "Fiverr", "Upwork", "LinkedIn", "Reddit", "Referral",
                "Website", "Cold Email", "Other"
            ])
            project_name = st.text_input("Project Name", placeholder="AI Chatbot for Website")
            project_value = st.number_input("Project Value (₹)", min_value=0, step=1000, value=0)

        notes = st.text_area("Notes", placeholder="Additional details...", height=80)

        submitted = st.form_submit_button("Add Client", use_container_width=True)

        if submitted and name:
            new_client = {
                "id": f"client_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "name": name,
                "email": email,
                "phone": phone,
                "company": company,
                "industry": industry,
                "source": source,
                "status": "Active",
                "projects": [{
                    "name": project_name or "Main Project",
                    "value": project_value,
                    "status": "In Progress",
                    "started_at": datetime.now().isoformat()
                }] if project_name or project_value > 0 else [],
                "total_paid": 0,
                "notes": notes,
                "created_at": datetime.now().isoformat(),
                "communication_log": []
            }
            clients.append(new_client)
            save_clients(clients)
            st.success(f"✅ Client '{name}' added!")
            st.rerun()

st.divider()

# ─── Filter ───────────────────────────────────────────────────────────────────

col1, col2 = st.columns([2, 1])
with col1:
    search = st.text_input("🔍 Search clients", placeholder="Name, company, or industry...")
with col2:
    status_filter = st.selectbox("Status", ["All", "Active", "Completed", "Paused"])

filtered = clients
if status_filter != "All":
    filtered = [c for c in filtered if c.get("status") == status_filter]
if search:
    search_lower = search.lower()
    filtered = [c for c in filtered if
        search_lower in c.get("name", "").lower() or
        search_lower in c.get("company", "").lower() or
        search_lower in c.get("industry", "").lower()
    ]

# ─── Client Cards ─────────────────────────────────────────────────────────────

if filtered:
    for client in filtered:
        client_id = client.get("id", "")
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                status_class = f"status-{client.get('status','Active').lower()}"
                st.markdown(f"### {client.get('name', 'Unknown')}")
                st.markdown(f"🏢 {client.get('company', 'N/A')} | 📧 {client.get('email', 'N/A')}")
                st.markdown(f"<span class='{status_class}'>{client.get('status', 'Active')}</span> | "
                           f"Source: {client.get('source', 'N/A')} | "
                           f"Industry: {client.get('industry', 'N/A')}",
                           unsafe_allow_html=True)

            with col2:
                projects = client.get("projects", [])
                if projects:
                    for proj in projects:
                        st.markdown(f"<span class='project-tag'>{proj.get('name', 'Project')}</span> "
                                   f"₹{proj.get('value', 0):,} — {proj.get('status', 'In Progress')}",
                                   unsafe_allow_html=True)
                else:
                    st.caption("No projects yet")

                st.caption(f"Total Paid: ₹{client.get('total_paid', 0):,}")

            with col3:
                new_status = st.selectbox("Status", ["Active", "Completed", "Paused"],
                    index=["Active", "Completed", "Paused"].index(client.get("status", "Active")),
                    key=f"status_{client_id}", label_visibility="collapsed")
                if new_status != client.get("status"):
                    client["status"] = new_status
                    save_clients(clients)
                    st.rerun()

                if st.button("🗑 Delete", key=f"del_{client_id}"):
                    clients = [c for c in clients if c["id"] != client_id]
                    save_clients(clients)
                    st.rerun()

            # Expandable details
            with st.expander("📝 Details & Communication Log"):
                st.markdown(f"**Notes:** {client.get('notes', 'No notes')}")
                st.markdown(f"**Phone:** {client.get('phone', 'N/A')}")
                st.markdown(f"**Added:** {client.get('created_at', '')[:10]}")

                # Add communication log
                st.markdown("---")
                st.markdown("**Communication Log:**")

                log = client.get("communication_log", [])
                for entry in log[-5:]:
                    st.markdown(f"• **{entry.get('date', '')}** [{entry.get('type', '')}] — {entry.get('note', '')}")

                with st.form(f"log_{client_id}"):
                    col_a, col_b = st.columns([1, 3])
                    with col_a:
                        log_type = st.selectbox("Type", ["Call", "Email", "Meeting", "Message", "Other"], key=f"lt_{client_id}")
                    with col_b:
                        log_note = st.text_input("Note", placeholder="What happened?", key=f"ln_{client_id}")
                    if st.form_submit_button("Add Log Entry"):
                        if log_note:
                            if "communication_log" not in client:
                                client["communication_log"] = []
                            client["communication_log"].append({
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "type": log_type,
                                "note": log_note
                            })
                            save_clients(clients)
                            st.success("Log entry added!")
                            st.rerun()

                # Add project
                st.markdown("---")
                with st.form(f"proj_{client_id}"):
                    st.markdown("**Add Project:**")
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        proj_name = st.text_input("Project Name", key=f"pn_{client_id}")
                    with col_p2:
                        proj_value = st.number_input("Value (₹)", min_value=0, step=1000, key=f"pv_{client_id}")
                    if st.form_submit_button("Add Project"):
                        if proj_name:
                            if "projects" not in client:
                                client["projects"] = []
                            client["projects"].append({
                                "name": proj_name,
                                "value": proj_value,
                                "status": "In Progress",
                                "started_at": datetime.now().isoformat()
                            })
                            save_clients(clients)
                            st.success(f"Project '{proj_name}' added!")
                            st.rerun()

                # Record payment
                st.markdown("---")
                with st.form(f"pay_{client_id}"):
                    st.markdown("**Record Payment:**")
                    payment = st.number_input("Payment Amount (₹)", min_value=0, step=500, key=f"pa_{client_id}")
                    if st.form_submit_button("Record Payment"):
                        if payment > 0:
                            client["total_paid"] = client.get("total_paid", 0) + payment
                            if "communication_log" not in client:
                                client["communication_log"] = []
                            client["communication_log"].append({
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "type": "Payment",
                                "note": f"Received ₹{payment:,}"
                            })
                            save_clients(clients)
                            st.success(f"₹{payment:,} payment recorded!")
                            st.rerun()

            st.markdown("---")
else:
    st.info("No clients found. Add your first client above! 👆")
